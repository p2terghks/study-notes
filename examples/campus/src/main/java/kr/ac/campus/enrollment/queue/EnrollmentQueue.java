package kr.ac.campus.enrollment.queue;

import java.util.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ClassPathResource;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.script.DefaultRedisScript;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

/** 선택형 FIFO 입장 제어. Redis가 켜져 있을 때 DB 신청 앞에 대기열을 둔다. */
@Service
public class EnrollmentQueue {
    public record Ticket(String status, int position, String ticket) {}
    private final boolean enabled;
    private final StringRedisTemplate redis;
    private final DefaultRedisScript<List> script;
    private static final List<String> KEYS = List.of("campus:{enrollment}:wait", "campus:{enrollment}:owners",
        "campus:{enrollment}:expiry", "campus:{enrollment}:active", "campus:{enrollment}:sequence", "campus:{enrollment}:users");
    public EnrollmentQueue(StringRedisTemplate redis, @Value("${app.enrollment-queue.enabled:false}") boolean enabled,
                           @Value("${app.redis.enabled:false}") boolean redisEnabled) {
        if (enabled && !redisEnabled) throw new IllegalArgumentException("Enrollment queue requires app.redis.enabled=true");
        this.redis = redis; this.enabled = enabled;
        script = new DefaultRedisScript<>(); script.setLocation(new ClassPathResource("redis/enrollment-queue.lua"));
        script.setResultType(List.class);
    }
    public boolean enabled() { return enabled; }
    public Ticket join(String user) { return call("join", user, UUID.randomUUID().toString()); }
    public Ticket poll(String user, String ticket) { return call("poll", user, ticket); }
    public void cancel(String user, String ticket) { call("cancel", user, ticket); }
    public void release(String user, String ticket) { call("release", user, ticket); }
    public void enroll(String user, String ticket, Runnable operation) {
        if (!enabled) { operation.run(); return; }
        if (ticket == null || !"admitted".equals(call("claim", user, ticket).status()))
            throw new ResponseStatusException(HttpStatus.CONFLICT, "대기열 입장 순서를 확인해주세요.");
        try { operation.run(); }
        finally {
            // DB 커밋 성공을 Redis 정리 실패로 뒤집지 않는다. 임대는 자동 만료된다.
            try { release(user, ticket); } catch (RuntimeException ignored) { }
        }
    }
    private Ticket call(String action, String user, String ticket) {
        if (!enabled) throw new ResponseStatusException(HttpStatus.NOT_FOUND, "대기열이 비활성화되어 있습니다.");
        if (ticket == null || ticket.length() > 64) throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "잘못된 대기표입니다.");
        try {
            var value = redis.execute(script, KEYS, action, user, ticket, Long.toString(System.currentTimeMillis()));
            if (value == null || value.size() != 3) throw new IllegalStateException("Invalid queue response");
            var result = new Ticket(value.get(0).toString(), Integer.parseInt(value.get(1).toString()), value.get(2).toString());
            if ("full".equals(result.status())) throw new ResponseStatusException(HttpStatus.TOO_MANY_REQUESTS, "대기열이 가득 찼습니다.");
            return result;
        } catch (ResponseStatusException e) { throw e; }
        catch (RuntimeException e) { throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE, "대기열에 연결하지 못했습니다. 신청 내역을 확인하고 다시 시도해주세요."); }
    }
}
