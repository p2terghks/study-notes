package kr.ac.campus.exception;

import kr.ac.campus.advisor.controller.AdvisorController;

import java.util.Map;
import org.springframework.dao.CannotAcquireLockException;
import org.springframework.dao.QueryTimeoutException;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.server.ResponseStatusException;

/** 화면의 공통 요청 함수가 읽을 수 있도록 오류 응답을 {message: ...} 형태로 통일한다. */
@RestControllerAdvice
class ApiErrors {

    @ExceptionHandler(ResponseStatusException.class)
    ResponseEntity<Map<String, String>> status(ResponseStatusException exception) {
        String message =
            exception.getReason() == null ? "요청을 처리할 수 없습니다." : exception.getReason();
        return ResponseEntity.status(exception.getStatusCode()).body(Map.of("message", message));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    ResponseEntity<Map<String, String>> invalid(MethodArgumentNotValidException exception) {
        if (exception.getParameter().getContainingClass() == AdvisorController.class) {
            return ResponseEntity.badRequest().body(
                Map.of(
                    "message",
                    "질문은 1~1000자, 학적 정보는 대학·학과·입학년도(1980~2100)를 확인해주세요."
                )
            );
        }
        return ResponseEntity.badRequest().body(
            Map.of("message", "학번 8~12자리, 이름, 비밀번호 8~64자를 확인해주세요.")
        );
    }

    // 잠금 대기 시간 초과는 신청 실패로 안내한다. 성공 여부가 불확실한 요청을 자동 재전송하지 않는다.
    @ExceptionHandler({ CannotAcquireLockException.class, QueryTimeoutException.class })
    ResponseEntity<Map<String, String>> busy() {
        return ResponseEntity.status(409).body(
            Map.of("message", "신청이 몰리고 있습니다. 잠시 후 다시 시도해주세요.")
        );
    }
}
