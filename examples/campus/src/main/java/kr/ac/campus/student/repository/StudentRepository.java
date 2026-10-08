package kr.ac.campus.student.repository;

import kr.ac.campus.student.entity.StudentEntity;

import jakarta.persistence.LockModeType;
import java.util.*;
import org.springframework.data.jpa.repository.*;
import org.springframework.data.repository.query.Param;

public interface StudentRepository extends JpaRepository<StudentEntity, Long> {
    Optional<StudentEntity> findByStudentNo(String studentNo);

    // 사용자 → 강의 순서로 잠금을 획득하며 트랜잭션 종료까지 유지한다.
    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @Query("select s from StudentEntity s where s.studentNo = :number")
    Optional<StudentEntity> lockByStudentNo(@Param("number") String number);
}
