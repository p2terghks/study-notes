# Spring·JPA 코드 설명 요약본

2026-10-15 현재 코드 기준입니다. [React 요약본](REACT_SUMMARY.md)과 같은 번호별 설명·코드 예시·해설 형식입니다. 코드는 핵심 발췌 또는 생략 표시가 있는 축약 예시이며, 생성자와 단순 getter는 반복 설명 대신 묶었습니다. 수강신청 서버의 현재 기능을 설명합니다.

## 1. 전체 폴더 구조

```text
수강2/
├── frontend/                         # 수강신청 React 원본
├── src/main/java/kr/ac/campus/
│   ├── CampusApplication.java        # 서버 시작
│   ├── api/                          # 공통 HTTP API
│   ├── auth/service/                 # 회원가입
│   ├── student/entity·repository/    # 학생
│   ├── course/entity·repository·service/ # 강의·시간·수강 업무
│   ├── enrollment/entity·repository/ # 신청 내역
│   ├── cart/entity·repository/       # 장바구니
│   ├── shared/entity/                # 공통 복합키
│   ├── config/                       # 인증·운영 세션
│   ├── exception/                    # 오류 응답
│   └── bootstrap/                    # 체험 데이터
├── src/main/resources/               # 설정·SQL·빌드된 화면
├── src/test/java/                    # 서버 통합 테스트
├── docs/                             # 코드 설명·요약
└── deploy/                           # ECS Fargate·RDS 배포 및 검증 파일
```

`entity·repository`는 두 개의 하위 폴더를 줄여 쓴 표현입니다. 실제 폴더 이름에 가운데점이 들어가지는 않습니다. 이후 수강신청 Java 파일 경로는 `src/main/java/kr/ac/campus/` 기준입니다.

## 2. 서버 시작과 역할 구분

```java
@SpringBootApplication
public class CampusApplication {
    public static void main(String[] args) {
        SpringApplication.run(CampusApplication.class, args);
    }
}
```

`main()`이 Spring Boot를 시작합니다. `@SpringBootApplication` 아래 패키지의 Controller·Service·설정 등을 찾아 연결합니다.

```text
React 요청 → Controller → Service → Repository → DB
React 화면 ← JSON 응답 ← DTO ← 조회·처리 결과
```

Controller는 요청을 받고, Service는 업무 규칙과 트랜잭션을 처리하며, Repository는 DB를 조회합니다. Entity는 테이블에 대응하는 객체, DTO는 화면에 전달할 데이터입니다. 생성자로 의존 객체를 받으면 Spring이 해당 객체를 주입합니다.

## 3. HTTP 요청 — ApiController

파일: [ApiController.java](../../../examples/campus/src/main/java/kr/ac/campus/api/ApiController.java)

| 메서드 | 요청 | 기능 |
| --- | --- | --- |
| `config()` | GET `/api/config` | 체험 기능 사용 여부 |
| `csrf(token)` | GET `/api/csrf` | 변경 요청용 CSRF 토큰·헤더 이름 |
| `state(principal)` | GET `/api/state` | 로그인 학생·강의·신청·장바구니 상태 |
| `register(registration)` | POST `/api/register` | 입력 검증 후 회원가입, 성공 201 |
| `enroll(principal, id)` | POST `/api/enrollments/{id}` | 신청, 성공 204 |
| `cancel(principal, id)` | DELETE `/api/enrollments/{id}` | 취소, 성공 204 |
| `addCart(principal, id)` | POST `/api/cart/{id}` | 장바구니 추가, 성공 204 |
| `removeCart(principal, id)` | DELETE `/api/cart/{id}` | 장바구니 삭제, 성공 204 |

```java
@PostMapping("/enrollments/{id}")
@ResponseStatus(HttpStatus.NO_CONTENT)
void enroll(Principal principal, @PathVariable long id) {
    service.enroll(principal.getName(), id);
}
```

`@PathVariable`은 URL의 강의 ID, `Principal`은 로그인한 사용자입니다. 학생 ID를 프론트에서 받아 신뢰하지 않고 인증 정보에서 학번을 가져옵니다. 204는 성공했지만 응답 본문이 없다는 뜻입니다. 이후 React가 state를 다시 조회합니다.

`Registration` record는 학번·이름·비밀번호 입력 DTO입니다. `@Valid`, `@Pattern`, `@NotBlank`, `@Size`로 형식과 길이를 검증합니다. 로그인과 로그아웃은 이 컨트롤러가 아닌 Spring Security가 처리합니다.

## 4. 로그인·회원가입·세션

| 파일 | 메서드 | 기능 |
| --- | --- | --- |
| `config/SecurityConfig.java` | `passwordEncoder()` | BCrypt 비밀번호 해시 도구 생성 |
| 같은 파일 | `users(students)` | 학번으로 학생을 찾아 인증용 UserDetails로 변환 |
| 같은 파일 | `security(http)` | 공개 경로·인증 경로·로그인·로그아웃·CSRF 설정 |
| `auth/service/RegistrationService.java` | `register(studentNo, name, password)` | 이름 공백 정리, 비밀번호 해시, 학생 저장 |
| `config/ProductionSessionConfig.java` | `cookieSerializer()` | 운영 세션 쿠키의 Secure·HttpOnly·SameSite 설정 |

```java
students.saveAndFlush(
    new StudentEntity(studentNo, name.strip(), encoder.encode(password), "컴퓨터공학과")
);
```

회원가입의 실제 핵심입니다. 비밀번호 원문 대신 해시를 저장합니다. 현재 가입 시 학과는 코드의 기본값인 컴퓨터공학과입니다. `saveAndFlush()`로 DB 반영을 실행해 중복 학번 오류를 메서드 안에서 409 응답으로 변환합니다.

로그인은 `POST /api/login`에 username·password 폼을 보내고, 성공하면 세션 쿠키를 사용합니다. `POST /api/logout`은 서버 세션을 종료합니다. 인증 실패는 401입니다. CSRF 보호는 유지하므로 변경 요청에는 토큰도 필요합니다.

운영 프로필의 `@EnableJdbcHttpSession`은 로그인·CSRF 상태를 DB에 공유합니다. 여러 Fargate 태스크가 같은 세션을 사용할 수 있게 하며 유휴 만료는 30분입니다. 이것은 업무 데이터용 JPA와 별개의 Spring Session JDBC 기능입니다.

## 5. 조회·신청 업무 — CourseService

파일: [CourseService.java](../../../examples/campus/src/main/java/kr/ac/campus/course/service/CourseService.java)

| 메서드 | 역할 |
| --- | --- |
| `student(username)` | 학생 조회 후 응답 DTO 생성, 없으면 401 |
| `courses()` | 강의와 수업 시간을 각각 일괄 조회해 강의별로 결합 |
| `state(username)` | 학생·강의·신청 ID·장바구니 ID를 한 응답으로 구성 |
| `enroll(username, courseId)` | 잠금 후 중복·정원·18학점·시간 충돌 검증 및 저장 |
| `cancel(username, courseId)` | 신청이 존재할 때 삭제하고 자리 반환 |
| `addCart(username, courseId)` | 이미 신청한 강의는 거부, 중복 없이 장바구니 저장 |
| `removeCart(username, courseId)` | 해당 학생의 장바구니 항목 삭제 |
| `lockStudent(username)` | 학생 행을 쓰기 잠금으로 조회 |
| `lockCourse(id)` | 강의 행을 쓰기 잠금으로 조회, 없으면 404 |
| `conflict(message)` | 업무 충돌용 409 예외 생성 |

```java
public record State(
    Student student,
    List<Course> courses,
    List<Long> enrolledIds,
    List<Long> cartIds
) {}
```

`Student`, `Course`, `Meeting`, `State`는 API 응답 DTO입니다. 학생의 비밀번호를 응답에 포함하지 않습니다. record는 데이터와 접근 메서드를 간결하게 정의하는 Java 문법이며 JPA 테이블 선언이 아닙니다.

`state()`는 읽기 전용 REPEATABLE_READ 트랜잭션으로 묶습니다. `courses()`는 수업 시간을 강의 ID별 Map으로 모아 각 강의에 붙입니다. 강의마다 시간을 개별 조회하는 N+1 패턴을 피합니다.

## 6. 동시 신청과 트랜잭션

아래는 실제 enroll의 흐름을 줄인 예시입니다. 생략한 검사는 원본에 있습니다.

```java
@Transactional
public void enroll(String username, long courseId) {
    long studentId = lockStudent(username);
    var course = lockCourse(courseId);
    var key = new StudentCourseId(studentId, courseId);
    if (enrollments.existsById(key)) throw conflict("이미 신청한 강의입니다.");
    if (course.getEnrolled() >= course.getCapacity()) throw conflict("정원이 마감되었습니다.");
    // 실제 코드: 최대 18학점 및 기존 수업과 시간 충돌도 검사
    enrollments.save(new EnrollmentEntity(studentId, courseId));
    course.reserveSeat();
    cart.findById(key).ifPresent(cart::delete);
}
```

학생 잠금은 같은 학생의 서로 다른 신청이 동시에 학점·시간 검사를 통과하는 문제를 막습니다. 강의 잠금은 여러 학생이 마지막 자리를 동시에 가져가는 문제를 막습니다. 학생 → 강의 순서를 유지합니다.

`@Transactional`은 검증과 신청 저장·인원 증가·장바구니 삭제를 하나로 묶습니다. 중간에 런타임 예외가 나면 전체가 롤백됩니다. 관리 중인 CourseEntity의 필드가 바뀌면 JPA가 커밋 때 UPDATE하는 변경 감지를 사용합니다.

```java
@Lock(LockModeType.PESSIMISTIC_WRITE)
@Query("select c from CourseEntity c where c.id = :id")
Optional<CourseEntity> lockById(@Param("id") long id);
```

JPA 조회에 DB 쓰기 잠금을 요청합니다. Java synchronized와 달리 같은 DB를 사용하는 여러 서버 사이에서도 경쟁을 조정합니다. 잠금 대기 실패는 오류 응답으로 처리하며 자동 재신청하지 않습니다.

## 7. 취소·장바구니

```java
enrollments.findById(new StudentCourseId(studentId, courseId)).ifPresent(e -> {
    enrollments.delete(e);
    course.releaseSeat();
});
```

cancel의 핵심입니다. 신청 내역이 실제 존재할 때만 자리를 반환하므로 같은 취소 요청이 반복되어도 인원이 계속 줄어들지 않습니다.

장바구니는 관심 목록입니다. 추가 시 학생·강의 확인과 이미 신청했는지 검사는 하지만 자리를 예약하지 않습니다. 정원·시간·학점의 최종 검사는 수강신청 시 수행합니다. 성공한 신청은 해당 장바구니 항목을 제거합니다.

## 8. JPA Entity와 복합키

| 파일 | 데이터·주요 메서드 |
| --- | --- |
| `student/entity/StudentEntity.java` | 학번·이름·비밀번호 해시·학과. `changeDepartment()`로 학과 변경 |
| `course/entity/CourseEntity.java` | 강의명·교수·학점·정원·현재 인원 등. `reserveSeat()` 증가, `releaseSeat()` 감소 |
| `course/entity/MeetingEntity.java` | 강의 ID·요일·시작/종료 분 |
| `enrollment/entity/EnrollmentEntity.java` | 학생·강의 복합키와 신청 시각 |
| `cart/entity/CartEntity.java` | 학생·강의 복합키와 저장 시각 |
| `shared/entity/StudentCourseId.java` | studentId + courseId, `equals()`와 `hashCode()`로 키 동등성 정의 |

각 Entity의 기본 생성자는 JPA가 객체를 복원할 때 사용합니다. 값이 있는 생성자는 신규 데이터 생성, `get...()`은 필드 읽기입니다. 시간은 월요일 0~금요일 4, 자정부터 지난 분으로 표현합니다.

```java
@Embeddable
public class StudentCourseId implements Serializable {
    // 실제 코드에는 @Column과 생성자·getter·equals·hashCode가 있음
    private Long studentId;
    private Long courseId;
}
```

신청과 장바구니 Entity는 이 키를 `@EmbeddedId`로 사용합니다. 같은 학생·강의 조합의 중복은 DB 기본키로도 차단합니다. 현재 관계는 ID 필드로 표현하며 모든 연결을 `@ManyToOne`으로 선언한 구조는 아닙니다.

## 9. Repository 메서드

| 인터페이스 | 메서드 | 조회 목적 |
| --- | --- | --- |
| `StudentRepository` | `findByStudentNo()` | 로그인·학생 조회 |
| 같은 인터페이스 | `lockByStudentNo()` | 해당 학생 잠금 |
| `CourseRepository` | `findAllByOrderByIdAsc()` | 강의 목록 |
| 같은 인터페이스 | `findByCode()` | 학수번호 조회, 체험 데이터 연결 |
| 같은 인터페이스 | `lockById()` | 강의 잠금 |
| `MeetingRepository` | `findAllByOrderByDayAscStartAsc()` | 요일·시작 시각 순 수업 시간 |
| `EnrollmentRepository` | `courseIds()` | 학생의 신청 강의 ID |
| 같은 인터페이스 | `credits()` | 신청 학점 합계 |
| 같은 인터페이스 | `conflicts()` | 신청할 강의와 겹치는 수업 시간 수 |
| `CartRepository` | `courseIds()` | 학생의 장바구니 강의 ID |

```java
public interface CourseRepository extends JpaRepository<CourseEntity, Long> {
    List<CourseEntity> findAllByOrderByIdAsc();
    Optional<CourseEntity> findByCode(String code);
}
```

`JpaRepository<Entity, 기본키타입>`을 상속하면 `save`, `findById`, `existsById`, `delete`, `count` 등을 사용할 수 있습니다. 메서드 이름으로 쿼리를 만들거나 `@Query`로 JPQL을 작성합니다. JPQL은 테이블명 대신 Entity와 Java 필드 이름을 사용합니다.

시간 충돌 조건은 같은 요일이며 `기존.start < 신규.end && 신규.start < 기존.end`입니다. 끝나는 시각과 시작하는 시각이 같으면 연속 수업으로 허용합니다.

## 10. 오류·체험 데이터

| 파일 | 메서드 | 역할 |
| --- | --- | --- |
| `exception/ApiErrors.java` | `status(exception)` | 업무 예외의 상태 코드·message 반환 |
| 같은 파일 | `invalid(exception)` | 잘못된 회원가입 입력을 400으로 안내 |
| 같은 파일 | `busy()` | 잠금·쿼리 대기 실패를 409로 안내 |
| `bootstrap/DemoData.java` | `run(args)` | 체험 모드에서 기존 강의가 없을 때 샘플 학생·강의·신청·장바구니 생성 |
| 같은 파일 | `course(...)` | 샘플 강의와 첫 번째/선택적 두 번째 수업 시간 저장 |

```java
return ResponseEntity.status(exception.getStatusCode())
    .body(Map.of("message", message));
```

오류 형태를 통일하면 React의 request가 `data.message`를 읽어 안내할 수 있습니다. Spring Security에서 발생한 오류는 필터가 별도로 처리하고 React가 상태 코드에 따른 기본 문구를 사용합니다.

## 14. 설정·DB·배포 파일

| 프로젝트 루트 기준 위치 | 역할 |
| --- | --- |
| `pom.xml`, `mvnw`, `.mvn/` | Java 의존성·빌드·Maven Wrapper |
| `src/main/resources/application.properties` | 기본 8080, 로컬 H2, 체험 모드, JPA 검증 등 |
| `src/main/resources/application-prod.properties` | PostgreSQL 환경변수, Flyway, 운영 쿠키·잠금 대기 설정 |
| `src/main/resources/schema.sql` | 로컬 DB 스키마 초기화 |
| `src/main/resources/db/migration/V1__initial_schema.sql` | 운영 업무 테이블 |
| `src/main/resources/db/migration/V2__shared_sessions.sql` | 운영 공유 세션 테이블 |
| `src/main/resources/static/` | React 빌드 결과. 직접 화면 코드를 편집하는 위치가 아님 |
| `Dockerfile`, `.dockerignore` | 수강신청 배포 이미지 빌드·포함 범위 |
| `deploy/ecs-fargate.json` | AWS 인프라 CloudFormation 정의 |
| `deploy/deploy.sh` | infra/app 단계로 인프라·이미지·서비스 배포 |
| `deploy/bootstrap-db.sql` | 제한된 앱 DB 계정 초기 준비 |
| `deploy/check-postgres.sh` | 임시 PostgreSQL 통합 검증 |
| `deploy/check-container.py` | 실제 컨테이너 간 세션 공유·초기화 검증 |

`ddl-auto=validate`는 Entity와 DB 구조를 검사하며 테이블을 자동 변경하지 않습니다. 운영 스키마는 Flyway 버전 파일로 관리합니다. 이미 적용한 마이그레이션을 고치지 않고 새 버전을 추가합니다. AWS 배포 파일이 준비된 것과 실제 배포 완료는 다릅니다. 실행 절차는 [배포 안내](../../../examples/campus/deploy/README.md)에 있습니다.

## 15. 테스트와 읽는 순서

| 파일 | 확인 범위 |
| --- | --- |
| `src/test/java/kr/ac/campus/CampusIntegrationTest.java` | 인증·업무 API·신청 검증·동시성 |
| `src/test/java/kr/ac/campus/DemoDataIntegrationTest.java` | 체험 데이터 초기화 |
| `src/test/java/kr/ac/campus/PostgresIntegrationTest.java` | PostgreSQL 환경에서 업무·세션 검증 |

```sh
# 수강2 루트에서 실행
./mvnw test
```


