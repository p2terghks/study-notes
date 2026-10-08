package kr.ac.campus.advisor.controller;

import kr.ac.campus.advisor.service.AdvisorService;

import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import java.security.Principal;
import org.springframework.web.bind.annotation.*;

/** 개인 상담은 인증된 사용자 기준으로만 조회한다. 채팅 API로 신청·취소를 실행하지 않는다. */
@RestController
@RequestMapping("/api/advisor")
public class AdvisorController {

    private final AdvisorService advisor;

    AdvisorController(AdvisorService advisor) {
        this.advisor = advisor;
    }

    record Question(
        @NotBlank @Size(max = 1000) String message,
        @Size(max = 30) String previousTopic
    ) {}

    record ProfileInput(
        @NotBlank @Size(max = 100) String university,
        @NotBlank @Size(max = 50) String department,
        @NotNull @Min(1980) @Max(2100) Integer admissionYear
    ) {}

    @GetMapping("/profile")
    AdvisorService.Profile profile(Principal user) {
        return advisor.profile(user.getName());
    }

    @PutMapping("/profile")
    AdvisorService.Profile profile(Principal user, @Valid @RequestBody ProfileInput input) {
        return advisor.saveProfile(
            user.getName(),
            input.university(),
            input.department(),
            input.admissionYear()
        );
    }

    @PostMapping("/chat")
    AdvisorService.Answer chat(Principal user, @Valid @RequestBody Question question) {
        return advisor.reply(user.getName(), question.message(), question.previousTopic());
    }
}
