package com.example.todolearning.todo;

import java.util.List;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional(readOnly = true)
public class TodoService {
    private final TodoRepository todoRepository;

    // 생성자 주입: 스프링이 필요한 Repository를 넣어 줍니다.
    public TodoService(TodoRepository todoRepository) {
        this.todoRepository = todoRepository;
    }

    public List<Todo> findAll() {
        return todoRepository.findAll(Sort.by(Sort.Direction.DESC, "id"));
    }

    public Todo findById(Long id) {
        return todoRepository.findById(id)
                .orElseThrow(() -> new TodoNotFoundException(id));
    }

    @Transactional
    public void create(TodoForm form) {
        todoRepository.save(new Todo(form.getTitle().strip()));
    }

    @Transactional
    public void update(Long id, TodoForm form) {
        Todo todo = findById(id);
        todo.update(form.getTitle().strip(), form.isCompleted());
        // 트랜잭션 안에서 조회한 엔티티의 변경은 커밋 때 DB에 반영됩니다.
        // 이 동작을 변경 감지(dirty checking)라고 부릅니다.
    }

    @Transactional
    public void delete(Long id) {
        todoRepository.delete(findById(id));
    }
}
