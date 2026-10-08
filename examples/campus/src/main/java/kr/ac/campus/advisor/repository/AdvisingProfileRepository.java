package kr.ac.campus.advisor.repository;

import kr.ac.campus.advisor.entity.AdvisingProfileEntity;

import jakarta.persistence.LockModeType;
import java.util.*;
import org.springframework.data.jpa.repository.*;
import org.springframework.data.repository.query.Param;

public interface AdvisingProfileRepository extends JpaRepository<AdvisingProfileEntity, Long> {}
