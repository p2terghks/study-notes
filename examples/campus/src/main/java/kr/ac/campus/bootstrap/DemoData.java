package kr.ac.campus.bootstrap;

import kr.ac.campus.cart.entity.CartEntity;
import kr.ac.campus.cart.repository.CartRepository;
import kr.ac.campus.course.entity.CourseEntity;
import kr.ac.campus.course.entity.MeetingEntity;
import kr.ac.campus.course.repository.CourseRepository;
import kr.ac.campus.course.repository.MeetingRepository;
import kr.ac.campus.enrollment.entity.EnrollmentEntity;
import kr.ac.campus.enrollment.repository.EnrollmentRepository;
import kr.ac.campus.student.entity.StudentEntity;
import kr.ac.campus.student.repository.StudentRepository;

import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

/** 로컬 체험용 초기 데이터. prod 프로필에서는 app.demo-enabled=false로 실행하지 않는다. */
@Component
@ConditionalOnProperty(name = "app.demo-enabled", havingValue = "true")
class DemoData implements CommandLineRunner {

    private final StudentRepository students;
    private final CourseRepository courses;
    private final MeetingRepository meetings;
    private final EnrollmentRepository enrollments;
    private final CartRepository cart;
    private final PasswordEncoder encoder;

    DemoData(
        StudentRepository students,
        CourseRepository courses,
        MeetingRepository meetings,
        EnrollmentRepository enrollments,
        CartRepository cart,
        PasswordEncoder encoder
    ) {
        this.students = students;
        this.courses = courses;
        this.meetings = meetings;
        this.enrollments = enrollments;
        this.cart = cart;
        this.encoder = encoder;
    }

    @Override
    @Transactional
    public void run(String... args) {
        // 재시작할 때 사용자가 바꾼 시간표를 덮어쓰지 않도록 강의가 없을 때만 초기화한다.
        if (courses.count() > 0) return;
        var student = students.save(
            new StudentEntity("20260001", "김캠퍼스", encoder.encode("campus1234"), "컴퓨터공학과")
        );
        course(
            "CSE201",
            "자료구조",
            "김지훈",
            "컴퓨터공학과",
            "전공필수",
            3,
            40,
            "공학관 302",
            "violet",
            0,
            540,
            630,
            2,
            540,
            630
        );
        course(
            "CSE203",
            "웹 프로그래밍",
            "이서연",
            "컴퓨터공학과",
            "전공선택",
            3,
            35,
            "공학관 405",
            "blue",
            1,
            600,
            690,
            3,
            600,
            690
        );
        course(
            "CSE301",
            "데이터베이스",
            "박민준",
            "컴퓨터공학과",
            "전공필수",
            3,
            40,
            "공학관 301",
            "teal",
            0,
            780,
            870,
            2,
            780,
            870
        );
        course(
            "CSE302",
            "운영체제",
            "최유진",
            "컴퓨터공학과",
            "전공필수",
            3,
            30,
            "공학관 402",
            "peach",
            1,
            780,
            870,
            3,
            780,
            870
        );
        course(
            "CSE305",
            "인공지능의 이해",
            "정도현",
            "컴퓨터공학과",
            "전공선택",
            3,
            30,
            "미래관 201",
            "rose",
            2,
            600,
            690,
            4,
            600,
            690
        );
        course(
            "GEN102",
            "디자인적 사고",
            "한소희",
            "교양학부",
            "교양선택",
            2,
            25,
            "인문관 108",
            "yellow",
            4,
            780,
            900,
            -1,
            0,
            0
        );
        course(
            "MAT201",
            "선형대수학",
            "윤서준",
            "수학과",
            "전공기초",
            3,
            45,
            "자연관 203",
            "blue",
            0,
            660,
            750,
            2,
            660,
            750
        );
        course(
            "GEN201",
            "일상 속의 심리학",
            "강하은",
            "교양학부",
            "교양선택",
            2,
            40,
            "인문관 204",
            "violet",
            1,
            900,
            1020,
            -1,
            0,
            0
        );
        course(
            "CSE204",
            "컴퓨터 네트워크",
            "임지호",
            "컴퓨터공학과",
            "전공선택",
            3,
            35,
            "공학관 303",
            "teal",
            0,
            900,
            990,
            3,
            900,
            990
        );
        course(
            "GEN103",
            "글쓰기와 소통",
            "송지안",
            "교양학부",
            "교양필수",
            2,
            30,
            "인문관 101",
            "rose",
            4,
            540,
            660,
            -1,
            0,
            0
        );
        course(
            "CSE401",
            "소프트웨어 프로젝트",
            "오현우",
            "컴퓨터공학과",
            "전공선택",
            3,
            20,
            "공학관 501",
            "peach",
            2,
            900,
            1080,
            -1,
            0,
            0
        );
        course(
            "BUS101",
            "경영학의 이해",
            "신수빈",
            "경영학과",
            "교양선택",
            3,
            50,
            "경영관 202",
            "yellow",
            1,
            540,
            630,
            3,
            540,
            630
        );
        long studentId = student.getId();
        for (String code : new String[] { "CSE201", "CSE203", "CSE301" }) {
            var c = courses.findByCode(code).orElseThrow();
            enrollments.save(new EnrollmentEntity(studentId, c.getId()));
            c.reserveSeat();
        }
        for (String code : new String[] { "CSE302", "GEN102" }) {
            cart.save(new CartEntity(studentId, courses.findByCode(code).orElseThrow().getId()));
        }
    }

    // day/day2는 월요일 0부터 시작하고, 두 번째 수업이 없으면 day2=-1을 사용한다.
    // start/end는 자정부터 지난 분이다(예: 540=09:00).
    private void course(
        String code,
        String name,
        String professor,
        String department,
        String category,
        int credits,
        int capacity,
        String room,
        String color,
        int day,
        int start,
        int end,
        int day2,
        int start2,
        int end2
    ) {
        var c = courses.save(
            new CourseEntity(
                code,
                name,
                professor,
                department,
                category,
                credits,
                capacity,
                0,
                room,
                color
            )
        );
        meetings.save(new MeetingEntity(c.getId(), day, start, end));
        if (day2 >= 0) meetings.save(new MeetingEntity(c.getId(), day2, start2, end2));
    }
}
