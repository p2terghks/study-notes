package kr.ac.campus.student.entity;

import jakarta.persistence.*;

/** students 테이블 매핑. 외부 응답에는 서비스 DTO를 사용한다. */
@Entity
@Table(name = "students")
public class StudentEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "id", nullable = false)
    private Long id;

    @Column(name = "student_no", nullable = false, length = 20, unique = true)
    private String studentNo;

    @Column(name = "name", nullable = false, length = 50)
    private String name;

    @Column(name = "password", nullable = false, length = 100)
    private String password;

    @Column(name = "department", nullable = false, length = 50)
    private String department;

    protected StudentEntity() {}

    public StudentEntity(String studentNo, String name, String password, String department) {
        this.studentNo = studentNo;
        this.name = name;
        this.password = password;
        this.department = department;
    }

    public Long getId() {
        return id;
    }

    public String getStudentNo() {
        return studentNo;
    }

    public String getName() {
        return name;
    }

    public String getPassword() {
        return password;
    }

    public String getDepartment() {
        return department;
    }

    public void changeDepartment(String department) {
        this.department = department;
    }
}
