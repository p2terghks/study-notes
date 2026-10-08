# React + Spring 코드 설명 가이드

현재 프론트는 React + Vite, 서버는 Spring Boot + Spring Data JPA입니다. React 원본은 `frontend/src`, 배포 파일은 `src/main/resources/static`에 있습니다. static 파일은 직접 수정하지 말고 React를 빌드하세요.

## 1. 실행과 빌드

```sh
npm --prefix frontend ci
npm --prefix frontend run build
./mvnw spring-boot:run
```

Node.js 22.12 이상과 Java 17 이상이 필요합니다. Spring은 8080에서 화면과 API를 제공합니다. 개발 중에는 Spring을 실행한 상태에서 `npm --prefix frontend run dev`로 Vite를 시작합니다. 5173의 `/api` 요청은 8080으로 전달됩니다. 프론트 테스트는 `npm --prefix frontend test`, 서버 테스트는 `./mvnw test`입니다.

Docker는 Node 단계에서 React를 빌드한 후 Java 단계에서 정적 파일을 JAR에 포함합니다. 실행 컨테이너에는 Node가 필요하지 않습니다.

## 2. 파일별 역할

| 파일 | 역할 |
| --- | --- |
| [main.jsx](../frontend/src/main.jsx) | React 진입점과 CSS 로드 |
| [App.jsx](../frontend/src/App.jsx) | 인증 화면/메인 화면과 알림 전환 |
| [AuthPage.jsx](../frontend/src/features/auth/AuthPage.jsx) | 로그인·회원가입·체험 계정 |
| [Dashboard.jsx](../frontend/src/features/dashboard/Dashboard.jsx) | 메뉴·검색·필터·요약·취소 확인 |
| [CourseRows.jsx](../frontend/src/features/courses/CourseRows.jsx) | 강의 목록, 신청 버튼, 미리보기 이벤트 |
| [Schedule.jsx](../frontend/src/features/timetable/Schedule.jsx) | 시간표 블록·충돌 표시·인쇄 |
| [Modal.jsx](../frontend/src/shared/ui/Modal.jsx) | 대화상자 초점·Escape 처리 |
| [useCampus.js](../frontend/src/features/registration/useCampus.js) | 서버 상태·인증·신청·주기 갱신 |
| [api.js](../frontend/src/shared/api/api.js) | HTTP·세션 쿠키·CSRF·오류 처리 |
| [courses.js](../frontend/src/features/courses/courses.js) | 검색·학점·시간 충돌 계산 |
| [styles.css](../frontend/src/styles.css) | features/·shared/의 기능별 CSS를 순서대로 불러오는 진입점 |

## 3. React는 상태에서 화면을 만든다

[App.jsx](../frontend/src/App.jsx)는 `useCampus()`가 반환한 서버 상태를 보고 화면을 선택합니다. 아래는 핵심을 간추린 예시입니다.

```jsx
const campus = useCampus();
return campus.state
  ? <Dashboard {...campus} />
  : <AuthPage login={campus.login} demoEnabled={campus.demoEnabled} />;
```

`state`는 `/api/state`에서 받은 학생·강의·신청·장바구니입니다. 로그인 상태가 없으면 `null`입니다. `setState()`로 새 응답을 저장하면 React가 바뀐 부분을 다시 그립니다. 이전처럼 `innerHTML`로 강의 목록을 새로 만들거나 DOM 이벤트를 재등록하지 않습니다.

Dashboard의 `tab`, `filters`, `previewId`는 화면 전용 상태입니다. 서버 신청 내역과 분리되어 있으므로 강의에 마우스를 올려도 실제 수강신청은 일어나지 않습니다.

```jsx
const [previewId, setPreviewId] = useState(null);
<CourseRows onPreview={setPreviewId} />
<Schedule previewId={previewId} />
```

실제 컴포넌트에는 state 등 추가 props가 전달됩니다. `onMouseEnter`와 `onFocus`는 강의 ID를 설정하고, 영역을 벗어나면 미리보기를 비웁니다. 사용자 이름·강의명은 JSX 텍스트로 출력하므로 HTML로 해석하지 않습니다.

## 4. 요청과 화면 갱신

```text
신청 버튼
  → Dashboard.onAction()
  → useCampus.mutate()
  → POST /api/enrollments/{id}
  → Spring Controller → Service → Repository → DB
  → GET /api/state
  → setState() → 목록·학점·시간표 갱신
```

`api.js`는 같은 출처에만 세션 쿠키를 전달합니다. 변경 요청에는 `/api/csrf`에서 받은 토큰을 헤더에 넣습니다. 로그인 후 토큰을 다시 받으며, 403 변경 요청은 자동 재전송하지 않습니다. 201·204처럼 본문이 없는 성공 응답도 처리합니다.

`useCampus`는 변경 중 연속 클릭을 막습니다. 변경 전 진행 중이던 조회가 있으면 먼저 완료하여 오래된 결과가 최신 신청 내역을 덮어쓰지 않게 합니다. 로그아웃·세션 만료 시 세대 번호를 변경해 이전 계정의 늦은 조회 응답을 무시합니다.

서버 변경은 성공했지만 뒤따르는 조회가 실패하면 “요청은 완료됐지만 화면을 갱신하지 못했어요”라고 구분해 안내합니다. 정원은 화면이 보일 때 20초마다 갱신하며 취소 확인 중에는 주기 갱신을 쉬어갑니다.

## 5. Spring Controller·Service·Repository·Entity

| 계층 | 실제 파일 | 역할 |
| --- | --- | --- |
| Controller | [ApiController.java](../src/main/java/kr/ac/campus/api/ApiController.java) | URL·입력 검증·인증된 학번 전달 |
| Service | [CourseService.java](../src/main/java/kr/ac/campus/course/service/CourseService.java) | 신청 규칙·트랜잭션·응답 DTO |
| Service | [RegistrationService.java](../src/main/java/kr/ac/campus/auth/service/RegistrationService.java) | BCrypt 해시·회원가입 저장 |
| Repository | [CourseRepository.java](../src/main/java/kr/ac/campus/course/repository/CourseRepository.java) | JPA 조회와 강의 행 잠금 |
| Entity | [CourseEntity.java](../src/main/java/kr/ac/campus/course/entity/CourseEntity.java) | courses 테이블 매핑 |
| Config | [SecurityConfig.java](../src/main/java/kr/ac/campus/config/SecurityConfig.java) | 세션 로그인·CSRF·정적 파일 접근 허용 |

컨트롤러는 로그인한 학번을 서비스에 전달합니다. 클라이언트가 학생 ID를 임의 지정하지 않습니다.

```java
@PostMapping("/enrollments/{id}")
@ResponseStatus(HttpStatus.NO_CONTENT)
void enroll(Principal principal, @PathVariable long id) {
    service.enroll(principal.getName(), id);
}
```

서비스는 사용자 행 → 강의 행 순서로 잠그고 중복·정원·18학점·시간 충돌을 검사합니다. 리포지토리의 비관적 잠금은 여러 Fargate 태스크 사이에서도 DB 기준으로 직렬화됩니다.

```java
@Lock(LockModeType.PESSIMISTIC_WRITE)
@Query("select c from CourseEntity c where c.id = :id")
Optional<CourseEntity> lockById(@Param("id") long id);
```

JPQL은 테이블명이 아닌 엔티티명과 필드를 사용합니다. `@Transactional` 안에서 다음 변경을 한 번에 커밋하거나 롤백합니다.

```java
enrollments.save(new EnrollmentEntity(studentId, courseId));
course.reserveSeat();
cart.findById(key).ifPresent(cart::delete);
```

관리 중인 강의 엔티티의 인원이 변경되면 Hibernate가 변경을 감지해 UPDATE합니다. 신청·장바구니는 `StudentCourseId` 복합키로 같은 학생·강의 중복을 막습니다. 화면에는 엔티티 대신 `CourseService.State` 등 record DTO를 반환합니다.

## 6. 운영과 범위

- React 빌드 파일 `/assets/**`는 로그인 전에도 제공되며 개인 API는 인증이 필요합니다.
- `spring.jpa.open-in-view=false`: 요청 전체에 영속성 컨텍스트를 유지하지 않습니다.
- `ddl-auto=validate`: 테이블 구조 검증만 합니다. 로컬은 schema.sql, 운영은 Flyway가 스키마를 관리합니다.
- 운영 세션 저장은 Spring Session JDBC를 유지합니다. JPA 전환 대상은 업무 데이터입니다.
- 학기 표시는 샘플 고정값이며 실제 대학 시스템 연동이 아닙니다.
- 챗봇 개발은 중단 상태로 서버 코드를 보존하고 React 화면에는 노출하지 않습니다.

도구 선택 배경은 [React의 직접 앱 구성 가이드](https://react.dev/learn/build-a-react-app-from-scratch)와 [Vite 시작 가이드](https://vite.dev/guide/)를 참고하세요.
