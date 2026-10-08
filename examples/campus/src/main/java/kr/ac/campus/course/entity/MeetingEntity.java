package kr.ac.campus.course.entity;

import jakarta.persistence.*;

/** meetings 테이블 매핑. 외부 응답에는 서비스 DTO를 사용한다. */
@Entity
@Table(name = "meetings")
public class MeetingEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "id", nullable = false)
    private Long id;

    @Column(name = "course_id", nullable = false)
    private Long courseId;

    @Column(name = "day_of_week", nullable = false)
    private int day;

    @Column(name = "start_minute", nullable = false)
    private int start;

    @Column(name = "end_minute", nullable = false)
    private int end;

    protected MeetingEntity() {}

    public MeetingEntity(Long courseId, int day, int start, int end) {
        this.courseId = courseId;
        this.day = day;
        this.start = start;
        this.end = end;
    }

    public Long getId() {
        return id;
    }

    public Long getCourseId() {
        return courseId;
    }

    public int getDay() {
        return day;
    }

    public int getStart() {
        return start;
    }

    public int getEnd() {
        return end;
    }
}
