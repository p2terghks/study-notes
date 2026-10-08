package kr.ac.campus.advisor.service;

import kr.ac.campus.advisor.catalog.GraduationCatalog;
import kr.ac.campus.advisor.entity.AdvisingProfileEntity;
import kr.ac.campus.advisor.repository.AdvisingProfileRepository;
import kr.ac.campus.course.service.CourseService;
import kr.ac.campus.student.repository.StudentRepository;

import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

/** 인증된 학사 데이터를 Python 상담 엔진에 전달한다. */
@Service
public class AdvisorService {

    public record Profile(
        String name,
        String university,
        String department,
        Integer admissionYear
    ) {}

    public record Source(String title, String url, String checkedOn) {}

    public record Recommendation(CourseService.Course course, String reason) {}

    public record Answer(
        String topic,
        String message,
        List<String> points,
        List<Recommendation> recommendations,
        List<Source> sources,
        List<String> suggestions
    ) {}

    private final CourseService courses;
    private final StudentRepository students;
    private final AdvisingProfileRepository profiles;
    private final GraduationCatalog graduation;
    private final PythonAdvisor python;

    AdvisorService(
        CourseService courses,
        StudentRepository students,
        AdvisingProfileRepository profiles,
        GraduationCatalog graduation,
        PythonAdvisor python
    ) {
        this.courses = courses;
        this.students = students;
        this.profiles = profiles;
        this.graduation = graduation;
        this.python = python;
    }

    public Profile profile(String username) {
        var student = courses.student(username);
        return profiles
            .findById(student.id())
            .map(p ->
                new Profile(
                    student.name(),
                    p.getUniversity(),
                    student.department(),
                    p.getAdmissionYear()
                )
            )
            .orElse(new Profile(student.name(), null, student.department(), null));
    }

    @Transactional
    public Profile saveProfile(
        String username,
        String university,
        String department,
        int admissionYear
    ) {
        var student = students
            .lockByStudentNo(username)
            .orElseThrow(() -> new ResponseStatusException(HttpStatus.UNAUTHORIZED));
        student.changeDepartment(department.strip());
        profiles.save(new AdvisingProfileEntity(student.getId(), university.strip(), admissionYear));
        return new Profile(
            student.getName(),
            university.strip(),
            student.getDepartment(),
            admissionYear
        );
    }

    public Answer reply(String username, String message, String previousTopic) {
        var profile = profile(username);
        var policy = graduation.find(profile.university(), profile.department(), profile.admissionYear());
        return python.reply(new ChatInput(courses.state(username), profile, message, previousTopic, policy.orElse(null)));
    }

    record ChatInput(CourseService.State state, Profile profile, String message,
                     String previousTopic, GraduationCatalog.Policy policy) {}
}
