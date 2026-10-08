package kr.ac.advisor.controller;

import kr.ac.advisor.service.CurriculumService;

import jakarta.servlet.http.HttpSession;
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import java.util.Map;
import org.springframework.http.ResponseEntity;
import org.springframework.security.web.csrf.CsrfToken;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.*;

@RestController
class AdvisorController {

    private final CurriculumService service;

    AdvisorController(CurriculumService service) {
        this.service = service;
    }

    record ProfileInput(
        @NotBlank @Size(max = 100) String university,
        @NotBlank @Size(max = 50) String department,
        @Min(1980) @Max(2100) int admissionYear,
        @NotNull @Pattern(regexp = "인공지능빅데이터|정보통신보안|스마트미디어") String track
    ) {}

    record Question(@NotBlank @Size(max = 1000) String message) {}

    @GetMapping("/api/csrf")
    Map<String, String> csrf(CsrfToken csrf) {
        return Map.of("headerName", csrf.getHeaderName(), "token", csrf.getToken());
    }

    @GetMapping("/api/advisor/profile")
    Object profile(HttpSession session) {
        var value = session.getAttribute("profile");
        return value == null ? Map.of() : value;
    }

    @PutMapping("/api/advisor/profile")
    CurriculumService.Profile save(HttpSession session, @Valid @RequestBody ProfileInput input) {
        var p = new CurriculumService.Profile(
            input.university().strip(),
            input.department().strip(),
            input.admissionYear(),
            input.track()
        );
        session.setAttribute("profile", p);
        return p;
    }

    @PostMapping("/api/advisor/chat")
    CurriculumService.Answer chat(HttpSession session, @Valid @RequestBody Question question) {
        return service.answer(
            (CurriculumService.Profile) session.getAttribute("profile"),
            question.message()
        );
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    ResponseEntity<?> invalid() {
        return ResponseEntity.badRequest().body(
            Map.of("message", "학적 정보와 트랙을 확인하세요. 질문은 1~1000자입니다.")
        );
    }
}
