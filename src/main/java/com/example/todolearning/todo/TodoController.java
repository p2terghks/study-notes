package com.example.todolearning.todo;

import jakarta.validation.Valid;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.validation.BindingResult;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;

@Controller
public class TodoController {
    private final TodoService todoService;

    public TodoController(TodoService todoService) {
        this.todoService = todoService;
    }

    @GetMapping("/")
    public String home() {
        return "redirect:/todos";
    }

    @GetMapping("/todos")
    public String list(Model model) {
        model.addAttribute("todos", todoService.findAll());
        return "todos/list";
    }

    @GetMapping("/todos/new")
    public String newForm(Model model) {
        model.addAttribute("todoForm", new TodoForm());
        return "todos/new";
    }

    @PostMapping("/todos")
    public String create(@Valid @ModelAttribute("todoForm") TodoForm form,
                         BindingResult bindingResult) {
        // BindingResult는 검증 대상 매개변수 바로 다음에 둡니다.
        if (bindingResult.hasErrors()) {
            return "todos/new";
        }
        todoService.create(form);
        return "redirect:/todos";
    }

    @GetMapping("/todos/{id}/edit")
    public String editForm(@PathVariable("id") Long id, Model model) {
        Todo todo = todoService.findById(id);
        TodoForm form = new TodoForm();
        form.setTitle(todo.getTitle());
        form.setCompleted(todo.isCompleted());
        model.addAttribute("todoForm", form);
        model.addAttribute("todoId", id);
        return "todos/edit";
    }

    @PostMapping("/todos/{id}/edit")
    public String update(@PathVariable("id") Long id,
                         @Valid @ModelAttribute("todoForm") TodoForm form,
                         BindingResult bindingResult, Model model) {
        if (bindingResult.hasErrors()) {
            model.addAttribute("todoId", id);
            return "todos/edit";
        }
        todoService.update(id, form);
        return "redirect:/todos";
    }

    @PostMapping("/todos/{id}/delete")
    public String delete(@PathVariable("id") Long id) {
        todoService.delete(id);
        return "redirect:/todos";
    }
}
