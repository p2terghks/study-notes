package kr.ac.campus.course.repository;

import kr.ac.campus.course.entity.CourseEntity;

import jakarta.persistence.LockModeType;
import java.util.*;
import org.springframework.data.jpa.repository.*;
import org.springframework.data.repository.query.Param;

public interface CourseRepository extends JpaRepository<CourseEntity, Long> {
    List<CourseEntity> findAllByOrderByIdAsc();
    Optional<CourseEntity> findByCode(String code);

    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @Query("select c from CourseEntity c where c.id = :id")
    Optional<CourseEntity> lockById(@Param("id") long id);
}
