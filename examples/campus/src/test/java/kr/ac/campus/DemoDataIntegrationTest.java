package kr.ac.campus;

import kr.ac.campus.course.service.CourseService;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

/** JPA 초기화 경로에서도 샘플 강의·수업 시간·신청 인원 관계가 함께 저장되는지 확인한다. */
@SpringBootTest(
    properties = {
        "spring.datasource.url=jdbc:h2:mem:campus-demo-test;DB_CLOSE_DELAY=-1",
        "app.demo-enabled=true",
    }
)
class DemoDataIntegrationTest {

    @Autowired
    CourseService service;

    @Test
    void seedsConsistentDemoState() {
        var state = service.state("20260001");
        assertThat(state.courses()).hasSize(12);
        assertThat(state.enrolledIds()).hasSize(3);
        assertThat(state.cartIds()).hasSize(2);
        assertThat(state.courses()).allSatisfy(c -> {
            assertThat(c.meetings()).isNotEmpty();
            assertThat(c.enrolled()).isEqualTo(state.enrolledIds().contains(c.id()) ? 1 : 0);
        });
    }
}
