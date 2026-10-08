package kr.ac.advisor;

import kr.ac.advisor.service.CurriculumService;

import static org.assertj.core.api.Assertions.*;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.csrf;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.web.servlet.MockMvc;

@SpringBootTest
@AutoConfigureMockMvc
class CurriculumTest {

    @Autowired
    CurriculumService service;

    @Autowired
    MockMvc mvc;

    CurriculumService.Profile profile(String track) {
        return new CurriculumService.Profile("나사렛대학교", "인공지능학부", 2024, track);
    }

    @Test
    void bluePoolPreservesPrintedCategoryAndSelectionRule() {
        var a = service.answer(profile("인공지능빅데이터"), "2학년 파란색 후보");
        assertThat(a.points()).anyMatch(p -> p.contains("합계 21학점"));
        assertThat(a.points()).anyMatch(
            p -> p.contains("UNIX") && p.contains("전공선택") && p.contains("3학점")
        );
        assertThat(a.points()).anyMatch(p -> p.contains("자료구조") && p.contains("전공심화"));
        assertThat(a.points()).noneMatch(p -> p.contains("영상편집실무"));
    }

    @Test
    void imagesOverrideEarlierRequiredLabels() {
        var a = service.answer(profile("스마트미디어"), "1학년 전공필수");
        assertThat(a.points()).anyMatch(p -> p.contains("파이썬프로그래밍"));
        assertThat(a.points()).noneMatch(p -> p.contains("컴퓨터그래픽기초"));
    }

    @Test
    void noOtherCohortOrGraduationVerdict() {
        var a = service.answer(
            new CurriculumService.Profile("나사렛대학교", "인공지능학부", 2025, "스마트미디어"),
            "졸업"
        );
        assertThat(a.message()).contains("등록되지");
        var b = service.answer(profile("스마트미디어"), "졸업");
        assertThat(b.points()).anyMatch(p -> p.contains("27학점"));
        assertThat(b.points()).anyMatch(p -> p.contains("누적 이수"));
    }

    @Test
    void creditsAndImageDiscrepanciesAreRetained() {
        var a = service.answer(profile("정보통신보안"), "4학년 현장실습2");
        assertThat(a.points()).anyMatch(p -> p.contains("2학기 28과목·85학점"));
        assertThat(service.data().courses())
            .filteredOn(c -> c.name().startsWith("현장실습"))
            .allMatch(c -> c.credits() == 12);
        assertThat(service.data().courses())
            .filteredOn(c -> c.name().startsWith("Lab"))
            .allMatch(c -> c.credits() == 1);
    }

    @Test
    void profilesAreSessionScopedAndCsrfProtected() throws Exception {
        var session = new org.springframework.mock.web.MockHttpSession();
        String body =
            "{\"university\":\"나사렛대학교\",\"department\":\"인공지능학부\",\"admissionYear\":2024,\"track\":\"스마트미디어\"}";
        mvc.perform(
            put("/api/advisor/profile")
                .session(session)
                .contentType("application/json")
                .content(body)
        ).andExpect(status().isForbidden());
        mvc.perform(
            put("/api/advisor/profile")
                .session(session)
                .with(csrf())
                .contentType("application/json")
                .content(body)
        ).andExpect(status().isOk());
        mvc.perform(get("/api/advisor/profile").session(session)).andExpect(
            jsonPath("$.track").value("스마트미디어")
        );
        mvc.perform(get("/api/advisor/profile")).andExpect(jsonPath("$.track").doesNotExist());
        mvc.perform(
            post("/api/advisor/chat")
                .session(session)
                .with(csrf())
                .contentType("application/json")
                .content("{\"message\":\"졸업\"}")
        )
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.message").value("나사렛대학교 2024학번 · 스마트미디어"));
    }
}
