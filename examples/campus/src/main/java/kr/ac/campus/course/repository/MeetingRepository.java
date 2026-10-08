package kr.ac.campus.course.repository;

import kr.ac.campus.course.entity.MeetingEntity;

import jakarta.persistence.LockModeType;
import java.util.*;
import org.springframework.data.jpa.repository.*;
import org.springframework.data.repository.query.Param;

public interface MeetingRepository extends JpaRepository<MeetingEntity, Long> {
    List<MeetingEntity> findAllByOrderByDayAscStartAsc();
}
