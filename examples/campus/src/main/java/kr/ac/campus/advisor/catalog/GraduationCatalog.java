package kr.ac.campus.advisor.catalog;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.net.URI;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import org.springframework.stereotype.Component;

/** 운영자가 공식 출처를 확인해 등록한 요건만 제공한다. 웹페이지를 임의로 추측하거나 생성하지 않는다. */
@Component
public class GraduationCatalog {

    public record Policy(
        String university,
        String department,
        int admissionYear,
        String title,
        String sourceUrl,
        LocalDate verifiedOn,
        List<String> requirements
    ) {}

    private final List<Policy> policies;

    public GraduationCatalog(
        ObjectMapper mapper,
        @Value("${app.advisor.requirements-location}") Resource resource
    ) throws IOException {
        try (var stream = resource.getInputStream()) {
            policies = List.copyOf(mapper.readValue(stream, new TypeReference<List<Policy>>() {}));
        }
        for (Policy policy : policies) {
            if (
                policy.university() == null ||
                policy.university().isBlank() ||
                policy.department() == null ||
                policy.department().isBlank() ||
                policy.title() == null ||
                policy.title().isBlank() ||
                policy.admissionYear() < 1980 ||
                policy.admissionYear() > 2100 ||
                policy.verifiedOn() == null ||
                policy.requirements() == null ||
                policy.requirements().isEmpty() ||
                policy
                    .requirements()
                    .stream()
                    .anyMatch(value -> value == null || value.isBlank())
            ) {
                throw new IllegalArgumentException(
                    "졸업요건의 대학·학과·입학년도·확인일·요건을 확인하세요."
                );
            }
            URI source = URI.create(policy.sourceUrl());
            if (!"https".equals(source.getScheme()) || source.getHost() == null) {
                throw new IllegalArgumentException("졸업요건 출처는 HTTPS URL이어야 합니다.");
            }
            long duplicates = policies
                .stream()
                .filter(
                    other ->
                        other.university().equals(policy.university()) &&
                        other.department().equals(policy.department()) &&
                        other.admissionYear() == policy.admissionYear()
                )
                .count();
            if (duplicates != 1) throw new IllegalArgumentException(
                "같은 대학·학과·입학년도의 졸업요건이 중복됩니다."
            );
        }
    }

    public Optional<Policy> find(String university, String department, Integer admissionYear) {
        if (university == null || admissionYear == null) return Optional.empty();
        return policies
            .stream()
            .filter(
                p ->
                    p.university().equals(university) &&
                    p.department().equals(department) &&
                    p.admissionYear() == admissionYear
            )
            .findFirst();
    }
}
