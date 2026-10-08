package kr.ac.campus.shared.entity;

import jakarta.persistence.*;
import java.io.Serializable;
import java.util.Objects;

/** 신청과 장바구니의 복합 기본키. DB에서도 동일 학생·강의 중복을 차단한다. */
@Embeddable
public class StudentCourseId implements Serializable {

    @Column(name = "student_id", nullable = false)
    private Long studentId;

    @Column(name = "course_id", nullable = false)
    private Long courseId;

    protected StudentCourseId() {}

    public StudentCourseId(Long studentId, Long courseId) {
        this.studentId = studentId;
        this.courseId = courseId;
    }

    public Long getStudentId() {
        return studentId;
    }

    public Long getCourseId() {
        return courseId;
    }

    @Override
    public boolean equals(Object other) {
        return (
            other instanceof StudentCourseId key &&
            Objects.equals(studentId, key.studentId) &&
            Objects.equals(courseId, key.courseId)
        );
    }

    @Override
    public int hashCode() {
        return Objects.hash(studentId, courseId);
    }
}
