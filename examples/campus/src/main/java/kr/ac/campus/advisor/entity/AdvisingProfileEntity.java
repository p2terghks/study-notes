package kr.ac.campus.advisor.entity;

import jakarta.persistence.*;

/** advising_profiles 테이블 매핑. 외부 응답에는 서비스 DTO를 사용한다. */
@Entity
@Table(name = "advising_profiles")
public class AdvisingProfileEntity {

    @Id
    @Column(name = "student_id", nullable = false)
    private Long studentId;

    @Column(name = "university", nullable = false, length = 100)
    private String university;

    @Column(name = "admission_year", nullable = false)
    private int admissionYear;

    protected AdvisingProfileEntity() {}

    public AdvisingProfileEntity(Long studentId, String university, int admissionYear) {
        this.studentId = studentId;
        this.university = university;
        this.admissionYear = admissionYear;
    }

    public Long getStudentId() {
        return studentId;
    }

    public String getUniversity() {
        return university;
    }

    public int getAdmissionYear() {
        return admissionYear;
    }
}
