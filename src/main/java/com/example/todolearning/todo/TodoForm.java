package com.example.todolearning.todo;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

// 화면 입력 전용 객체(DTO). DB 객체인 Todo와 역할을 구분합니다.
public class TodoForm {
    @NotBlank(message = "할 일을 입력해 주세요.")
    @Size(max = 100, message = "할 일은 100자 이내로 입력해 주세요.")
    private String title;

    private boolean completed;

    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }
    public boolean isCompleted() { return completed; }
    public void setCompleted(boolean completed) { this.completed = completed; }
}
