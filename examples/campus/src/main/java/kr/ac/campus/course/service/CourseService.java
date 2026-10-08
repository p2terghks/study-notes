package kr.ac.campus.course.service;

import kr.ac.campus.cart.entity.CartEntity;
import kr.ac.campus.cart.repository.CartRepository;
import kr.ac.campus.course.entity.CourseEntity;
import kr.ac.campus.course.repository.CourseRepository;
import kr.ac.campus.course.repository.MeetingRepository;
import kr.ac.campus.enrollment.entity.EnrollmentEntity;
import kr.ac.campus.enrollment.repository.EnrollmentRepository;
import kr.ac.campus.shared.entity.StudentCourseId;
import kr.ac.campus.student.repository.StudentRepository;

import java.util.*;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.*;
import org.springframework.web.server.ResponseStatusException;

/** 업무 검증과 트랜잭션을 담당하며 DB 접근은 JPA 리포지토리에 위임한다. */
@Service
public class CourseService {

    static final int MAX_CREDITS = 18;
    private final StudentRepository students;
    private final CourseRepository courses;
    private final MeetingRepository meetings;
    private final EnrollmentRepository enrollments;
    private final CartRepository cart;

    public CourseService(
        StudentRepository students,
        CourseRepository courses,
        MeetingRepository meetings,
        EnrollmentRepository enrollments,
        CartRepository cart
    ) {
        this.students = students;
        this.courses = courses;
        this.meetings = meetings;
        this.enrollments = enrollments;
        this.cart = cart;
    }

    /** day는 월요일 0~금요일 4, start/end는 자정부터 지난 분이다. */
    public record Meeting(int day, int start, int end) {}

    public record Course(
        long id,
        String code,
        String name,
        String professor,
        String department,
        String category,
        int credits,
        int capacity,
        int enrolled,
        String room,
        String color,
        List<Meeting> meetings
    ) {}

    public record Student(
        long id,
        String studentNo,
        String name,
        String department,
        int maxCredits
    ) {}

    /** 화면이 한 번의 요청으로 그릴 수 있도록 사용자·강의·신청·장바구니를 함께 반환한다. */
    public record State(
        Student student,
        List<Course> courses,
        List<Long> enrolledIds,
        List<Long> cartIds
    ) {}

    public Student student(String username) {
        var s = students
            .findByStudentNo(username)
            .orElseThrow(() -> new ResponseStatusException(HttpStatus.UNAUTHORIZED));
        return new Student(
            s.getId(),
            s.getStudentNo(),
            s.getName(),
            s.getDepartment(),
            MAX_CREDITS
        );
    }

    public List<Course> courses() {
        Map<Long, List<Meeting>> times = new HashMap<>();
        // 두 번의 일괄 조회로 N+1 조회를 피한다.
        for (var m : meetings.findAllByOrderByDayAscStartAsc())
            times
                .computeIfAbsent(m.getCourseId(), id -> new ArrayList<>())
                .add(new Meeting(m.getDay(), m.getStart(), m.getEnd()));
        return courses
            .findAllByOrderByIdAsc()
            .stream()
            .map(c ->
                new Course(
                    c.getId(),
                    c.getCode(),
                    c.getName(),
                    c.getProfessor(),
                    c.getDepartment(),
                    c.getCategory(),
                    c.getCredits(),
                    c.getCapacity(),
                    c.getEnrolled(),
                    c.getRoom(),
                    c.getColor(),
                    times.getOrDefault(c.getId(), List.of())
                )
            )
            .toList();
    }

    @Transactional(readOnly = true, isolation = Isolation.REPEATABLE_READ)
    public State state(String username) {
        var s = student(username);
        return new State(s, courses(), enrollments.courseIds(s.id()), cart.courseIds(s.id()));
    }

    /** 잠금 순서: 사용자 → 강의. 검사·신청·인원·장바구니 변경은 모두 함께 커밋/롤백된다. */
    @Transactional
    public void enroll(String username, long courseId) {
        long studentId = lockStudent(username);
        var course = lockCourse(courseId);
        var key = new StudentCourseId(studentId, courseId);
        if (enrollments.existsById(key)) throw conflict("이미 신청한 강의입니다.");
        if (course.getEnrolled() >= course.getCapacity()) throw conflict("정원이 마감되었습니다.");
        if (enrollments.credits(studentId) + course.getCredits() > MAX_CREDITS) throw conflict(
            "최대 신청 학점은 18학점입니다."
        );
        if (enrollments.conflicts(studentId, courseId) > 0) throw conflict(
            "신청한 강의와 시간이 겹칩니다."
        );
        enrollments.save(new EnrollmentEntity(studentId, courseId));
        course.reserveSeat(); // 관리 중인 엔티티의 변경은 커밋 때 UPDATE된다.
        cart.findById(key).ifPresent(cart::delete);
    }

    @Transactional
    public void cancel(String username, long courseId) {
        long studentId = lockStudent(username);
        var course = lockCourse(courseId);
        enrollments.findById(new StudentCourseId(studentId, courseId)).ifPresent(e -> {
            enrollments.delete(e);
            course.releaseSeat(); // 실제 신청이 있을 때만 반환: 재전송에도 안전하다.
        });
    }

    @Transactional
    public void addCart(String username, long courseId) {
        long studentId = lockStudent(username);
        lockCourse(courseId);
        var key = new StudentCourseId(studentId, courseId);
        if (enrollments.existsById(key)) throw conflict("이미 신청한 강의입니다.");
        if (!cart.existsById(key)) cart.save(new CartEntity(studentId, courseId));
    }

    @Transactional
    public void removeCart(String username, long courseId) {
        long studentId = lockStudent(username);
        cart.findById(new StudentCourseId(studentId, courseId)).ifPresent(cart::delete);
    }

    private long lockStudent(String username) {
        return students
            .lockByStudentNo(username)
            .orElseThrow(() -> new ResponseStatusException(HttpStatus.UNAUTHORIZED))
            .getId();
    }

    private CourseEntity lockCourse(long id) {
        return courses
            .lockById(id)
            .orElseThrow(() ->
                new ResponseStatusException(HttpStatus.NOT_FOUND, "강의를 찾을 수 없습니다.")
            );
    }

    private ResponseStatusException conflict(String message) {
        return new ResponseStatusException(HttpStatus.CONFLICT, message);
    }
}
