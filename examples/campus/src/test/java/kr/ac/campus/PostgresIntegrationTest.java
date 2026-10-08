package kr.ac.campus;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestBuilders.formLogin;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;

/** Run against a disposable PostgreSQL database: inherited tests delete all course/student records. */
@ActiveProfiles("prod")
@EnabledIfEnvironmentVariable(named = "TEST_POSTGRES_URL", matches = ".+")
class PostgresIntegrationTest extends CampusIntegrationTest {

    @DynamicPropertySource
    static void database(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", () -> System.getenv("TEST_POSTGRES_URL"));
        registry.add("spring.datasource.username", () -> System.getenv("TEST_POSTGRES_USERNAME"));
        registry.add("spring.datasource.password", () -> System.getenv("TEST_POSTGRES_PASSWORD"));
        registry.add("spring.flyway.enabled", () -> "true");
        registry.add("spring.sql.init.mode", () -> "never");
    }

    @Test
    void sessionIsStoredInDatabaseAndCookieAuthenticatesNextRequest() throws Exception {
        var response = mvc
            .perform(formLogin("/api/login").user("20260001").password("password123"))
            .andExpect(status().isNoContent())
            .andReturn()
            .getResponse();
        var cookie = response.getCookie("SESSION");
        assertThat(cookie).isNotNull();
        assertThat(cookie.getSecure()).isTrue();
        assertThat(cookie.isHttpOnly()).isTrue();
        assertThat(
            db.queryForObject(
                "SELECT COUNT(*) FROM spring_session WHERE principal_name='20260001'",
                Integer.class
            )
        ).isPositive();
        mvc.perform(get("/api/state").cookie(cookie))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.student.studentNo").value("20260001"));
        mvc.perform(get("/api/config")).andExpect(jsonPath("$.demoEnabled").value(false));
        mvc.perform(get("/actuator/health/readiness"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.status").value("UP"))
            .andExpect(jsonPath("$.components").doesNotExist());
    }
}
