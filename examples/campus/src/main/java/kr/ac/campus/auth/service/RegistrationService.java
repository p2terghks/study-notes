package kr.ac.campus.auth.service;

import kr.ac.campus.student.entity.StudentEntity;
import kr.ac.campus.student.repository.StudentRepository;

import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.http.HttpStatus;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

/** 비밀번호 해시와 회원 저장을 담당한다. 학번 중복은 DB UNIQUE 제약으로 최종 보장한다. */
@Service
public class RegistrationService {

    private final StudentRepository students;
    private final PasswordEncoder encoder;

    public RegistrationService(StudentRepository students, PasswordEncoder encoder) {
        this.students = students;
        this.encoder = encoder;
    }

    @Transactional
    public void register(String studentNo, String name, String password) {
        if (studentNo == null) throw new ResponseStatusException(
            HttpStatus.BAD_REQUEST,
            "학번을 입력해주세요."
        );
        try {
            // flush로 UNIQUE 오류를 이 범위에서 변환하고 트랜잭션 전체를 롤백한다.
            students.saveAndFlush(
                new StudentEntity(studentNo, name.strip(), encoder.encode(password), "컴퓨터공학과")
            );
        } catch (DataIntegrityViolationException e) {
            throw new ResponseStatusException(HttpStatus.CONFLICT, "이미 등록된 학번입니다.");
        }
    }
}
