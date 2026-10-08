package kr.ac.campus.api;

import kr.ac.campus.auth.service.RegistrationService;
import kr.ac.campus.course.service.CourseService;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import java.security.Principal;
import java.util.Map;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.security.web.csrf.CsrfToken;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

/** HTTP 요청의 인증 사용자와 입력을 서비스에 전달한다. 신청 규칙은 CourseService에서 검증한다. */
@RestController
@RequestMapping("/api")
class ApiController {

    private final CourseService service;
    private final RegistrationService registrationService;

    ApiController(CourseService service, RegistrationService registrationService) {
        this.service = service;
        this.registrationService = registrationService;
    }

    @Value("${app.demo-enabled:false}")
    private boolean demoEnabled;

    @GetMapping("/config")
    Map<String, Boolean> config() {
        return Map.of("demoEnabled", demoEnabled);
    }

    // 브라우저는 이 토큰을 변경 요청의 헤더에 넣는다. 로그인 성공 후에는 새 토큰을 받는다.
    @GetMapping("/csrf")
    Map<String, String> csrf(CsrfToken token) {
        return Map.of("token", token.getToken(), "headerName", token.getHeaderName());
    }

    // 학생 ID를 클라이언트에서 받지 않아 다른 사용자의 내역을 임의로 조회할 수 없게 한다.
    @GetMapping("/state")
    CourseService.State state(Principal principal) {
        return service.state(principal.getName());
    }

    record Registration(
        @Pattern(regexp = "[0-9]{8,12}") String studentNo,
        @NotBlank @Size(max = 30) String name,
        @NotBlank @Size(min = 8, max = 64) String password
    ) {}

    // 비밀번호 원문 대신 BCrypt 해시만 저장한다. 학번 중복은 DB의 UNIQUE 제약으로도 보호한다.
    @PostMapping("/register")
    @ResponseStatus(HttpStatus.CREATED)
    void register(@Valid @RequestBody Registration registration) {
        registrationService.register(
            registration.studentNo(),
            registration.name(),
            registration.password()
        );
    }

    @PostMapping("/enrollments/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    void enroll(Principal principal, @PathVariable long id) {
        service.enroll(principal.getName(), id);
    }

    @DeleteMapping("/enrollments/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    void cancel(Principal principal, @PathVariable long id) {
        service.cancel(principal.getName(), id);
    }

    @PostMapping("/cart/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    void addCart(Principal principal, @PathVariable long id) {
        service.addCart(principal.getName(), id);
    }

    @DeleteMapping("/cart/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    void removeCart(Principal principal, @PathVariable long id) {
        service.removeCart(principal.getName(), id);
    }
}
