package kr.ac.campus.advisor.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.annotation.PreDestroy;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.Semaphore;
import java.util.concurrent.TimeUnit;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ClassPathResource;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ResponseStatusException;

/** 로컬 Python 프로세스와 JSON으로 통신한다. 셸과 외부 네트워크를 사용하지 않는다. */
@Component
public class PythonAdvisor {
    private final ObjectMapper mapper;
    private final String executable;
    private final Path script;
    private final Semaphore slots = new Semaphore(4);

    public PythonAdvisor(ObjectMapper mapper,
                         @Value("${app.advisor.python-executable:python3}") String executable) throws IOException {
        this.mapper = mapper;
        this.executable = executable;
        script = Files.createTempFile("campus-advisor-", ".py");
        try (var stream = new ClassPathResource("python/advisor.py").getInputStream()) {
            Files.copy(stream, script, java.nio.file.StandardCopyOption.REPLACE_EXISTING);
        }
    }

    public AdvisorService.Answer reply(AdvisorService.ChatInput input) {
        if (!slots.tryAcquire()) throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE,
            "상담 요청이 많아요. 잠시 후 다시 시도해주세요.");
        Path request = null, response = null;
        Process process = null;
        try {
            request = Files.createTempFile("advisor-request-", ".json");
            response = Files.createTempFile("advisor-response-", ".json");
            mapper.writeValue(request.toFile(), input);
            var builder = new ProcessBuilder(executable, "-I", "-X", "utf8", script.toString())
                .redirectInput(request.toFile()).redirectOutput(response.toFile())
                .redirectError(ProcessBuilder.Redirect.DISCARD);
            process = builder.start();
            if (!process.waitFor(10, TimeUnit.SECONDS)) {
                throw new IOException("Python advisor timed out");
            }
            if (process.exitValue() != 0) throw new IOException("Python advisor failed");
            return mapper.readValue(response.toFile(), AdvisorService.Answer.class);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw unavailable(e);
        } catch (IOException e) {
            throw unavailable(e);
        } finally {
            if (process != null && process.isAlive()) {
                process.destroyForcibly();
                try { process.waitFor(1, TimeUnit.SECONDS); }
                catch (InterruptedException e) { Thread.currentThread().interrupt(); }
            }
            remove(request);
            remove(response);
            slots.release();
        }
    }

    private ResponseStatusException unavailable(Exception cause) {
        return new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE,
            "Python 상담 엔진을 실행할 수 없어요. 서버의 Python 설정을 확인해주세요.", cause);
    }

    private void remove(Path path) {
        if (path != null) {
            try { Files.deleteIfExists(path); }
            catch (IOException ignored) { path.toFile().deleteOnExit(); }
        }
    }

    @PreDestroy
    void close() { remove(script); }
}
