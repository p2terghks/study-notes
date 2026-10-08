package kr.ac.campus.cart.repository;

import kr.ac.campus.cart.entity.CartEntity;
import kr.ac.campus.shared.entity.StudentCourseId;

import jakarta.persistence.LockModeType;
import java.util.*;
import org.springframework.data.jpa.repository.*;
import org.springframework.data.repository.query.Param;

public interface CartRepository extends JpaRepository<CartEntity, StudentCourseId> {
    @Query(
        "select e.id.courseId from CartEntity e where e.id.studentId = :studentId order by e.id.courseId"
    )
    List<Long> courseIds(@Param("studentId") long studentId);
}
