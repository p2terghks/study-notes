package kr.ac.advisor.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.util.*;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Service;

@Service
public class CurriculumService {

    public record Course(
        String name,
        int year,
        int semester,
        String category,
        List<String> tracks,
        Integer credits,
        boolean blue,
        String sourcePage
    ) {}

    public record Curriculum(
        String university,
        List<String> departments,
        int admissionYear,
        String source,
        String receivedOn,
        List<String> tracks,
        List<String> requirements,
        List<String> cautions,
        List<String> unresolvedRows,
        List<Course> courses
    ) {}

    public record Profile(
        String university,
        String department,
        int admissionYear,
        String track
    ) implements java.io.Serializable {}

    public record Source(String title, String url, String checkedOn) {}

    public record Answer(
        String message,
        List<String> points,
        List<Source> sources,
        List<String> suggestions
    ) {}

    private final Curriculum data;

    public CurriculumService(ObjectMapper mapper) throws IOException {
        try (var stream = new ClassPathResource("advising/kornu-2024.json").getInputStream()) {
            data = mapper.readValue(stream, Curriculum.class);
        }
    }

    public Curriculum data() {
        return data;
    }

    private String normalize(String value) {
        return value.toLowerCase(Locale.ROOT).replaceAll("\\s+", "").replace("&", "/");
    }

    public Answer answer(Profile profile, String message) {
        String query = normalize(message);
        if (profile == null) return result(
            "학적 정보를 먼저 저장해주세요.",
            List.of("나사렛대학교 2024학번과 본인 트랙을 선택하면 교육과정을 안내합니다.")
        );
        if (
            !data.university().equals(profile.university()) ||
            !data.departments().contains(profile.department()) ||
            data.admissionYear() != profile.admissionYear()
        ) return result(
            "해당 대학·학과·학번 자료는 등록되지 않았습니다.",
            List.of("현재 자료는 나사렛대학교 인공지능학부(IT인공지능학부) 2024학번에 한정합니다.")
        );
        String track = data
            .tracks()
            .stream()
            .filter(query::contains)
            .findFirst()
            .orElse(profile.track());
        boolean blue = query.contains("파란") || query.contains("파랑") || query.contains("심화");
        boolean rule =
            query.contains("졸업") ||
            query.contains("교양") ||
            query.contains("복수전공") ||
            query.contains("자율") ||
            query.contains("127");
        List<String> points = new ArrayList<>();
        if (rule) {
            points.addAll(data.requirements());
        } else {
            var matched = data
                .courses()
                .stream()
                .filter(c -> query.contains(normalize(c.name())))
                .max(Comparator.comparingInt(c -> normalize(c.name()).length()));
            boolean listing =
                blue ||
                matched.isPresent() ||
                query.contains("학년") ||
                query.contains("학기") ||
                query.contains("필수") ||
                query.contains("선택") ||
                query.contains("교육과정") ||
                query.contains("추천");
            if (!listing) return result(
                "등록된 교육과정과 졸업 기준을 안내하는 학사 도우미입니다.",
                List.of(
                    "예: 2학년 필수 과목, 파란색 심화 후보, JAVA 학점, 졸업 학점",
                    "수강신청 사이트·성적표·실시간 개설 강의와 연결되지 않은 독립 시제품입니다."
                )
            );
            if (track == null) return result("트랙을 선택해주세요.", data.tracks());
            int year = 0,
                semester = 0;
            for (int n = 1; n <= 4; n++) if (query.contains(n + "학년")) year = n;
            for (int n = 1; n <= 2; n++) if (query.contains(n + "학기")) semester = n;
            final int y = year,
                s = semester;
            final String name = matched.map(Course::name).orElse(null);
            var selected = data
                .courses()
                .stream()
                .filter(c -> c.tracks().contains(track))
                .filter(c -> y == 0 || c.year() == y)
                .filter(c -> s == 0 || c.semester() == s)
                .filter(c -> name == null || normalize(c.name()).equals(normalize(name)))
                .filter(c -> name != null || !blue || c.blue())
                .filter(
                    c ->
                        name != null ||
                        blue ||
                        !query.contains("필수") ||
                        c.category().equals("전공필수")
                )
                .filter(
                    c ->
                        name != null ||
                        blue ||
                        !query.contains("선택") ||
                        c.category().equals("전공선택")
                )
                .toList();
            if (blue) points.add(
                "졸업하려는 트랙의 파란색 과목 중 합계 21학점을 선택 이수합니다. 파란색 과목 전부가 필수라는 의미는 아닙니다. 표의 이수구분과 파란색 표시는 별도로 유지합니다."
            );
            if (query.contains("추천")) points.add(
                "아래는 교육과정 탐색 후보입니다. 현재 개설 여부·이수 이력·시간 충돌·선수과목을 확인할 수 없어 신청 가능한 강의로 확정하지 않습니다."
            );
            for (var c : selected)
                points.add(
                    c.year() +
                        "학년 " +
                        c.semester() +
                        "학기 · " +
                        c.name() +
                        " · " +
                        c.credits() +
                        "학점 · 표 구분: " +
                        c.category() +
                        (c.blue() ? " · 파란색(21학점 선택 후보)" : "")
                );
            if (selected.isEmpty()) points.add(
                "이 트랙과 조건에 해당하는 과목이 자료에 없습니다. 면제나 이수 완료를 뜻하지 않습니다."
            );
            if (track.equals("정보통신보안")) points.addAll(data.unresolvedRows());
        }
        points.addAll(data.cautions());
        return result("나사렛대학교 2024학번 · " + (track == null ? "공통 기준" : track), points);
    }

    private Answer result(String message, List<String> points) {
        return new Answer(
            message,
            points,
            List.of(new Source(data.source(), null, null)),
            List.of(
                "졸업 학점 알려줘",
                "2학년 전공필수 알려줘",
                "파란색 심화 후보 알려줘",
                "3학년 교육과정 알려줘"
            )
        );
    }
}
