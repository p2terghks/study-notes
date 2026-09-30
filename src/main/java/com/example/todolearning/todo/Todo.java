package com.example.todolearning.todo;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;

// 자바 객체를 DB 테이블의 한 행과 연결합니다.
@Entity
public class Todo {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 100)
    private String title;

    @Column(nullable = false)
    private boolean completed;

    // JPA가 DB 데이터를 객체로 만들 때 사용하는 기본 생성자입니다.
    protected Todo() {
    }

    public Todo(String title) {
        this.title = title;
        this.completed = false;
    }

    public void update(String title, boolean completed) {
        this.title = title;
        this.completed = completed;
    }

    public Long getId() { return id; }
    public String getTitle() { return title; }
    public boolean isCompleted() { return completed; }
}
