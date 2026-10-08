# 코드 읽기 안내

짧은 코드 예시로 복습하려면 [프론트엔드 React 요약본](REACT_SUMMARY.md)과 [백엔드 Spring·JPA 요약본](BACKEND_SUMMARY.md)을 참고하세요.

처음부터 학습하려면 [React·Spring 상세 가이드](../../../examples/campus/docs/FRONTEND_SPRING_GUIDE.md)를 읽어보세요. 실제 React 컴포넌트와 Spring API의 연결을 설명합니다.

## 패키지 구조

`src/main/java/kr/ac/campus` 아래를 기능별로 나누고 각 기능 안에 entity·repository·service를 둡니다.

```text
campus/
├── CampusApplication.java  # 실행 진입점
├── api/                   # 여러 기능을 연결하는 기존 공통 API
├── auth/service/          # 회원가입
├── student/               # 학생 entity·repository
├── course/                # 강의·수업 시간 entity·repository·service
├── enrollment/            # 신청 entity·repository
├── cart/                  # 장바구니 entity·repository
├── advisor/               # 상담 API·프로필·Python 연결: controller·service·catalog·entity·repository
├── shared/entity/         # 학생·강의 복합키
├── config/                # 보안·운영 세션
├── exception/             # 공통 오류 응답
└── bootstrap/             # 샘플 데이터
```

업무 DB 접근은 **Spring Data JPA**입니다. `entity`에는 학생·강의·시간·신청·장바구니·상담 프로필 매핑을, `repository`에는 조회와 잠금 쿼리를 둡니다. Controller → Service → Repository → DB 순서입니다. 운영 세션은 Spring Session JDBC, 테스트의 데이터 준비·DB 직접 검증은 JdbcTemplate을 유지합니다.

`@Lock(PESSIMISTIC_WRITE)`가 사용자와 강의 행을 순서대로 잠급니다. 서비스의 `@Transactional` 안에서 신청 저장과 관리 엔티티의 인원 변경을 함께 커밋합니다. `ddl-auto=validate`로 스키마만 검증하고 실제 테이블 생성은 로컬 schema.sql, 운영 Flyway가 담당합니다. 자동 스키마 변경은 사용하지 않습니다.

요청·응답용 `record`는 기존처럼 컨트롤러/서비스 내부에 있습니다. 예를 들어 `CourseService.Course`는 API 응답 DTO이며 JPA 엔티티가 아닙니다. `advisor/catalog`는 DB 저장소가 아닌 공식 자료 설정 파일의 조회 역할입니다. 상담 답변 로직은 `src/main/resources/python/advisor.py`에 있습니다. `AdvisorService.reply()`가 인증 사용자 데이터를 조회하고 `PythonAdvisor.reply()`가 로컬 Python에 JSON을 전달합니다. 현재 수강신청 화면에는 상담 UI가 없습니다.

## 서버

| 파일 | 역할 |
| --- | --- |
| `CampusApplication.java` | Spring Boot 실행 진입점 |
| `config/SecurityConfig.java` | 인증 필요 경로, 세션 로그인/로그아웃, CSRF 보호 |
| `api/ApiController.java` | HTTP 입력 검증과 인증 사용자 전달, 회원가입 |
| `exception/ApiErrors.java` | 예외를 화면이 읽는 `message` 응답으로 변환 |
| `course/service/CourseService.java` | 강의 조회, 신청 검증, DB 잠금, 신청/취소/장바구니 변경 |
| `config/ProductionSessionConfig.java` | 운영 컨테이너 간 로그인 세션 공유 및 쿠키 설정 |
| `bootstrap/DemoData.java` | 로컬 체험용 샘플 데이터 초기화 |

수강신청은 `ApiController.enroll()` → `CourseService.enroll()` 순서로 진행합니다. 서비스에서는 **사용자 잠금 → 강의 잠금 → 중복/정원/학점/시간 검사 → 신청·인원·장바구니 변경**을 하나의 트랜잭션으로 수행합니다. 잠금 순서와 트랜잭션 범위는 동시성 보장의 일부이므로 수정할 때 유지해야 합니다.

시간 데이터는 월요일 0~금요일 4, 자정부터 지난 분으로 표현합니다. 예를 들어 월요일 09:00~10:30은 `Meeting(0, 540, 630)`입니다. 충돌 검사는 종료 시각을 제외한 구간으로 비교하므로 수업이 끝나자마자 시작하는 다음 강의를 허용합니다.

## 화면

프론트 원본은 `frontend/src`에 있습니다.

- `App.jsx`: 로그인 여부에 따른 화면 전환과 알림.
- `features/registration/useCampus.js`: 인증·서버 상태·변경 요청·20초 갱신·세션 만료.
- `shared/api/api.js`: 세션 쿠키·CSRF·HTTP 오류 처리.
- `features/courses/courses.js`: 학점 계산, 검색 필터, 시간 충돌 표시.
- `features/auth/AuthPage.jsx`: 로그인·회원가입·체험 로그인.
- `features/dashboard/Dashboard.jsx`: 탐색 메뉴·검색·요약·신청 취소 확인.
- `features/courses/CourseRows.jsx`: 강의 행과 신청·장바구니 버튼.
- `features/timetable/Schedule.jsx`: 개인 시간표와 마우스·키보드 미리보기.
- `shared/ui/Modal.jsx`: 초점과 Escape 처리를 포함하는 dialog.
- `styles.css`: 스타일 import 진입점. 실제 규칙은 `features/`의 해당 기능과 `shared/`에 나눴습니다.

React가 상태에서 화면을 렌더링하므로 `innerHTML`로 목록을 만들거나 이벤트를 다시 연결하지 않습니다. 사용자 문자열은 JSX 텍스트로 출력됩니다. 서버가 최종 신청 규칙을 검증합니다.

`npm --prefix frontend run build`는 `src/main/resources/static`에 배포 결과물을 생성합니다. 원본을 수정한 뒤 빌드해야 Spring 화면에 반영됩니다. 수강신청 서버의 Python 상담 API는 화면에 연결되어 있지 않습니다. 별도 `academic-advisor` React 화면은 기존 Java 상담 서버에 연결됩니다.

## 설정과 서식

- `.editorconfig`: UTF-8, 줄바꿈, 들여쓰기 기본값.
- `.prettierrc.json`: 화면 코드는 2칸, Java는 4칸, 한 줄 길이는 100자를 기준으로 합니다.
- Prettier 사용 시 Java에는 `prettier-plugin-java`, XML에는 `@prettier/plugin-xml`을 함께 사용합니다. 포맷터는 개발 편의 도구이며 React 빌드에는 Node.js가 필요하고, 빌드된 JAR 실행에는 Node.js가 필요하지 않습니다.
- 이미 적용된 `db/migration/V*.sql`은 Flyway 체크섬이 있으므로 서식이나 주석만을 위해서도 수정하지 않습니다. 새 DB 변경은 새로운 버전의 파일로 추가합니다.
- `mvnw`, `mvnw.cmd`, CloudFormation 리소스 정의는 자동 생성/배포 성격을 고려해 불필요한 구조 변경을 피합니다.

검증 명령은 `./mvnw test`, 운영 DB 검증은 `./deploy/check-postgres.sh`입니다. 후자는 Docker가 필요하고 임시 DB에서만 실행됩니다.
