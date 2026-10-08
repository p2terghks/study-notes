package kr.ac.campus.enrollment.entity;

import kr.ac.campus.shared.entity.StudentCourseId;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "enrollments")
public class EnrollmentEntity {

    @EmbeddedId
    private StudentCourseId id;

    @Column(name = "created_at", nullable = false)
    private LocalDateTime createdAt;

    protected EnrollmentEntity() {}

    public EnrollmentEntity(long studentId, long courseId) {
        id = new StudentCourseId(studentId, courseId);
        createdAt = LocalDateTime.now();
    }

    public StudentCourseId getId() {
        return id;
    }
}
