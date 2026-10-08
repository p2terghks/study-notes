package kr.ac.campus;

import kr.ac.campus.course.service.CourseService;

import static org.assertj.core.api.Assertions.*;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestBuilders.formLogin;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.web.server.ResponseStatusException;

/** H2에서 실행하는 공통 시나리오. PostgreSQL 테스트도 상속해 같은 업무 규칙을 검증한다. */
@SpringBootTest(
    properties = {
        "spring.datasource.url=jdbc:h2:mem:campus-test;DB_CLOSE_DELAY=-1;LOCK_TIMEOUT=10000",
        "app.demo-enabled=false",
    }
)
@AutoConfigureMockMvc
class CampusIntegrationTest {

    @Autowired
    CourseService service;

    @Autowired
    JdbcTemplate db;

    @Autowired
    PasswordEncoder encoder;

    @Autowired
    MockMvc mvc;

    @BeforeEach
    void setup() {
        for (String table : List.of(
            "advising_profiles",
            "cart",
            "enrollments",
            "meetings",
            "courses",
            "students"
        ))
            db.update("DELETE FROM " + table);
        student("20260001");
    }

    void student(String no) {
        db.update(
            "INSERT INTO students(student_no,name,password) VALUES (?,?,?)",
            no,
            "테스트",
            encoder.encode("password123")
        );
    }

    long course(String code, int capacity, int credits, int day, int start, int end) {
        db.update(
            "INSERT INTO courses(code,name,professor,department,category,credits,capacity,room,color) VALUES (?,?, '교수','컴퓨터공학과','전공필수',?,?,'공학관','violet')",
            code,
            code,
            credits,
            capacity
        );
        long id = db.queryForObject("SELECT id FROM courses WHERE code=?", Long.class, code);
        db.update(
            "INSERT INTO meetings(course_id,day_of_week,start_minute,end_minute) VALUES (?,?,?,?)",
            id,
            day,
            start,
            end
        );
        return id;
    }

    @Test
    void cartEnrollAndCancelAreConsistent() {
        long id = course("A", 10, 3, 0, 540, 600);
        service.addCart("20260001", id);
        service.addCart("20260001", id);
        assertThat(service.state("20260001").cartIds()).containsExactly(id);
        service.enroll("20260001", id);
        assertThat(service.state("20260001").cartIds()).isEmpty();
        assertThat(service.state("20260001").enrolledIds()).containsExactly(id);
        assertThatThrownBy(() -> service.enroll("20260001", id)).isInstanceOf(
            ResponseStatusException.class
        );
        service.cancel("20260001", id);
        service.cancel("20260001", id);
        assertThat(
            db.queryForObject("SELECT enrolled FROM courses WHERE id=?", Integer.class, id)
        ).isZero();
    }

    @Test
    void timeConflictRollsBackAndAdjacentClassIsAllowed() {
        long a = course("A", 10, 3, 0, 540, 600),
            b = course("B", 10, 3, 0, 570, 630),
            c = course("C", 10, 3, 0, 600, 660);
        service.enroll("20260001", a);
        assertThatThrownBy(() -> service.enroll("20260001", b)).hasMessageContaining(
            "시간이 겹칩니다"
        );
        assertThat(
            db.queryForObject("SELECT enrolled FROM courses WHERE id=?", Integer.class, b)
        ).isZero();
        service.enroll("20260001", c);
        assertThat(service.state("20260001").enrolledIds()).hasSize(2);
    }

    @Test
    void creditLimitEnforced() {
        long a = course("A", 10, 18, 0, 540, 600),
            b = course("B", 10, 1, 1, 540, 600);
        service.enroll("20260001", a);
        assertThatThrownBy(() -> service.enroll("20260001", b)).hasMessageContaining("18학점");
    }

    interface Attempt {
        void run(int index);
    }

    // 모든 작업이 준비된 뒤 동시에 출발시켜 마지막 자리·동일 사용자 요청의 경쟁을 재현한다.
    // 409만 예상한 신청 거절로 처리하고, 다른 예외는 Future.get()을 통해 테스트를 실패시킨다.
    int race(int count, Attempt attempt) throws Exception {
        ExecutorService pool = Executors.newFixedThreadPool(count);
        CountDownLatch ready = new CountDownLatch(count),
            go = new CountDownLatch(1);
        AtomicInteger success = new AtomicInteger();
        List<Future<?>> futures = new ArrayList<>();
        try {
            for (int i = 0; i < count; i++) {
                int index = i;
                futures.add(
                    pool.submit(() -> {
                        ready.countDown();
                        try {
                            go.await();
                            attempt.run(index);
                            success.incrementAndGet();
                        } catch (ResponseStatusException e) {
                            assertThat(e.getStatusCode().value()).isEqualTo(409);
                        } catch (InterruptedException e) {
                            Thread.currentThread().interrupt();
                            throw new RuntimeException(e);
                        }
                    })
                );
            }
            assertThat(ready.await(10, TimeUnit.SECONDS)).isTrue();
            go.countDown();
            for (Future<?> f : futures) f.get(30, TimeUnit.SECONDS);
            return success.get();
        } finally {
            go.countDown();
            pool.shutdownNow();
        }
    }

    @Test
    void twentyConcurrentStudentsCannotExceedThreeSeats() throws Exception {
        long id = course("A", 3, 3, 0, 540, 600);
        for (int i = 0; i < 20; i++) student("300000" + String.format("%02d", i));
        assertThat(
            race(20, i -> service.enroll("300000" + String.format("%02d", i), id))
        ).isEqualTo(3);
        assertThat(
            db.queryForObject("SELECT enrolled FROM courses WHERE id=?", Integer.class, id)
        ).isEqualTo(3);
        assertThat(
            db.queryForObject(
                "SELECT COUNT(*) FROM enrollments WHERE course_id=?",
                Integer.class,
                id
            )
        ).isEqualTo(3);
    }

    @Test
    void concurrentRequestsFromSameStudentCannotDuplicate() throws Exception {
        long id = course("A", 20, 3, 0, 540, 600);
        assertThat(race(10, i -> service.enroll("20260001", id))).isEqualTo(1);
        assertThat(
            db.queryForObject("SELECT enrolled FROM courses WHERE id=?", Integer.class, id)
        ).isEqualTo(1);
    }

    @Test
    void concurrentDifferentCoursesForSameStudentCannotOverlap() throws Exception {
        long a = course("A", 10, 3, 0, 540, 600),
            b = course("B", 10, 3, 0, 540, 600);
        assertThat(race(2, i -> service.enroll("20260001", i == 0 ? a : b))).isEqualTo(1);
    }

    @Test
    void concurrentDifferentCoursesCannotExceedCredits() throws Exception {
        long a = course("A", 10, 10, 0, 540, 600),
            b = course("B", 10, 10, 1, 540, 600);
        assertThat(race(2, i -> service.enroll("20260001", i == 0 ? a : b))).isEqualTo(1);
    }

    @Test
    void concurrentCancelAndReenrollPreserveCounter() throws Exception {
        long id = course("A", 1, 3, 0, 540, 600);
        service.enroll("20260001", id);
        race(10, i -> {
            if (i % 2 == 0) service.cancel("20260001", id);
            else service.enroll("20260001", id);
        });
        int count = db.queryForObject(
            "SELECT COUNT(*) FROM enrollments WHERE course_id=?",
            Integer.class,
            id
        );
        assertThat(
            db.queryForObject("SELECT enrolled FROM courses WHERE id=?", Integer.class, id)
        ).isEqualTo(count);
    }

    @Test
    void authenticationCsrfAndUserIsolation() throws Exception {
        long id = course("A", 10, 3, 0, 540, 600);
        student("20260002");
        service.enroll("20260001", id);
        mvc.perform(get("/api/state")).andExpect(status().isUnauthorized());
        mvc.perform(post("/api/enrollments/" + id).with(user("20260002"))).andExpect(
            status().isForbidden()
        );
        mvc.perform(get("/api/state").with(user("20260002"))).andExpect(
            jsonPath("$.enrolledIds").isEmpty()
        );
        mvc.perform(
            delete("/api/enrollments/" + id)
                .with(user("20260002"))
                .with(csrf())
        ).andExpect(status().isNoContent());
        assertThat(service.state("20260001").enrolledIds()).containsExactly(id);
        mvc.perform(formLogin("/api/login").user("20260001").password("password123")).andExpect(
            status().isNoContent()
        );
        mvc.perform(formLogin("/api/login").user("20260001").password("wrong")).andExpect(
            status().isUnauthorized()
        );
    }

    @Test
    void pythonChatUsesAuthenticatedStateAndPreservesResponseContract() throws Exception {
        long id = course("PY101", 10, 3, 0, 600, 660);
        service.enroll("20260001", id);
        mvc.perform(post("/api/advisor/chat").with(user("20260001")).with(csrf())
                .contentType("application/json").content("{\"message\":\"내 시간표 알려줘\"}"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.topic").value("timetable"))
            .andExpect(jsonPath("$.message").value("현재 1과목, 3학점을 신청했어요."))
            .andExpect(jsonPath("$.recommendations").isArray())
            .andExpect(jsonPath("$.sources").isArray());
        student("20260002");
        mvc.perform(post("/api/advisor/chat").with(user("20260002")).with(csrf())
                .contentType("application/json").content("{\"message\":\"내 시간표 알려줘\"}"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.message").value("현재 0과목, 0학점을 신청했어요."));
        mvc.perform(post("/api/advisor/chat").with(user("20260001")).with(csrf())
                .contentType("application/json").content("{\"message\":\" \"}"))
            .andExpect(status().isBadRequest());
        mvc.perform(post("/api/advisor/chat").with(csrf())
                .contentType("application/json").content("{\"message\":\"안녕\"}"))
            .andExpect(status().isUnauthorized());
    }

    @Test
    void advisingProfileJpaInsertUpdateAndIsolation() throws Exception {
        student("20260002");
        for (int year : new int[] { 2024, 2025 }) {
            mvc.perform(
                put("/api/advisor/profile")
                    .with(user("20260001"))
                    .with(csrf())
                    .contentType("application/json")
                    .content(
                        "{\"university\":\"테스트대학교\",\"department\":\"인공지능학부\",\"admissionYear\":" +
                            year +
                            "}"
                    )
            )
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.admissionYear").value(year));
        }
        mvc.perform(get("/api/advisor/profile").with(user("20260001")))
            .andExpect(jsonPath("$.department").value("인공지능학부"))
            .andExpect(jsonPath("$.admissionYear").value(2025));
        mvc.perform(get("/api/advisor/profile").with(user("20260002"))).andExpect(
            jsonPath("$.university").doesNotExist()
        );
        assertThat(
            db.queryForObject("SELECT COUNT(*) FROM advising_profiles", Integer.class)
        ).isEqualTo(1);
    }

    @Test
    void reactPageAndBundledAssetsArePublicButStateIsPrivate() throws Exception {
        mvc.perform(get("/index.html")).andExpect(status().isOk())
            .andExpect(content().string(org.hamcrest.Matchers.containsString("id=\"root\"")));
        var resolver = new org.springframework.core.io.support.PathMatchingResourcePatternResolver();
        var assets = resolver.getResources("classpath*:static/assets/*");
        assertThat(assets).isNotEmpty();
        for (var asset : assets) {
            mvc.perform(get("/assets/" + asset.getFilename())).andExpect(status().isOk());
        }
        mvc.perform(get("/api/state")).andExpect(status().isUnauthorized());
    }

    @Test
    void registrationValidatesAndHashesPasswords() throws Exception {
        mvc.perform(
            post("/api/register")
                .with(csrf())
                .contentType("application/json")
                .content(
                    "{\"studentNo\":\"20269999\",\"name\":\"새학생\",\"password\":\"safe12345\"}"
                )
        ).andExpect(status().isCreated());
        String hash = db.queryForObject(
            "SELECT password FROM students WHERE student_no='20269999'",
            String.class
        );
        assertThat(encoder.matches("safe12345", hash)).isTrue();
        assertThat(hash).isNotEqualTo("safe12345");
        mvc.perform(
            post("/api/register")
                .with(csrf())
                .contentType("application/json")
                .content(
                    "{\"studentNo\":\"20269999\",\"name\":\"중복\",\"password\":\"safe12345\"}"
                )
        ).andExpect(status().isConflict());
        mvc.perform(
            post("/api/register")
                .with(csrf())
                .contentType("application/json")
                .content("{\"studentNo\":\"1\",\"name\":\"\",\"password\":\"a\"}")
        ).andExpect(status().isBadRequest());
    }
}
