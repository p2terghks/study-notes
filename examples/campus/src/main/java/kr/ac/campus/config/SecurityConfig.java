package kr.ac.campus.config;

import kr.ac.campus.student.repository.StudentRepository;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;

/** 세션 인증과 CSRF 보호를 적용한다. 로그인/로그아웃은 Spring Security 필터가 처리한다. */
@Configuration
class SecurityConfig {

    @Bean
    PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    @Bean
    UserDetailsService users(StudentRepository students) {
        return username ->
            students
                .findByStudentNo(username)
                .map(student ->
                    User.withUsername(student.getStudentNo())
                        .password(student.getPassword())
                        .roles("STUDENT")
                        .build()
                )
                .orElseThrow(() -> new UsernameNotFoundException("학생을 찾을 수 없습니다."));
    }

    // SPA 요청에 HTML 리다이렉트 대신 상태 코드를 반환한다. CSRF 보호는 기본값 그대로 유지한다.
    @Bean
    SecurityFilterChain security(HttpSecurity http) throws Exception {
        return http
            .authorizeHttpRequests(a ->
                a
                    .requestMatchers(
                        "/",
                        "/index.html",
                        "/assets/**",
                        "/favicon.svg",
                        "/actuator/health",
                        "/actuator/health/liveness",
                        "/actuator/health/readiness",
                        "/api/config",
                        "/api/csrf",
                        "/api/register",
                        "/error"
                    )
                    .permitAll()
                    .anyRequest()
                    .authenticated()
            )
            .exceptionHandling(e ->
                e.authenticationEntryPoint((req, res, ex) -> res.sendError(401))
            )
            .formLogin(f ->
                f
                    .loginProcessingUrl("/api/login")
                    .successHandler((req, res, auth) -> res.setStatus(204))
                    .failureHandler((req, res, ex) -> res.sendError(401))
            )
            .logout(l ->
                l
                    .logoutUrl("/api/logout")
                    .logoutSuccessHandler((req, res, auth) -> res.setStatus(204))
            )
            .build();
    }
}
