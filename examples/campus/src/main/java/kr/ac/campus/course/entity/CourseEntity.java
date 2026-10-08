package kr.ac.campus.course.entity;

import jakarta.persistence.*;

/** courses 테이블 매핑. 외부 응답에는 서비스 DTO를 사용한다. */
@Entity
@Table(name = "courses")
public class CourseEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "id", nullable = false)
    private Long id;

    @Column(name = "code", nullable = false, length = 20, unique = true)
    private String code;

    @Column(name = "name", nullable = false, length = 100)
    private String name;

    @Column(name = "professor", nullable = false, length = 50)
    private String professor;

    @Column(name = "department", nullable = false, length = 50)
    private String department;

    @Column(name = "category", nullable = false, length = 20)
    private String category;

    @Column(name = "credits", nullable = false)
    private int credits;

    @Column(name = "capacity", nullable = false)
    private int capacity;

    @Column(name = "enrolled", nullable = false)
    private int enrolled;

    @Column(name = "room", nullable = false, length = 50)
    private String room;

    @Column(name = "color", nullable = false, length = 20)
    private String color;

    protected CourseEntity() {}

    public CourseEntity(
        String code,
        String name,
        String professor,
        String department,
        String category,
        int credits,
        int capacity,
        int enrolled,
        String room,
        String color
    ) {
        this.code = code;
        this.name = name;
        this.professor = professor;
        this.department = department;
        this.category = category;
        this.credits = credits;
        this.capacity = capacity;
        this.enrolled = enrolled;
        this.room = room;
        this.color = color;
    }

    public Long getId() {
        return id;
    }

    public String getCode() {
        return code;
    }

    public String getName() {
        return name;
    }

    public String getProfessor() {
        return professor;
    }

    public String getDepartment() {
        return department;
    }

    public String getCategory() {
        return category;
    }

    public int getCredits() {
        return credits;
    }

    public int getCapacity() {
        return capacity;
    }

    public int getEnrolled() {
        return enrolled;
    }

    public String getRoom() {
        return room;
    }

    public String getColor() {
        return color;
    }

    public void reserveSeat() {
        enrolled++;
    }

    public void releaseSeat() {
        enrolled--;
    }
}
