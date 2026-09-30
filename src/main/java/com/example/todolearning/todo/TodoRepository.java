package com.example.todolearning.todo;

import org.springframework.data.jpa.repository.JpaRepository;

// <관리할 엔티티, 기본 키 타입>. 구현체는 Spring Data JPA가 생성합니다.
public interface TodoRepository extends JpaRepository<Todo, Long> {
}
