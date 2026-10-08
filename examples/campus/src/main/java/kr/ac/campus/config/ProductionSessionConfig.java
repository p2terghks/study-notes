package kr.ac.campus.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Profile;
import org.springframework.session.jdbc.config.annotation.web.http.EnableJdbcHttpSession;
import org.springframework.session.web.http.CookieSerializer;
import org.springframework.session.web.http.DefaultCookieSerializer;

/** Fargate 태스크 간 로그인·CSRF 상태를 DB로 공유한다. 세션 테이블은 Flyway가 생성한다. */
@Configuration
@Profile("prod")
@EnableJdbcHttpSession(maxInactiveIntervalInSeconds = 1800)
class ProductionSessionConfig {

    @Bean
    CookieSerializer cookieSerializer() {
        DefaultCookieSerializer cookie = new DefaultCookieSerializer();
        // HTTPS를 종료하는 ALB 뒤에서도 브라우저는 HTTPS 요청에만 세션 쿠키를 보낸다.
        cookie.setUseSecureCookie(true);
        cookie.setUseHttpOnlyCookie(true);
        cookie.setSameSite("Lax");
        cookie.setCookiePath("/");
        return cookie;
    }
}
