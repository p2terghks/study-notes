# Spring 기능·사용법 요약

## 먼저 보는 기능 지도

**Spring에서는 메서드, 어노테이션, 설정을 함께 사용합니다.** 모두를 ‘함수’로 부르면 헷갈리므로 종류를 구분했습니다. Java 21 / Spring Boot 4 계열의 MVC·JPA 입문용 요약입니다. 아래 코드는 필요한 부분만 발췌했으며 import와 주변 클래스는 생략할 수 있습니다.

| 하고 싶은 일 | 사용할 기능 | 종류 |
|---|---|---|
| 앱 실행 | SpringApplication.run | 메서드 |
| 객체 등록 | @Service, @Component, @Bean | 어노테이션 |
| URL 처리 | @GetMapping, @PostMapping | 어노테이션 |
| 입력 받기 | @PathVariable, @RequestParam, @RequestBody | 어노테이션 |
| 화면에 데이터 전달 | Model.addAttribute | 메서드 |
| 상태 코드와 JSON 응답 | ResponseEntity | 타입·메서드 |
| DB CRUD | save, findById, findAll, deleteById | Repository 메서드 |
| 작업 단위 묶기 | @Transactional | 어노테이션 |
| 입력 검증 | @Valid, @NotBlank | 어노테이션 |

```text
요청 → Controller → Service → Repository → JPA/Hibernate → DB
        DTO 입력       작업 단위       Entity 저장
```

## 실행과 빈 등록

| 기능 | 언제 사용? | 간단한 사용법 |
|---|---|---|
| SpringApplication.run | 앱 시작 | run(App.class, args) |
| @SpringBootApplication | 시작 클래스 | 자동 설정·컴포넌트 탐색 |
| @Component | 일반 객체 등록 | 클래스 위에 선언 |
| @Service | 업무 처리 객체 등록 | 서비스 클래스 위에 선언 |
| @Repository | 데이터 접근 계층 표현 | 직접 만든 DAO 등에 사용 |
| @Configuration / @Bean | 직접 생성한 객체 등록 | 설정 클래스의 메서드 |

```java
@SpringBootApplication
public class App {
    public static void main(String[] args) {
        SpringApplication.run(App.class, args);
    }
}
```

```java
@Configuration
class AppConfig {
    @Bean
    Clock clock() {
        return Clock.systemUTC();
    }
}
```

생성자가 하나이면 @Autowired 없이 생성자 주입을 사용할 수 있습니다. Spring Data의 JpaRepository 인터페이스는 보통 @Repository를 직접 붙이지 않아도 구현체가 등록됩니다.

[Spring 공식: 빈과 의존성 주입](https://docs.spring.io/spring-framework/reference/core/beans/dependencies/factory-collaborators.html)

## URL 처리 — Mapping

| 기능 | 목적 | 예 |
|---|---|---|
| @RequestMapping | 공통 경로 | 클래스에 /api/todos |
| @GetMapping | 조회 | 목록, 상세 |
| @PostMapping | 생성·처리 | 새 할 일 등록 |
| @PutMapping | 전체 교체 의미의 수정 | 전체 수정 DTO |
| @PatchMapping | 일부 변경 | 완료 상태만 변경 |
| @DeleteMapping | 삭제 | ID로 삭제 |

```java
@RestController
@RequestMapping("/api/todos")
class TodoApiController {
    @GetMapping("/hello")
    public Map<String, String> hello() {
        return Map.of("message", "안녕하세요");
    }
}
```

GET /api/todos/hello 요청은 JSON 객체를 반환합니다. `@Controller`는 화면 처리에, `@RestController`는 응답 본문 데이터에 사용합니다. 같은 URL이라도 HTTP 메서드에 따라 다른 처리를 연결할 수 있습니다.

[Spring MVC 공식 문서](https://docs.spring.io/spring-framework/reference/web/webmvc.html)

## 입력 연결 — 경로·쿼리·JSON·폼

| 어노테이션 | 읽는 곳 | 요청 예 |
|---|---|---|
| @PathVariable | URL 경로 | /todos/3 |
| @RequestParam | 쿼리·폼 매개변수 | ?page=0 |
| @RequestBody | 요청 본문 | JSON 객체 |
| @ModelAttribute | 폼·쿼리를 객체로 바인딩 | title=공부 |
| @RequestHeader | HTTP 헤더 | X-Request-Id |

```java
@GetMapping("/{id}")
public TodoResponse detail(@PathVariable("id") Long id) {
    return service.find(id);
}

@GetMapping
public List<TodoResponse> list(
        @RequestParam(name = "page", defaultValue = "0") int page) {
    return service.list(page);
}
```

위 service와 TodoResponse는 애플리케이션이 정의하는 타입과 메서드입니다. Spring이 자동으로 만들어 주는 이름은 아닙니다.

```java
public record TodoCreateRequest(
    @NotBlank @Size(max = 100) String title
) {}

@PostMapping
public ResponseEntity<TodoResponse> create(
        @Valid @RequestBody TodoCreateRequest request) {
    TodoResponse saved = service.create(request);
    return ResponseEntity.created(
        URI.create("/api/todos/" + saved.id())
    ).body(saved);
}
```

`request.title()`은 Java record의 접근자입니다. JSON 본문을 받을 때 Content-Type은 application/json을 사용합니다. DTO는 입력 전달용이고 Entity는 영속 데이터용입니다.

[공식: @RequestBody](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-controller/ann-methods/requestbody.html)

## 응답 만들기 — Model·ResponseEntity

| 호출 | 결과 |
|---|---|
| model.addAttribute("todos", list) | 화면에서 읽을 이름과 값 추가 |
| return "todos/list" | @Controller에서 템플릿 이름 선택 |
| return "redirect:/todos" | 다른 주소로 이동 |
| ResponseEntity.ok(dto) | 200과 응답 본문 |
| ResponseEntity.created(uri).body(dto) | 201, Location 헤더, 본문 |
| ResponseEntity.noContent().build() | 204, 본문 없음 |
| ResponseEntity.notFound().build() | 404 |

```java
@GetMapping("/todos")
public String listPage(Model model) {
    model.addAttribute("todos", service.findAll());
    return "todos/list";
}
```

위 메서드는 @Controller 안에서 사용합니다. @RestController에서 같은 문자열을 반환하면 화면이 아니라 문자열 본문이 됩니다.

[공식: ResponseEntity](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-controller/ann-methods/responseentity.html)

## 입력 검증과 오류 처리

| 기능 | 역할 | 주의점 |
|---|---|---|
| @NotNull | null 거부 | 빈 문자열은 허용 |
| @NotBlank | null·빈 값·공백 거부 | 문자열용 |
| @Size | 길이·개수 제한 | null 자체는 보통 허용 |
| @Min / @Max | 숫자 범위 | null 금지는 별도 |
| @Valid | 객체의 검증 실행 요청 | 규칙 선언과 함께 사용 |
| BindingResult.hasErrors | 폼 검증 오류 확인 | 검증 대상 인자 바로 뒤 |

```java
@PostMapping("/todos")
public String create(@Valid @ModelAttribute("todoForm") TodoForm form,
                     BindingResult errors) {
    if (errors.hasErrors()) return "todos/new";
    service.create(form);
    return "redirect:/todos";
}
```

```java
@RestControllerAdvice
class ApiErrors {
    @ExceptionHandler(TodoNotFoundException.class)
    ResponseEntity<Map<String, String>> notFound() {
        return ResponseEntity.status(404)
            .body(Map.of("message", "할 일이 없습니다."));
    }
}
```

TodoNotFoundException은 직접 정의한 예외입니다. 예제 오류 응답은 ‘없는 할 일’만 처리하며 검증 오류와 모든 서버 오류를 한꺼번에 처리하지는 않습니다.

[공식: 검증](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-controller/ann-validation.html) · [예외 처리](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-controller/ann-exceptionhandler.html)

## DB 작업 — Repository 메서드

```java
public interface TodoRepository extends JpaRepository<Todo, Long> {
    List<Todo> findByTitleContaining(String keyword);
}
```

| 메서드 | 용도 | 반환·주의점 |
|---|---|---|
| save(entity) | 신규 저장 또는 병합 | 반환된 엔티티 사용 권장 |
| saveAll(list) | 여러 엔티티 저장 | 한 번의 bulk SQL을 보장하지 않음 |
| findById(id) | ID 조회 | Optional, 없는 경우 처리 |
| findAll() | 전체 조회 | 데이터가 많으면 페이징 |
| existsById(id) | 존재 여부 | 이후 변경까지 보장하지 않음 |
| count() | 개수 조회 | long |
| deleteById(id) | ID 삭제 | 404 정책은 직접 정의 |
| flush() | 보류된 변경을 DB와 동기화 | commit과 다름 |

```java
Todo todo = repository.findById(id)
    .orElseThrow(() -> new TodoNotFoundException(id));
```

`orElseThrow`는 Spring이 아니라 Java Optional의 메서드입니다. save는 신규 여부 판정에 따라 persist 또는 merge를 사용하므로 무조건 INSERT라는 뜻이 아닙니다.

[공식: 엔티티 저장](https://docs.spring.io/spring-data/jpa/reference/jpa/entity-persistence.html)

## 페이징·정렬·검색

```java
Pageable pageable = PageRequest.of(
    0, 20, Sort.by(Sort.Direction.DESC, "id")
);
Page<Todo> page = repository.findAll(pageable);
List<Todo> items = page.getContent();
```

| 기능 | 의미 |
|---|---|
| PageRequest.of(0, 20) | 첫 페이지, 최대 20개 |
| Sort.by(...) | 엔티티 속성으로 정렬 |
| Page.getContent() | 현재 페이지의 데이터 |
| Page.getTotalElements() | 전체 개수 |
| Page.getTotalPages() | 전체 페이지 수 |

페이지 번호는 0부터 시작합니다. 외부 입력 page는 0 이상, size는 합리적인 상한으로 검증하세요. Page는 전체 개수 조회가 필요할 수 있고 Slice는 다음 구간 존재 여부에 집중합니다.

`findByTitleContaining` 같은 메서드 이름은 엔티티의 title 속성을 기준으로 해석됩니다. DB 열 이름을 임의로 넣는 것이 아닙니다.

[공식: 쿼리 메서드](https://docs.spring.io/spring-data/jpa/reference/jpa/query-methods.html)

## 트랜잭션과 변경 감지

```java
@Service
class TodoService {
    private final TodoRepository repository;

    TodoService(TodoRepository repository) {
        this.repository = repository;
    }

    @Transactional
    public void update(Long id, String title) {
        Todo todo = repository.findById(id)
            .orElseThrow(() -> new TodoNotFoundException(id));
        todo.changeTitle(title);
    }
}
```

changeTitle은 직접 정의한 엔티티 메서드입니다. 트랜잭션에서 관리 중인 엔티티를 변경하면 JPA의 변경 감지로 반영되어 반드시 save를 다시 부를 필요는 없습니다.

| 설정 | 의미 |
|---|---|
| @Transactional | DB 작업의 트랜잭션 경계 |
| readOnly = true | 읽기 최적화 힌트, 쓰기 권한 통제가 아님 |
| rollbackFor = Exception.class | checked 예외도 포함하도록 롤백 규칙 확장 |

기본 롤백은 RuntimeException과 Error에 적용됩니다. 프록시 방식에서 같은 객체 내부의 메서드 호출만으로 별도 트랜잭션 어노테이션이 적용되지는 않습니다.

[공식: @Transactional](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/annotations.html)

## 자주 헷갈리는 부분

| 오해 | 정확한 구분 |
|---|---|
| Controller의 create는 Spring 내장 함수 | 이름은 개발자가 정하고 Mapping이 요청 연결 |
| @Entity는 Service와 같은 빈 | JPA 엔티티와 스프링 빈은 관리 역할이 다름 |
| DTO에 붙인 검증은 언제나 자동 실행 | @Valid 등 검증을 호출하는 경계 필요 |
| JPA가 곧 DB | JPA는 표준, Hibernate는 구현, DB는 저장소 |
| redirect가 JSON API에도 필수 | REST API는 보통 상태 코드·DTO 반환 |
| CORS가 로그인 권한 검사 | CORS는 브라우저 출처 정책, 인증·인가는 별도 |

**찾아보기 순서:** URL → 입력 방식 → 검증 → Service → Repository → 응답. 기존 학습 프로젝트를 읽을 때 이 순서대로 추적해 보세요.
