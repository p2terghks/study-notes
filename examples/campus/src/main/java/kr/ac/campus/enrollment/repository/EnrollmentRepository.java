package kr.ac.campus.enrollment.repository;

import kr.ac.campus.course.entity.CourseEntity;
import kr.ac.campus.course.entity.MeetingEntity;
import kr.ac.campus.enrollment.entity.EnrollmentEntity;
import kr.ac.campus.shared.entity.StudentCourseId;

import jakarta.persistence.LockModeType;
import java.util.*;
import org.springframework.data.jpa.repository.*;
import org.springframework.data.repository.query.Param;

public interface EnrollmentRepository extends JpaRepository<EnrollmentEntity, StudentCourseId> {
    @Query(
        "select e.id.courseId from EnrollmentEntity e where e.id.studentId = :studentId order by e.id.courseId"
    )
    List<Long> courseIds(@Param("studentId") long studentId);

    @Query(
        "select coalesce(sum(c.credits),0) from CourseEntity c where c.id in (select e.id.courseId from EnrollmentEntity e where e.id.studentId = :studentId)"
    )
    long credits(@Param("studentId") long studentId);

    // 종료 시각은 포함하지 않아 연속 수업은 허용한다.
    @Query(
        "select count(m) from MeetingEntity m, MeetingEntity requested where requested.courseId = :courseId and m.day = requested.day and m.start < requested.end and requested.start < m.end and m.courseId in (select e.id.courseId from EnrollmentEntity e where e.id.studentId = :studentId)"
    )
    long conflicts(@Param("studentId") long studentId, @Param("courseId") long courseId);
}
