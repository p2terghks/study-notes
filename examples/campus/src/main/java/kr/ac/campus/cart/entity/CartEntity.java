package kr.ac.campus.cart.entity;

import kr.ac.campus.shared.entity.StudentCourseId;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "cart")
public class CartEntity {

    @EmbeddedId
    private StudentCourseId id;

    @Column(name = "created_at", nullable = false)
    private LocalDateTime createdAt;

    protected CartEntity() {}

    public CartEntity(long studentId, long courseId) {
        id = new StudentCourseId(studentId, courseId);
        createdAt = LocalDateTime.now();
    }

    public StudentCourseId getId() {
        return id;
    }
}
