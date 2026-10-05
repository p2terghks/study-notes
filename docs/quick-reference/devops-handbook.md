## 이 가이드의 목표와 읽는 순서

**목표는 “코드가 내 컴퓨터에서 실행된다”를 넘어, 팀이 같은 방법으로 개발하고 안전하게 배포하며 장애를 복구할 수 있게 만드는 것입니다.** Spring Boot API + React 웹 + PostgreSQL을 기준으로 GitHub Actions, Docker, AWS ECS, Terraform을 연결합니다.

> 이 문서는 구축 순서와 실무 판단을 자세히 설명하는 가이드입니다. 코드에는 **완성된 파일**, **기존 파일에 추가하는 발췌**, **환경값을 바꿔야 하는 템플릿**을 구분했습니다. AWS 리소스를 실제 생성하거나 배포한 결과를 뜻하지 않습니다. 예제 코드 묶음은 마지막 항목에서 받을 수 있습니다.

|처음 배우는 경우|이미 개발하는 경우|운영을 맡은 경우|
|---|---|---|
|용어 → 전체 구조 → 로컬 환경 → API → CI|CI → Docker → 인증 → CD → DB 변경|모니터링 → 장애 대응 → 보안 → 백업 → 비용|

본문의 명령은 따로 표시하지 않으면 **저장소 최상위 디렉터리**에서 실행합니다. `$` 프롬프트는 붙이지 않았습니다. 예시 리소스 이름과 계정 번호는 본인 값으로 바꿉니다. 클라우드 생성·배포 명령은 과금과 서비스 변경을 일으키므로 실습용 계정/환경부터 사용합니다.

이전 자료와 연결해서 읽기: [GitHub](github-reference.html) · [Docker](docker-reference.html) · [AWS CLI](aws-cli-reference.html) · [Terraform](terraform-reference.html) · [실행 가능한 Node 기반 ECS 프로젝트](cloud-cicd-reference.html).

## CI · CD · IDE · DevOps부터 구분하기

|용어|기능|실제 예|완료 기준|
|---|---|---|---|
|IDE|코드 작성·실행·디버깅을 돕는 프로그램|IntelliJ IDEA, VS Code|브레이크포인트에서 멈추고 변수 확인|
|통합 개발환경 구축|도구·설정·실행 방법을 팀에서 맞춤|JDK, Node, DB, 환경변수, 명령 문서|새 팀원이 README대로 실행|
|CI, 지속적 통합|변경을 자주 합치고 자동 검증|PR마다 테스트·빌드 실행|실패한 코드가 main에 합쳐지지 않음|
|Continuous Delivery|언제든 배포할 수 있는 산출물 준비|테스트된 이미지 + 운영 승인 대기|승인 후 재빌드 없이 배포|
|Continuous Deployment|검증된 변경을 자동으로 운영에 반영|승인 없이 정책에 따라 배포|운영 검증·자동 복구까지 동작|
|DevOps|개발과 운영이 함께 변경·품질·복구 책임을 관리|개발자가 배포와 장애 분석 참여|인수인계보다 피드백이 빨라짐|
|IaC|인프라 구성을 코드로 선언|Terraform의 VPC, ECS 정의|변경 검토·재현·이력 추적 가능|
|관측 가능성|시스템 내부 상태를 외부 신호로 이해|로그·메트릭·트레이스|어디서 왜 느려졌는지 설명 가능|

“GitHub Actions를 쓴다”만으로 CI/CD가 완성되지는 않습니다. 무엇을 검증하고, 어떤 파일을 배포하고, 실패를 어떻게 발견하고 되돌릴지가 연결되어야 합니다.

## 전체 구조: 코드 한 줄이 사용자에게 도착하는 과정

```text
개발자 IDE
  ├─ React :5173 ── 개발 프록시 ── Spring :8080 ── PostgreSQL :5432
  └─ git push → PR → CI 테스트/빌드 → 리뷰 → main
                                         ↓
                               Docker 이미지 → ECR
                                         ↓ 같은 이미지 digest
                              GitHub OIDC → AWS 배포 역할
                                         ↓
사용자 → HTTPS → ALB → ECS Fargate의 Spring → RDS PostgreSQL
사용자 → HTTPS → CloudFront → 비공개 S3의 React 정적 파일
                         ↓
                 CloudWatch 로그·메트릭·알람
```

프런트엔드와 백엔드는 별도 배포 단위입니다. React 소스는 브라우저에서 실행할 정적 파일로 빌드되고, Spring은 서버에서 실행됩니다. ECR은 이미지를 보관할 뿐 요청을 처리하지 않습니다. ECS는 컨테이너 실행 상태를 관리하고, Fargate는 서버 관리 부담을 줄이는 실행 방식입니다.

**처음부터 위 구조를 전부 만들 필요는 없습니다.** 로컬 → CI → 개발용 배포 → DB 변경 → 운영 통제 순서로 쌓습니다. 학습용 단일 태스크와 운영용 다중 AZ 구성의 목적도 구분합니다.

## 클라우드 개발자가 하는 일과 결과물

|업무|구체적으로 하는 일|남겨야 하는 결과물|
|---|---|---|
|요구사항 분석|예상 사용자, 트래픽, 데이터 민감도, 장애 허용 범위 확인|성능·보안·가용성 기준|
|구조 설계|서비스 경계, 동기/비동기 처리, 네트워크 경로 결정|구성도, 설계 결정 기록|
|애플리케이션 개발|API, 인증, 검증, DB 접근, 오류 처리|코드, API 문서, 테스트|
|개발환경 표준화|런타임·패키지 잠금·실행 절차 통일|README, Compose, 환경변수 예시|
|자동화|빌드·테스트·배포·복구 단계를 코드화|워크플로, Dockerfile, 배포 기록|
|인프라 관리|리소스 생성, 상태 관리, 접근 제어|Terraform, 승인된 plan|
|운영|로그 분석, 알람 대응, 성능·비용 개선|대시보드, 런북, 개선 PR|
|보안|최소 권한, 비밀 관리, 의존성 보완|역할 정책, 회전 절차, 조치 기록|
|복구|백업·복원·롤백을 실제 연습|복원 소요 시간, 복구 검증 기록|

작은 팀에서는 한 사람이 여러 역할을 맡을 수 있습니다. 큰 팀에서는 플랫폼 엔지니어·SRE·보안 담당자와 나눕니다. 개발자는 최소한 **자신이 만든 기능의 배포 조건, 필요한 권한, 정상 지표, 실패 시 대응 방법**을 설명할 수 있어야 합니다.

## 1단계: 저장소 구조와 버전 규칙 정하기

설명용 저장소의 구조입니다. 이번 다운로드는 이 구조에 넣을 설정 템플릿이며, 완성된 Spring·React 애플리케이션 전체는 아닙니다.

```text
team-web/
├── backend/                   # Spring 프로젝트: Maven Wrapper 포함
│   ├── pom.xml
│   ├── mvnw, .mvn/
│   ├── Dockerfile
│   └── src/{main,test}/
├── frontend/                  # React + Vite 프로젝트
│   ├── package.json, package-lock.json
│   └── src/
├── infra/                     # Terraform
├── deploy/task-definition.json
├── scripts/verify-release.py
├── .github/workflows/ci.yml
├── compose.yaml
├── .env.example
└── README.md
```

|대상|팀에서 고정할 내용|이유|
|---|---|---|
|Java|예: JDK 21, 배포 런타임도 같은 major|컴파일·실행 호환성|
|Spring Boot|지원 중인 정확한 버전을 pom.xml에 지정|의존성 조합과 보안 업데이트 관리|
|Node|예제는 22.x, 팀에서는 패치와 지원 기간도 확인|CI와 로컬 빌드 차이 감소|
|npm|lockfile 커밋, 설치는 `npm ci`|의존성 재현|
|Maven|Wrapper와 wrapper 설정 커밋|시스템 Maven 차이 감소|
|Docker 이미지|운영에서는 검토한 digest 기록|태그가 이동해도 동일 이미지 추적|
|Terraform/provider|지원 버전 범위 + lockfile|provider 변경 통제|

버전 숫자는 최신 버전을 의미하지 않습니다. 신규 프로젝트 생성 시 지원 정책을 확인하고, 버전 변경을 별도 PR로 테스트합니다. 비밀값·빌드 결과·개발자 개인 IDE 설정은 커밋 대상에서 구분합니다.

```gitignore
.env
.env.*
!.env.example
backend/target/
frontend/node_modules/
frontend/dist/
**/.terraform/
*.tfstate
*.tfstate.*
*.tfplan
crash.log
```

`.terraform.lock.hcl`은 커밋합니다. `.env.example`에는 변수 이름과 가짜 값만 넣습니다. 이미 커밋된 비밀은 `.gitignore`에 추가해도 사라지지 않으므로 폐기·회전이 먼저입니다.

## 2단계: IDE에서 실행·디버깅 연결하기

|도구|사용법|확인할 내용|
|---|---|---|
|IntelliJ IDEA|`backend/pom.xml`을 Maven 프로젝트로 열고 JDK 설정|프로젝트 JDK와 실행 JDK 일치|
|VS Code|Java 확장, Java 디버거, ESLint 등을 프로젝트에 맞게 설치|백엔드 디버그 실행과 프런트 오류 표시|
|터미널|각 앱의 실행 명령을 README에 고정|IDE 밖에서도 실행 가능|
|브라우저 DevTools|Network, Console, Sources 확인|API 주소·상태 코드·요청 내용|
|DB 클라이언트|로컬 개발 DB 계정으로 접속|테이블·데이터·트랜잭션 확인|

```bash
# 터미널 A: backend 폴더에서
./mvnw spring-boot:run -Dspring-boot.run.profiles=local
# 터미널 B: frontend 폴더에서
npm ci
npm run dev
```

브레이크포인트는 “이 줄을 실행하기 직전에 멈추기”입니다. 컨트롤러에 설정하고 요청을 보내면 DTO의 값, 서비스 호출, 쿼리 결과를 순서대로 살펴볼 수 있습니다. Step Over는 현재 줄을 실행하고 다음 줄로, Step Into는 호출한 메서드 안으로 들어갑니다.

VS Code의 `.vscode/launch.json` 예시입니다. `mainClass`는 실제 클래스의 전체 이름으로 바꿉니다. 환경변수는 IDE의 실행 구성에도 별도로 전달해야 합니다. Compose가 읽는 `.env`가 Java 실행에 자동 전달되지는 않습니다.

```json
{
  "version": "0.2.0",
  "configurations": [{
    "type": "java",
    "name": "Spring 로컬 디버그",
    "request": "launch",
    "mainClass": "com.example.demo.DemoApplication",
    "args": "--spring.profiles.active=local",
    "env": {"DB_URL": "jdbc:postgresql://localhost:5432/app"}
  }]
}
```

DB 사용자·비밀번호는 개인 실행 설정 또는 셸 환경에서 주입합니다. 원격 디버그 포트를 인터넷에 공개하지 않습니다. [VS Code Java 디버깅](https://code.visualstudio.com/docs/java/java-debugging).

## 3단계: Docker Compose로 개발 DB 통일하기

**완성 파일: `compose.yaml`**. 앱은 IDE에서 실행하고 DB만 컨테이너로 띄우는 구성입니다.

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: app
      POSTGRES_USER: app
      POSTGRES_PASSWORD: ${DB_PASSWORD:?set DB_PASSWORD in .env}
    ports:
      - "127.0.0.1:5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app -d app"]
      interval: 5s
      timeout: 3s
      retries: 10
volumes:
  pgdata:
```

`.env.example`을 `.env`로 복사하고 개발용 비밀번호를 입력합니다.

```bash
cp .env.example .env
# .env의 DB_PASSWORD 값을 편집한 다음 실행
 docker compose up -d --wait db
 docker compose ps
 docker compose logs --tail=50 db
```

|설정·명령|기능|주의점|
|---|---|---|
|`ports`|호스트 5432에서 컨테이너 5432로 전달|127.0.0.1로 로컬에만 바인딩|
|`volumes`|컨테이너 교체 후에도 데이터 유지|비밀번호 env 변경만으로 기존 DB 암호가 바뀌지 않음|
|`healthcheck`|DB 준비 상태 검사|인증·스키마·전체 앱 정상까지 보장하지 않음|
|`up -d --wait`|백그라운드 실행 후 준비 상태 대기|healthcheck 없는 서비스는 실행 여부 수준|
|`down`|컨테이너·기본 네트워크 정리|명명 볼륨은 유지|
|`down -v`|볼륨까지 제거|로컬 DB 데이터 삭제 명령|

앱도 Compose에 넣으면 DB 주소는 `localhost`가 아니라 서비스 이름 `db`입니다. `depends_on`만으로 준비 완료가 보장되지는 않으며 `condition: service_healthy`로 연결할 수 있습니다. 시작 후 DB가 끊기는 문제는 앱의 재연결·오류 처리로 다룹니다. [Compose 시작 순서](https://docs.docker.com/compose/how-tos/startup-order/).

## 4단계: Spring 설정과 배포에 필요한 기능

기존 Maven 프로젝트에 Web, Validation, Data JPA, PostgreSQL driver, Actuator, Flyway 의존성을 구성합니다. 의존성 버전은 Spring Boot가 관리하는 조합을 우선 사용하고, PostgreSQL용 Flyway 모듈이 필요한 버전이면 함께 추가합니다.

**`application-local.yml` 설정 발췌**:

```yaml
spring:
  datasource:
    url: ${DB_URL:jdbc:postgresql://localhost:5432/app}
    username: ${DB_USER:app}
    password: ${DB_PASSWORD}
  jpa:
    hibernate:
      ddl-auto: validate
  flyway:
    enabled: true
management:
  endpoints:
    web:
      exposure:
        include: health,info
  endpoint:
    health:
      show-details: never
      probes:
        enabled: true
server:
  shutdown: graceful
```

|기능|필요한 설정·코드|이유|
|---|---|---|
|외부 설정|`${DB_PASSWORD}`|환경마다 코드를 고치지 않음|
|스키마 검증|`ddl-auto: validate`|JPA 모델과 DB 불일치 감지|
|스키마 변경|Flyway SQL migration|순서·이력을 관리|
|상태 검사|Actuator health|프로세스 실행과 서비스 준비 구분|
|정상 종료|graceful shutdown|배포 교체 중 진행 중인 요청 처리|
|릴리스 식별|환경변수 `RELEASE_SHA`|현재 요청을 처리한 코드 추적|
|입력 검증|`@Valid`, `@NotBlank`|잘못된 입력의 DB 유입 방지|
|예외 응답|`@RestControllerAdvice`|일관된 오류 형태|

`local` 설정이 운영에 자동 적용되지는 않습니다. 운영은 `application-prod.yml`과 `SPRING_PROFILES_ACTIVE=prod`로 분리합니다. 별도 migration 작업을 사용한다면 운영 앱의 `spring.flyway.enabled=false`로 중복 실행을 피합니다. `ddl-auto=create`와 운영 DB 초기화 스크립트를 섞지 않습니다.

Actuator 경로를 전부 외부 공개하지 않습니다. liveness는 재시작 필요 여부, readiness는 요청 수용 가능 여부입니다. 공유 DB 장애를 liveness에 묶으면 모든 인스턴스가 재시작할 수 있습니다. readiness에도 DB를 넣을지는 트래픽 차단의 영향을 보고 결정합니다. [Actuator](https://docs.spring.io/spring-boot/reference/actuator/endpoints.html).

## 5단계: DTO · 서비스 · API와 필요한 메서드

클라우드에 올릴 앱도 기본은 요청·검증·처리·응답입니다. DTO는 요청/응답 모양, Entity는 DB 저장 구조, Service는 업무 규칙을 담당합니다.

**구조 설명용 발췌**입니다. import, Entity, Repository 구현과 예외 처리는 기존 Spring 가이드에 이어 붙입니다.

```java
public record CreateTodoRequest(@NotBlank String title) {}
public record TodoResponse(Long id, String title) {}

@RestController
@RequestMapping("/api/todos")
@RequiredArgsConstructor
class TodoController {
    private final TodoService service;

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    TodoResponse create(@Valid @RequestBody CreateTodoRequest request) {
        return service.create(request.title());
    }
}

@Service
@RequiredArgsConstructor
class TodoService {
    private final TodoRepository repository;

    @Transactional
    public TodoResponse create(String title) {
        Todo saved = repository.save(new Todo(title));
        return new TodoResponse(saved.getId(), saved.getTitle());
    }
}
```

`@RequiredArgsConstructor`는 Lombok이 필요합니다. Lombok을 쓰지 않으면 생성자를 직접 작성해 주입합니다. 사용자 소유 데이터라면 인증 사용자와 소유권 검증을 추가해야 합니다.

|요소|기능|사용 시점|
|---|---|---|
|`@RequestBody`|JSON → Java 객체 변환|JSON 요청 본문 받을 때|
|`@Valid`|DTO 제약 검사|입력 경계에서 검증|
|`@Transactional`|업무 변경을 트랜잭션으로 묶음|여러 저장 작업의 일관성|
|`repository.save()`|Entity 저장 처리|생성·변경을 영속화|
|`findById()`|PK로 조회, Optional 반환|없으면 404 등으로 변환|
|`Pageable`|페이지와 정렬 정보를 받음|무제한 조회 방지, 최대 크기 제한|
|`@RestControllerAdvice`|컨트롤러 예외 공통 처리|내부 stack trace를 응답에서 숨김|

`save()` 직후에 SQL INSERT가 항상 바로 실행된다고 단정하지 않습니다. flush/commit과 ID 전략에 영향을 받습니다. 데이터 무결성은 검증 코드뿐 아니라 DB의 NOT NULL, UNIQUE, FK로도 보장합니다.

## 6단계: React에서 API 연결과 배포 설정 이해하기

개발에서는 Vite 프록시로 `/api` 요청을 Spring에 전달할 수 있습니다. **`vite.config.js` 발췌**:

```js
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: { '/api': 'http://localhost:8080' }
  }
});
```

**API 함수 발췌**. 서버가 JSON 응답을 준다는 계약을 전제로 합니다.

```js
export async function createTodo(title, signal) {
  const response = await fetch('/api/todos', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
    signal
  });
  if (!response.ok) {
    throw new Error(`저장 실패 (${response.status})`);
  }
  return response.json();
}
```

|함수·기능|역할|운영에서 확인|
|---|---|---|
|`fetch()`|HTTP 요청|404·500도 Promise 자체는 성공하므로 `ok` 확인|
|`JSON.stringify()`|객체를 JSON 문자열로 변환|요청 DTO와 필드명 일치|
|`response.json()`|응답 JSON 해석|204처럼 본문 없는 응답은 따로 처리|
|`AbortController`|필요 없어진 요청 중단|화면 이동 시 리소스 정리|
|`useState()`|로딩·오류·데이터 상태|중복 제출 방지, 오류 표시|
|`useEffect()`|외부 시스템 동기화|cleanup과 재실행 고려|

Vite 프록시는 개발 서버 기능이며 `dist/`에 포함되지 않습니다. 운영에서는 CloudFront `/api/*` 동작을 ALB로 라우팅하거나, 별도 API 도메인과 정확한 CORS 설정을 사용합니다. React의 `VITE_*` 값은 브라우저에 노출될 수 있으므로 DB 비밀번호나 AWS 키를 넣으면 안 됩니다. [Vite 환경변수](https://vite.dev/guide/env-and-mode), [서버 프록시](https://vite.dev/config/server-options#server-proxy).

## 7단계: 테스트를 어디까지 자동화할까

|종류|검증 내용|도구 예|실패 예|
|---|---|---|---|
|단위 테스트|작은 업무 규칙|JUnit, Vitest|완료된 할 일을 다시 완료할 때 규칙 위반|
|API 테스트|입력·상태 코드·응답|MockMvc|빈 제목인데 201 반환|
|DB 통합 테스트|실제 DB 제약·SQL·트랜잭션|Testcontainers + PostgreSQL|중복 값이 저장됨|
|컴포넌트 테스트|사용자 조작과 UI 반응|Testing Library|저장 실패 메시지가 안 보임|
|E2E|핵심 사용자 흐름|Playwright|로그인→생성→조회 실패|
|스모크 테스트|배포 직후 최소 정상 여부|curl, 전용 점검 스크립트|새 버전인데 상태 API 실패|
|부하 테스트|목표 트래픽의 지연·오류|k6 등|동시 요청에서 연결 풀 고갈|

테스트의 개수보다 실패를 잡는 능력이 중요합니다. 정상 생성, 입력 오류, 권한 오류, 데이터 없음, 동시 수정, 외부 장애를 대표 사례로 잡습니다. CI에서 테스트를 건너뛰거나 실패해도 성공으로 처리하면 배포 게이트가 무력해집니다.

```bash
# backend 폴더: 프로젝트 설정에 따라 통합 테스트 플러그인도 연결
./mvnw -B verify
# frontend 폴더: package.json에 해당 scripts와 도구가 있어야 함
npm ci
npm run lint
npm run test:ci
npm run build
```

`verify`가 모든 통합 테스트를 자동 발견하는 것은 아닙니다. Failsafe 등의 설정과 클래스 이름 규칙을 확인합니다. 테스트 DB는 운영 DB와 분리하고, 테스트 종료 시 격리 데이터가 정리되게 합니다.

## 8단계: 브랜치 · PR · 코드 검토 규칙

1. `feature/todo-create` 같은 짧은 작업 브랜치를 만듭니다.
2. 기능과 실패 사례 테스트를 함께 커밋합니다.
3. PR에는 문제, 변경 행동, 검증 결과, DB·설정 변경 유무를 적습니다.
4. CI 통과와 리뷰 후 main에 병합합니다.
5. main의 특정 커밋으로 릴리스를 만들고 배포 기록에 연결합니다.

```bash
git switch -c feature/todo-create
git add backend/src frontend/src
git commit -m "feat: add todo creation with validation"
git push -u origin feature/todo-create
```

GitHub ruleset/브랜치 보호에서 필수 체크, 리뷰, 직접 push 제한을 구성합니다. 워크플로 파일을 만들기만 해서는 병합 제한이 생기지 않습니다. 배포 Environment에는 운영 배포 브랜치와 승인자를 설정하며, 사용 가능한 보호 기능은 요금제·저장소 공개 여부에 따라 확인합니다.

**`.github/CODEOWNERS` 예시**:

```text
/backend/ @example/backend-team
/infra/ @example/platform-team
/.github/workflows/ @example/platform-team
```

팀 핸들은 실제 접근 권한이 있는 팀으로 바꿉니다. 소유자를 선언하는 것과 리뷰를 필수로 요구하는 것은 별도 설정입니다. [환경과 배포 보호](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments).

## 9단계: GitHub Actions CI 파일 작성하기

**완성 형태의 템플릿: `.github/workflows/ci.yml`**. 저장소 구조와 npm scripts가 앞의 조건을 만족해야 실행됩니다. JDK 21과 Node 22를 사용하며 버전은 팀 기준에 맞게 바꿉니다.

```yaml
name: CI
on:
  pull_request:
  push:
    branches: [main]
permissions:
  contents: read
concurrency:
  group: ci-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
jobs:
  backend:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    defaults:
      run:
        working-directory: backend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: '21'
          cache: maven
      - run: chmod +x mvnw
      - run: ./mvnw -B verify
  frontend:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '22'
          cache: npm
          cache-dependency-path: frontend/package-lock.json
      - run: npm ci
      - run: npm run lint
      - run: npm run test:ci
      - run: npm run build
```

읽기 편하게 major 태그를 썼습니다. 운영 저장소는 검토한 Action의 전체 commit SHA로 고정하고 업데이트 PR을 받는 방식을 권장합니다. 이 예제의 버전은 “최신 버전 목록”이 아닙니다.

|키|기능|헷갈리기 쉬운 점|
|---|---|---|
|`on`|실행 이벤트|push와 PR 이벤트는 서로 다름|
|`jobs`|별도 runner에서 실행할 작업|파일·환경변수를 자동 공유하지 않음|
|`steps`|job 안에서 순서대로 실행|이전 step 실패 시 기본적으로 후속 실행 중단|
|`uses`|재사용 Action 실행|입력은 `with`|
|`run`|셸 명령 실행|작업 폴더와 셸 종류 확인|
|`needs`|다른 job 성공 후 실행|배포가 테스트를 기다리게 할 때|
|`permissions`|GITHUB_TOKEN 권한|AWS IAM 권한과 별도|
|`timeout-minutes`|무한 대기 제한|외부 호출에도 timeout 필요|
|`concurrency`|동시 실행 통제|CI 취소와 운영 배포 취소 정책은 구분|

필수 체크에는 두 job을 모두 연결합니다. PR에서 AWS 배포 자격증명을 사용할 필요가 없습니다. 신뢰하지 않는 PR 코드를 높은 권한으로 실행하는 `pull_request_target` 패턴은 피합니다. [Workflow 문법](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax), [Concurrency](https://docs.github.com/en/actions/concepts/workflows-and-actions/concurrency).

## 10단계: 캐시 · 산출물 · 보안 검사를 구분하기

**캐시는 속도를 위한 재사용, 산출물은 결과를 전달하기 위한 보관**입니다. 캐시가 없어도 빌드가 성공해야 합니다. 운영 배포는 “어떤 산출물인지” 추적 가능해야 합니다.

|종류|예|관리 방법|
|---|---|---|
|의존성 캐시|Maven 저장소, npm 캐시|lockfile 등으로 키 변경|
|빌드 산출물|JAR, dist, 테스트 리포트|커밋·실행 ID와 연결, 보관 기간 설정|
|컨테이너 이미지|ECR의 이미지|digest 기준 식별, 취약점·서명 검증 정책|
|SBOM|패키지 구성 목록|이미지와 함께 보관|
|테스트 증거|JUnit XML, E2E 보고서|실패 원인을 PR에서 찾을 수 있게|

보안 게이트는 비밀 유출 탐지, 의존성 취약점, 정적 분석, 이미지 검사, IaC 정책 검사로 나눌 수 있습니다. 발견 건수만으로 운영 가능 여부를 결정하지 말고 심각도·악용 가능성·노출 경로·해결 가능성을 고려합니다. 예외를 허용할 때는 담당자와 만료일을 남깁니다.

CI 파일의 기본 테스트만으로 이 검사가 전부 실행되는 것은 아닙니다. 팀의 스캐너를 별도 step으로 추가하고 **종료 코드가 실제로 실패를 전달하는지** 확인합니다.

## 11단계: Spring Dockerfile과 이미지 식별

**`backend/Dockerfile` 템플릿**. Maven이 최종 파일을 `target/app.jar`로 만들도록 `pom.xml`의 `<build>` 아래에 `<finalName>app</finalName>`을 설정합니다. 프로젝트 의존성 다운로드가 가능한 빌드 환경이 필요합니다.

```dockerfile
FROM eclipse-temurin:21-jdk AS build
WORKDIR /src
COPY .mvn .mvn
COPY mvnw pom.xml ./
RUN chmod +x mvnw
COPY src src
RUN ./mvnw -B -DskipTests package

FROM eclipse-temurin:21-jre
WORKDIR /app
COPY --from=build /src/target/app.jar /app/app.jar
USER 10001:10001
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
```

이 빌드는 **앞선 CI 테스트가 통과한 동일 커밋**을 패키징하는 용도입니다. 단독 사용이면 먼저 테스트를 실행합니다. `USER`는 root 대신 숫자 UID/GID로 실행하며, 앱이 쓰는 경로는 권한을 별도로 설계합니다. 실행 이미지는 운영에서 digest로 고정하고 주기적으로 갱신합니다.

**`backend/.dockerignore`**:

```text
target
.git
.env
.env.*
*.log
```

```bash
docker build --platform linux/amd64 -t team-api:local backend
# .env.backend에는 Spring용 DB_URL/DB_USER/DB_PASSWORD 등을 별도로 작성
# macOS Docker Desktop에서 호스트 DB에 접근할 때 host.docker.internal 사용 가능
docker run --rm -p 127.0.0.1:8080:8080 --env-file .env.backend team-api:local
```

`EXPOSE`는 문서 성격의 포트 선언이며 호스트 포트를 공개하지 않습니다. `-p`가 전달을 설정합니다. ARM Mac에서 빌드한 이미지와 ECS의 CPU 아키텍처가 일치해야 합니다. `latest`만으로 배포하면 무엇을 실행 중인지 불명확해지므로 커밋 태그와 `sha256` digest를 기록합니다.

## 12단계: AWS 배포 전에 준비할 리소스

|순서|리소스|만드는 이유|점검 항목|
|---|---|---|---|
|1|계정·SSO·예산 알림|접근과 비용 범위 확정|개발/운영 분리, MFA|
|2|VPC·서브넷·라우트|트래픽 경로 구성|다중 AZ, 인터넷 경로|
|3|Security Group|필요한 연결만 허용|ALB → 앱 → DB|
|4|ECR·로그 그룹|이미지와 실행 로그 저장|보관·삭제 정책|
|5|IAM 역할·Secrets|실행과 배포 권한 분리|최소 권한, 비밀 참조|
|6|RDS|영속 데이터 저장|비공개 접근, 백업, 암호화|
|7|ALB·대상 그룹·ACM|HTTPS와 요청 분산|인증서·헬스 경로·포트|
|8|ECS cluster·task·service|앱 실행과 복제 수 관리|이미지·역할·네트워크 연결|
|9|Route 53/DNS|사용자 도메인 연결|인증서 도메인과 일치|
|10|GitHub OIDC·Environment|배포 주체 인증|정확한 저장소·환경 제한|

처음 ECS service를 만들 때에도 실행 가능한 이미지가 필요합니다. Terraform이 존재하지 않는 이미지로 서비스 안정화를 기다리지 않도록 **초기 이미지 게시 → 서비스 생성 → 이후 CD 갱신** 순서를 정합니다. DB 준비와 마이그레이션 완료도 앱 시작 조건입니다.

학습용이라도 RDS를 인터넷 전체에 열지 않습니다. 접속이 필요하면 승인된 관리 경로를 마련합니다. 이 가이드의 AWS 명령은 인증된 CLI와 사전 구성된 리소스를 전제로 합니다.

## 13단계: IAM 역할 4개를 구분하기

|역할|누가 사용?|대표 권한|피해야 할 구성|
|---|---|---|---|
|개발자 역할|SSO로 로그인한 사람|로그·배포 상태 조회, 승인된 작업|장기 관리자 키 공유|
|GitHub 배포 역할|OIDC로 인증한 workflow|ECR push, task 등록, 지정 service 갱신|계정 전체 AdministratorAccess|
|Task execution role|ECS 실행 에이전트|이미지 pull, 로그 전송, 시작 시 secret 취득|앱의 업무 권한까지 혼합|
|Task role|컨테이너 안의 앱|지정 S3·SQS 등 업무 API|AWS 키를 이미지에 내장|

배포 역할의 `iam:PassRole`은 **허용한 task role과 execution role ARN**으로 제한하고, 전달 대상 서비스 조건을 적용합니다. `ecr:GetAuthorizationToken`처럼 `Resource: "*"`가 필요한 작업과 저장소 ARN으로 제한 가능한 작업은 정책 문장을 나눕니다.

비밀이 KMS 고객 관리 키로 암호화되었다면 secret 접근 외에 해당 키 복호화 권한과 키 정책도 맞아야 합니다. AWS SDK는 task role의 임시 자격증명을 사용하게 하고 코드에 access key를 넣지 않습니다. [Task role](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-iam-roles.html), [Execution role](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_execution_IAM_role.html).

## 14단계: GitHub OIDC 인증과 신뢰 정책

OIDC는 GitHub가 발급한 신원 토큰을 AWS가 검증하여 임시 권한을 주는 방식입니다. “토큰을 발급받을 수 있다”와 “AWS에서 무엇을 할 수 있다”는 별개입니다.

```text
GitHub job → OIDC JWT → AWS STS 검증 → 임시 자격증명 → 허용된 AWS API
                 ↑ issuer/audience/subject가 신뢰 정책과 일치해야 함
```

**IAM 역할 trust policy 템플릿**. `ACCOUNT_ID`와 `VERIFIED_GITHUB_SUBJECT`를 실제 값으로 바꿉니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "Federated": "arn:aws:iam::ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
    },
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": {
        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
        "token.actions.githubusercontent.com:sub": "VERIFIED_GITHUB_SUBJECT"
      }
    }
  }]
}
```

GitHub `sub` 형태는 저장소 설정, 생성 시점, Environment 사용 여부에 영향을 받습니다. 공식 문서의 현재 subject 형식과 자신의 설정을 확인해야 하며, 오래된 `repo:조직/저장소:...` 예제를 무조건 복사하지 않습니다. Environment를 쓰면 subject의 문맥이 branch 대신 environment가 될 수 있으므로 해당 Environment의 배포 브랜치 제한도 구성합니다. 토큰 원문을 로그에 남기지 않습니다.

**job에 추가하는 인증 발췌**:

```yaml
permissions:
  contents: read
  id-token: write
steps:
  - uses: aws-actions/configure-aws-credentials@v6.3.0
    with:
      role-to-assume: ${{ vars.AWS_ROLE_ARN }}
      aws-region: ${{ vars.AWS_REGION }}
  - run: aws sts get-caller-identity
```

`get-caller-identity`로 계정·역할을 확인하고 의도한 환경과 다르면 중단합니다. [GitHub OIDC와 AWS](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws), [AWS 공식 인증 Action](https://github.com/aws-actions/configure-aws-credentials).

## 15단계: CD 파이프라인 설계와 승격

**안전한 순서**: 테스트 → 이미지 생성 → 검사 → digest 기록 → 개발 배포 → 검증 → 승인 → 동일 digest 운영 배포 → 관찰.

|단계|입력|출력|실패하면|
|---|---|---|---|
|테스트|커밋|테스트 결과|배포 중단|
|빌드|같은 커밋|ECR 이미지 digest|배포 중단|
|준비|이미지·설정·DB 변경 계획|task definition|잘못된 참조 수정|
|DB 변경|검토된 migration|적용 버전·종료 코드|서비스 갱신 중단|
|배포|승인된 task definition|새 service deployment|자동 복구 정책 확인|
|검증|예상 revision·endpoint|정확한 배포·스모크 결과|원인 분석·롤백 판단|
|운영 관찰|메트릭·로그|릴리스 기록|알람 대응|

운영 승인 뒤에 이미지를 다시 빌드하면 개발에서 확인한 이미지와 달라질 수 있습니다. React도 정적 빌드 산출물 버전을 보관합니다. 환경별 프런트 설정을 빌드에 넣으면 환경마다 다른 산출물이라는 사실을 관리해야 합니다.

CI와 CD가 서로 다른 workflow라면 main push만 받는다는 이유로 CI 통과가 보장되지는 않습니다. 같은 workflow의 `needs`로 연결하거나, 성공한 CI 실행과 정확한 commit/artifact를 검증하는 승격 절차를 사용합니다.

운영 배포는 `cancel-in-progress: false`로 중간 취소를 피하고 같은 환경의 concurrency group을 공유합니다. 다만 이것만으로 모든 대기 배포의 순서·보존을 보장한다고 생각하지 않습니다. 긴급 배포와 이전 커밋 재배포를 구분하는 운영 규칙도 필요합니다.

## 16단계: ECS 배포 Action 사용법

다음은 **인증·이미지 게시·migration이 완료된 CD job에 넣는 발췌**입니다. `IMAGE_URI`는 태그가 아닌 `registry/repository@sha256:...` 형태로 앞 단계에서 확보한 값입니다.

```yaml
- uses: actions/checkout@v4
- name: Render task definition
  id: render
  uses: aws-actions/amazon-ecs-render-task-definition@v1
  with:
    task-definition: deploy/task-definition.json
    container-name: api
    image: ${{ env.IMAGE_URI }}
- name: Deploy
  id: deploy
  uses: aws-actions/amazon-ecs-deploy-task-definition@v2
  with:
    task-definition: ${{ steps.render.outputs.task-definition }}
    cluster: ${{ vars.ECS_CLUSTER }}
    service: ${{ vars.ECS_SERVICE }}
    wait-for-service-stability: true
- name: Check exact release
  env:
    EXPECTED_TASK: ${{ steps.deploy.outputs.task-definition-arn }}
    CLUSTER: ${{ vars.ECS_CLUSTER }}
    SERVICE: ${{ vars.ECS_SERVICE }}
  run: |
    aws ecs describe-services --cluster "$CLUSTER" --services "$SERVICE" > service.json
    python3 scripts/verify-release.py service.json "$EXPECTED_TASK"
```

`render`는 JSON 안의 특정 컨테이너 이미지를 바꾸고 새 파일 경로를 출력합니다. `deploy`는 task definition을 등록하고 ECS service를 갱신합니다. 안정화 대기 후에도 **내가 요청한 revision이 실제 활성화되었는지** 확인합니다. 이전 버전으로 자동 롤백되어 안정화된 경우를 성공으로 오인하지 않기 위해서입니다.

복사 가능한 전체 파이프라인은 [기존 Docker·ECS 실습](cloud-cicd-reference.html)에 있습니다. 그 프로젝트는 Node 앱이며 이 장의 Spring 프로젝트와 파일 구조가 다릅니다. 두 예제를 섞을 때 빌드 경로·컨테이너 이름·포트·헬스 경로를 맞춥니다. [Render Action](https://github.com/aws-actions/amazon-ecs-render-task-definition), [Deploy Action](https://github.com/aws-actions/amazon-ecs-deploy-task-definition).

## 17단계: Task definition에 어떤 값이 필요한가

|항목|역할|예|
|---|---|---|
|`family`|task definition 그룹 이름|team-api-prod|
|`cpu`, `memory`|태스크 자원|허용되는 Fargate 조합 선택|
|`networkMode`|네트워크 방식|Fargate는 awsvpc|
|`executionRoleArn`|이미지·로그·secret 준비 권한|실행 역할 ARN|
|`taskRoleArn`|앱 업무 권한|앱 역할 ARN|
|`containerDefinitions`|태스크 안의 컨테이너 설정|api와 선택적 sidecar|
|`portMappings`|앱 리스닝 포트|containerPort 8080|
|`environment`|일반 설정|SPRING_PROFILES_ACTIVE=prod|
|`secrets`|비밀의 참조|Secrets Manager ARN|
|`logConfiguration`|로그 수집|awslogs와 기존 로그 그룹|
|`runtimePlatform`|CPU/OS|X86_64, LINUX|

**컨테이너 설정 발췌**:

```json
{
  "name": "api",
  "image": "ECR_REPOSITORY_URI@sha256:IMAGE_DIGEST",
  "essential": true,
  "portMappings": [{"containerPort": 8080, "protocol": "tcp"}],
  "environment": [
    {"name": "SPRING_PROFILES_ACTIVE", "value": "prod"},
    {"name": "DB_URL", "value": "jdbc:postgresql://DB_HOST:5432/app"},
    {"name": "DB_USER", "value": "app"}
  ],
  "secrets": [
    {"name": "DB_PASSWORD", "valueFrom": "SECRET_ARN"}
  ]
}
```

여기서는 secret 문자열 전체가 비밀번호라고 가정합니다. JSON secret의 일부 키를 쓰려면 ECS의 key selector 형식과 플랫폼 지원 조건을 확인합니다. 새 secret 값이 저장되어도 이미 시작한 컨테이너의 환경변수가 자동 변경되지 않으므로 회전 시 재배포 전략을 정합니다.

Task definition은 실행 설계도, Task는 실행 인스턴스, Service는 원하는 개수와 교체를 관리하는 관리자입니다. Cluster 자체가 EC2 서버 한 대를 의미하는 것은 아닙니다.

## 18단계: 배포 검증에 필요한 Python 함수

다운로드의 `scripts/verify-release.py`는 AWS CLI JSON을 읽는 **로컬 검증기**입니다. AWS를 호출하거나 변경하지 않습니다.

```python
def verify(payload, expected):
    if payload.get("failures"):
        raise ValueError("ECS 조회 실패")
    services = payload.get("services", [])
    if len(services) != 1:
        raise ValueError("서비스를 하나만 조회해야 합니다")
    service = services[0]
    deployments = service.get("deployments", [])
    if len(deployments) != 1:
        raise ValueError("교체 중인 deployment가 남아 있습니다")
    deployment = deployments[0]
    if service.get("status") != "ACTIVE":
        raise ValueError("서비스가 ACTIVE 상태가 아닙니다")
    if deployment.get("status") != "PRIMARY":
        raise ValueError("PRIMARY deployment가 아닙니다")
    if service.get("taskDefinition") != expected:
        raise ValueError("서비스 revision 불일치: 롤백 여부 확인")
    if deployment.get("taskDefinition") != expected:
        raise ValueError("deployment revision 불일치")
    if deployment.get("rolloutState") != "COMPLETED":
        raise ValueError("롤링 배포가 완료되지 않았습니다")
    desired = service.get("desiredCount", 0)
    if desired < 1 or service.get("runningCount") != desired:
        raise ValueError("목표 태스크 개수에 도달하지 못했습니다")
    if service.get("pendingCount") != 0:
        raise ValueError("시작 대기 태스크가 있습니다")
```

|함수·문법|역할|왜 필요한가|
|---|---|---|
|`json.load()`|파일의 JSON을 dict로 읽음|CLI 결과 해석|
|`dict.get()`|키 조회, 기본값 지정|누락 필드에 대해 명확한 실패 처리|
|`raise ValueError()`|검증 실패를 예외로 표현|CI를 실패로 종료|
|`sys.exit(1)`|실패 종료 코드 전달|후속 승격 차단|
|`len()`|배열 원소 수 확인|교체 중 deployment 감지|

이 검증기는 **ECS rolling 배포**를 대상으로 합니다. CodeDeploy blue/green이나 task set 기반 배포에는 맞는 검증기를 별도로 작성해야 합니다. 통과 후에도 ALB를 거친 스모크 테스트와 오류율 관찰이 필요합니다. AWS control plane 상태만으로 업무 기능을 검증할 수는 없습니다.

## 19단계: Terraform으로 인프라 관리하기

Terraform의 기본 단위는 provider(서비스 연결), resource(만들 대상), data(기존 정보 조회), variable(입력), output(출력), module(재사용 묶음)입니다.

**HCL 발췌**:

```hcl
variable "environment" {
  type = string
  validation {
    condition     = contains(["dev", "stg", "prod"], var.environment)
    error_message = "dev, stg, prod 중 하나를 선택하세요."
  }
}
locals {
  name = "team-api-${var.environment}"
  tags = { Project = "team-web", Environment = var.environment }
}
resource "aws_ecr_repository" "api" {
  name                 = local.name
  image_tag_mutability = "IMMUTABLE"
  tags                 = local.tags
}
output "repository_url" {
  value = aws_ecr_repository.api.repository_url
}
```

```bash
terraform fmt -check -recursive
terraform init
terraform validate
terraform plan -out=review.tfplan
# 계획의 생성·변경·삭제 대상과 계정을 확인한 뒤 적용
terraform apply review.tfplan
```

|명령·함수|기능|주의|
|---|---|---|
|`fmt`|HCL 형식 정리|문법·정책 전체 검증은 아님|
|`validate`|구조·타입 검증|실제 AWS 권한·quota까지 보장하지 않음|
|`plan`|현재 상태와 원하는 상태의 차이 계산|검토할 변경 목록|
|`apply`|변경 실행|저장된 plan을 보호하고 최신성 확인|
|`output`|필요한 리소스 값 조회|비밀 노출 여부 확인|
|`jsonencode()`|HCL 값을 JSON으로 변환|IAM 정책·task 정의 생성|
|`templatefile()`|변수를 텍스트 템플릿에 삽입|비밀을 렌더링 결과에 남기지 않도록 주의|
|`merge()`|map 합치기|공통 태그와 환경 태그 구성|
|`for_each`|키 기반 여러 리소스 선언|안정적인 키 사용|

Terraform이 ECS service의 task revision도 관리하고 CD가 같은 값을 바꾸면 다음 apply에서 되돌릴 수 있습니다. “인프라 속성은 Terraform, 릴리스 revision은 CD”처럼 소유권을 정하고 필요한 항목에 한해 `ignore_changes` 등을 설계합니다. 모든 drift를 무시하면 실제 설정 오류도 감춰집니다. [Terraform 상세 가이드](terraform-reference.html).

## 20단계: 원격 state와 환경 분리

state는 Terraform 리소스와 실제 AWS 리소스의 대응표입니다. 민감한 값이 포함될 수 있어 일반 소스 코드처럼 공개하면 안 됩니다. `sensitive = true`는 화면 표시를 가릴 뿐 state에서 값을 제거하는 기능이 아닙니다.

```hcl
terraform {
  backend "s3" {
    bucket       = "REPLACE_WITH_EXISTING_STATE_BUCKET"
    key          = "team-web/dev/terraform.tfstate"
    region       = "ap-northeast-2"
    encrypt      = true
    use_lockfile = true
  }
}
```

state용 버킷은 별도의 bootstrap으로 먼저 만들고 접근 통제·버전 관리·암호화를 설정합니다. S3 native locking을 지원하는 Terraform 버전을 사용합니다. state 읽기/쓰기 권한과 `.tflock` 객체의 읽기/쓰기/삭제 권한을 구분합니다. [S3 backend 공식 문서](https://developer.hashicorp.com/terraform/language/backend/s3).

|분리 대상|개발·운영 구분 방식|
|---|---|
|계정|가능하면 AWS 계정을 분리하여 권한·비용 경계 설정|
|state|환경별 key와 접근 역할 분리|
|설정|환경별 tfvars, 비밀은 외부 관리|
|배포|GitHub Environment와 역할 분리|
|DB|다른 인스턴스/클러스터와 계정, 데이터 마스킹|

Terraform workspace 이름만 바꾸는 것으로 계정·권한이 자동 분리되지 않습니다. 잠금 오류를 만났을 때 실제 작업이 진행 중인지 확인하기 전에 `force-unlock`하지 않습니다. 운영 `destroy`는 평상시 배포 흐름과 분리합니다.

## 21단계: 네트워크와 연결 오류 읽는 방법

```text
인터넷 → ALB SG:443
ALB SG → 앱 SG:8080
앱 SG → DB SG:5432
앱 → ECR/로그/Secrets/S3: 필요한 외부 경로 또는 VPC endpoint
```

|요소|기능|개발자가 알아야 할 것|
|---|---|---|
|Subnet|VPC 주소 범위의 일부|AZ와 라우트 테이블 연결|
|Route table|패킷을 어디로 보낼지 결정|public/private는 이름이 아니라 경로와 연결 조건|
|Security Group|연결 허용 규칙, stateful|출발지 SG로 좁히기|
|NACL|서브넷 단위 stateless 규칙|응답 포트도 고려|
|NAT Gateway|private subnet의 외부 IPv4 통신 경로|시간·처리량 비용과 AZ 경로|
|VPC endpoint|AWS 서비스에 사설 경로 제공|서비스별 endpoint·DNS·정책 차이|
|DNS|이름을 주소로 변환|잘못된 주소·캐시·레코드 확인|
|TLS|암호화와 서버 신원 검증|인증서 도메인·만료·중간 체인|

접속 실패는 **DNS → 연결/TLS → HTTP → 앱 → DB** 순서로 좁힙니다. 응답 시간 초과는 네트워크·과부하 등 여러 원인이고, HTTP 500은 요청이 서버까지 도착했지만 내부 처리에 실패한 것입니다. 502/503/504도 ALB와 target 로그를 함께 봐야 합니다.

```bash
# 본인 서비스 도메인으로 교체
curl --connect-timeout 5 --max-time 15 -I https://api.example.com
# AWS 인증 후 대상 상태 확인
aws elbv2 describe-target-health --target-group-arn "$TARGET_GROUP_ARN"
```

보안 그룹을 `0.0.0.0/0` 전체 개방해서 문제를 덮지 말고, 실패한 연결의 출발지·목적지·포트를 확인합니다.

## 22단계: DB 마이그레이션과 호환성

코드 롤백과 DB 롤백은 다릅니다. 이전 이미지로 되돌려도 삭제된 컬럼·데이터가 돌아오지 않습니다. 운영에서는 보통 **확장 → 데이터 이관 → 전환 → 나중에 정리** 순서를 사용합니다.

예: `title`을 `name`으로 바꾸려면 바로 rename하여 구버전을 깨뜨리기보다 새 컬럼을 추가하고 양쪽 호환 기간을 설계합니다.

```sql
-- V2__add_description.sql : 기존 행을 유지하는 확장 예
ALTER TABLE todos ADD COLUMN description varchar(500);
```

1. 기존/새 앱이 모두 사용할 수 있는 스키마 변경을 적용합니다.
2. 필요하면 배치로 데이터를 이관하고 누락을 확인합니다.
3. 새 앱을 배포해 읽기/쓰기 동작을 전환합니다.
4. 롤백 가능 기간이 지난 후 구 필드를 제거합니다.

|점검|이유|
|---|---|
|DDL 잠금과 실행 시간|큰 테이블 변경이 요청을 막을 수 있음|
|인덱스 생성 방식|DB 특성과 트랜잭션 제약 확인|
|단일 migration 실행자|여러 태스크의 동시 시작과 구분|
|실패 종료 코드 검사|DB 실패 뒤 앱 배포를 막음|
|백업과 복구 연습|되돌릴 수 있는 데이터 확보|
|롤백 호환 버전|이전 코드가 새 스키마에서도 동작해야 함|

ECS one-off migration task를 쓴다면 task가 `STOPPED`가 된 것만으로 성공이 아닙니다. 컨테이너의 `exitCode == 0`, 실행 실패 사유, 적용된 DB 버전을 확인합니다. 이미 적용한 migration 파일은 수정하지 않고 후속 파일로 변경합니다. [Flyway migration 개념](https://documentation.red-gate.com/flyway/flyway-concepts/migrations).

## 23단계: 롤링 · Blue/Green · Canary와 롤백

|전략|동작|장점|준비할 것|
|---|---|---|---|
|Rolling|구버전 일부를 신버전으로 차례로 교체|추가 구성 부담이 작음|구/신버전 동시 호환, 여유 용량|
|Blue/Green|두 환경 사이에서 트래픽 전환|전환 전 검증·빠른 복귀 가능|추가 용량, 라우팅, 데이터 호환|
|Canary|일부 트래픽부터 새 버전에 전달|오류 영향을 제한|분할 라우팅, 판단 지표, 자동 중단|

ECS rolling의 `minimumHealthyPercent=100`, `maximumPercent=200`은 교체 중 기존 정상 개수를 유지하면서 최대 두 배까지 실행할 수 있도록 하는 예입니다. quota·서브넷 IP·CPU 등 실제 여유가 있어야 합니다. 작은 환경에 무조건 적합한 값은 아닙니다.

Deployment circuit breaker는 시작·상태 검사 실패를 탐지할 수 있습니다. 자동 rollback에는 이전에 완료된 deployment가 필요하며, 업무 오류나 DB 파괴적 변경까지 되돌리는 장치는 아닙니다. [ECS circuit breaker](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-circuit-breaker.html).

수동 롤백도 승인된 이전 task definition을 지정하는 **서비스 변경**입니다. 먼저 DB 호환성을 확인합니다.

```bash
# PREVIOUS_TASK_ARN은 배포 기록에 보관한 이전 정상 revision
aws ecs update-service --cluster "$CLUSTER" --service "$SERVICE" \
  --task-definition "$PREVIOUS_TASK_ARN"
aws ecs wait services-stable --cluster "$CLUSTER" --services "$SERVICE"
# 이후 정확한 revision 확인과 스모크 테스트를 다시 수행
```

## 24단계: React 정적 웹 배포

React SPA의 `dist/`는 S3에 저장하고 CloudFront로 서비스할 수 있습니다. S3를 비공개로 두고 CloudFront OAC로 접근하게 하는 구성이 일반적입니다. 웹사이트 endpoint 방식과 S3 REST origin + OAC 방식은 다르므로 섞지 않습니다.

빌드 결과는 파일명 hash가 있는 JS/CSS와 `index.html`로 구분해 캐시 정책을 다르게 둡니다. 정적 자산은 길게, 진입 HTML은 짧게 또는 재검증하게 관리합니다. 새 자산을 먼저 업로드한 다음 새 HTML을 반영해야 전환 중 파일 누락을 줄일 수 있습니다.

**전용 SPA 버킷 루트가 준비된 경우의 업로드 예**:

```bash
aws s3 sync frontend/dist/ "s3://$WEB_BUCKET/" \
  --exclude 'index.html' --cache-control 'public,max-age=31536000,immutable'
aws s3 cp frontend/dist/index.html "s3://$WEB_BUCKET/index.html" \
  --cache-control 'no-cache' --content-type 'text/html'
aws cloudfront create-invalidation --distribution-id "$DISTRIBUTION_ID" \
  --paths '/index.html' '/'
```

이 장기 캐시는 **HTML 외 파일도 내용 hash로 버전이 바뀐다는 전제**입니다. Vite `public/`처럼 고정 이름 파일은 별도 짧은 캐시 정책으로 업로드합니다. 이전 자산은 롤백·열린 탭을 고려해 일정 기간 유지하고 나중에 정리합니다. `/todos/123` 새로고침의 SPA 라우팅은 별도 설정하며 `/api` 오류를 index.html로 덮지 않습니다.

프런트 롤백에는 이전 HTML과 연결된 정적 자산 세트가 필요합니다. API 응답 변경도 이미 열린 구버전 브라우저와 호환되어야 합니다. [CloudFront OAC](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html).

## 25단계: 로그 · 메트릭 · 트레이스

|종류|대답하는 질문|예|
|---|---|---|
|로그|어떤 사건이 일어났나?|요청 실패와 오류 원인|
|메트릭|얼마나 자주·많이 발생하나?|초당 요청, p95 지연, 오류율|
|트레이스|한 요청이 어디를 거쳤나?|ALB → API → DB/외부 API 시간|

로그에는 시각, level, 서비스, 환경, release, request/trace ID, 작업명, 결과를 담습니다. 비밀번호·토큰·전체 개인정보 본문은 기록하지 않습니다. 사용자 입력을 그대로 문자열에 합쳐 로그 구조를 깨뜨리지 않게 합니다.

```java
// SLF4J Logger가 선언된 서비스 내부의 설명용 발췌
long started = System.nanoTime();
try {
    return repository.findById(id)
        .orElseThrow(() -> new TodoNotFoundException(id));
} finally {
    long elapsedMs = (System.nanoTime() - started) / 1_000_000;
    log.info("operation=todo_lookup elapsed_ms={}", elapsedMs);
}
```

이 코드는 수행 시간을 로그에 남길 뿐 분산 트레이싱 전체를 구현하지 않습니다. request ID 전파·MDC 정리·비동기 전파는 필터/계측 라이브러리로 일관되게 구성합니다. metric label에 사용자 ID·request ID를 넣으면 cardinality가 폭증할 수 있습니다.

처음 대시보드는 요청량, 오류율, p95/p99 응답 시간, 정상 태스크 수, CPU/메모리, DB 연결 수·지연으로 시작합니다. 평균만 보면 일부 사용자의 긴 대기가 숨겨집니다.

## 26단계: 알람 · SLI · SLO 설계

SLI는 측정 지표, SLO는 목표, SLA는 계약상 약속입니다. 예를 들어 “30일 동안 유효 요청의 99.9%가 성공해야 한다”가 SLO이고, 성공률 계산이 SLI입니다.

```text
요청 기반 성공률 = 성공으로 정의한 요청 수 / 전체 유효 요청 수 × 100
오류 예산 = 전체 유효 요청 수 × (1 - 목표 성공률)
예: 1,000,000건 × 0.001 = 1,000건
```

무엇을 성공/실패로 볼지, 4xx를 포함할지, 측정 위치는 어디인지 먼저 정의합니다. 시간 기반 가용성과 요청 기반 성공률은 다르므로 “99.9% = 장애 몇 분”을 무조건 변환하면 안 됩니다.

|알람|처음 검토할 기준|대응|
|---|---|---|
|5xx 증가|최소 요청량을 만족하면서 비율 상승|최근 배포·의존성 오류 확인|
|p95 지연 증가|일정 기간 목표 초과|DB·외부 API·큐 대기 확인|
|정상 target 감소|기대 개수 미달 지속|task 종료·헬스 실패 조사|
|DB 연결 포화|최대 연결 대비 사용량 증가|누수·풀 설정·트래픽 확인|
|큐 체류 시간 증가|업무 처리 목표 초과|worker 실패·처리량 조사|
|예산 임계치|예상 비용 초과 경향|사용량·유휴 리소스 검토|

알람에는 담당자, 심각도, 런북 링크, 환경, 관련 대시보드를 연결합니다. 일시적 1회 실패와 지속 장애를 구분하고, 데이터 없음 처리도 정합니다. 고정 CPU 임계치만으로 사용자 영향을 판단하지 않습니다.

## 27단계: 장애 대응 순서와 조회 명령

**목표는 우선 사용자 영향을 줄이고, 그다음 원인을 설명하는 것입니다.** 담당자 지정 → 범위 확인 → 최근 변경 확인 → 완화 → 정상 검증 → 원인 분석 순서로 진행합니다.

```bash
# 현재 계정 확인
aws sts get-caller-identity
# 서비스 상태와 최근 event
aws ecs describe-services --cluster "$CLUSTER" --services "$SERVICE"
# 최근 중단된 task ARN
aws ecs list-tasks --cluster "$CLUSTER" --service-name "$SERVICE" \
  --desired-status STOPPED
# 조회한 ARN을 넣어 중단 사유와 컨테이너 종료 코드 확인
aws ecs describe-tasks --cluster "$CLUSTER" --tasks "$TASK_ARN"
# 앱 로그: 로그 그룹은 실제 값으로 설정
aws logs tail "$LOG_GROUP" --since 30m --format short
```

|증상|우선 볼 것|가능한 조치|
|---|---|---|
|새 task가 시작 안 됨|image pull, execution role, 네트워크, secret|이미지·권한·접근 경로 수정|
|시작 직후 종료|exitCode, 메모리, 설정 누락, DB 오류|설정 복구 또는 이전 버전|
|ALB 503|healthy target, 포트·경로·SG|헬스 경로·등록 상태 수정|
|지연만 증가|DB 쿼리, 연결 풀, 외부 timeout|병목 완화·부하 제한|
|특정 API만 500|release별 로그·입력 패턴|기능 비활성화·호환 롤백|
|비용 급증|서비스·리전·태그별 비용|불필요 작업 중단·설정 수정|

변경을 여러 개 동시에 하면 원인을 찾기 어렵습니다. 시간과 조치를 기록하고, 실패한 버전을 덮어버리기 전에 로그·배포 정보·메트릭을 보존합니다. 긴급 조치 후에는 임시 설정을 IaC와 문서에 반영하거나 원상복구합니다.

사후 분석에는 원인뿐 아니라 “왜 감지/차단되지 않았나”, “어떤 조건에서 재발하나”, “담당자와 기한이 있는 개선 작업”을 남깁니다.

## 28단계: 보안과 비밀값 운영

|영역|개발자가 수행할 일|확인 증거|
|---|---|---|
|인증|사용자·서비스 신원 확인|토큰 만료·서명·issuer 검증 테스트|
|인가|누가 어떤 데이터에 접근 가능한지 검사|다른 사용자의 리소스 접근 거부|
|IAM|필요한 API·리소스만 허용|환경별 역할·정책 검토|
|비밀|Secret Manager/Parameter Store 등 사용|회전·재배포 절차|
|데이터|전송·저장 암호화, 접근 기록|TLS·KMS·감사 설정|
|공급망|의존성·이미지·Action 업데이트|검사 결과와 조치 PR|
|감사|누가 무엇을 변경했는지 기록|CloudTrail·배포 이력|

AWS 키를 숨긴 변수에 저장하는 것과 키 자체를 쓰지 않는 OIDC는 다릅니다. CI 로그 마스킹만 믿고 `env` 전체 출력, 토큰 출력, 디버그 dump를 남기지 않습니다. Terraform plan/state와 테스트 리포트에도 비밀이 섞일 수 있습니다.

CORS는 브라우저의 교차 출처 접근 정책이며 인증·인가를 대신하지 않습니다. 클라이언트가 전달한 사용자 ID만 믿고 DB를 조회하지 말고 서버의 인증 정보를 기준으로 소유권을 검증합니다.

## 29단계: 백업 · 복원 · RTO · RPO

RTO는 복구까지 허용하는 시간, RPO는 허용 가능한 데이터 손실 시점 범위입니다. 예를 들어 RTO 1시간, RPO 5분이면 장애 후 1시간 이내 서비스 복구와 최대 5분 수준의 데이터 손실 목표를 함께 검증해야 합니다.

|준비|확인할 내용|
|---|---|
|DB 자동 백업/PITR|보존 기간, 복원 가능한 최신 시점|
|S3 버전 관리|삭제·덮어쓰기 복구와 보관 비용|
|인프라 재생성|state·코드·비밀·이미지 접근 가능 여부|
|이미지/정적 파일 보관|이전 정상 릴리스 사용 가능 여부|
|복구 접근권한|평소와 사고 시 역할·승인 절차|
|복원 훈련|새 DB 복원 → 데이터 검사 → 앱 연결 → 요청 검증|

Multi-AZ는 가용성 향상을 돕지만 실수로 삭제한 데이터를 자동 되살리는 백업과 같은 기능이 아닙니다. RDS 시점 복원은 보통 새 DB 인스턴스로 복원하므로 연결 endpoint 전환과 데이터 일관성 확인까지 포함합니다. 실제 복원 시간을 재지 않으면 RTO 달성을 주장할 수 없습니다. [RDS 시점 복원](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_PIT.html).

## 30단계: 성능 · 확장 · 비용 관리

성능 개선은 측정 → 병목 가설 → 작은 변경 → 같은 조건 비교 순서로 합니다. CPU를 늘려도 느린 DB 쿼리나 외부 API timeout은 해결되지 않을 수 있습니다.

|항목|점검·사용법|주의|
|---|---|---|
|수평 확장|ECS desired count/auto scaling|DB 연결 수도 함께 증가|
|연결 풀|태스크 수 × 인스턴스별 최대 연결 계산|DB 연결 한도와 여유 확보|
|쿼리|실행 계획, 인덱스, N+1 확인|쓰기 비용·저장 공간도 증가|
|캐시|반복 조회, TTL·무효화 정책|오래된 값 허용 범위|
|비동기 큐|즉시 응답 불필요한 작업 분리|중복·순서·재시도·DLQ|
|재시도|일시 오류에 제한된 횟수+backoff+jitter|비멱등 요청의 중복 생성|
|timeout|연결·응답·전체 요청 시간 제한|무한 대기와 자원 고갈 방지|

비용은 Fargate/EC2만 보지 않습니다. RDS, ALB, NAT, 로그 수집·보관, 데이터 전송, 공인 IPv4, ECR 이미지도 확인합니다. Budget 알림은 기본적으로 지출을 강제로 차단하는 장치가 아닙니다. 태그와 비용 대시보드로 소유자·환경을 연결하고, 개발 환경의 종료 정책과 로그 보존 기간을 정합니다.

예약·약정형 할인은 사용량을 먼저 파악한 뒤 검토합니다. 실습 종료 때 데이터 보존 여부를 결정하고 리소스 목록으로 정리 결과를 확인합니다. [AWS Well-Architected](https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html).

## 31단계: 자주 쓰는 명령 · 함수 빠른 사전

|코드·명령|기능|언제 사용|
|---|---|---|
|`git diff` / `git status`|변경 내용·작업 상태|커밋·배포 전에 확인|
|`./mvnw verify`|Java 검증 lifecycle|로컬·CI 품질 확인|
|`npm ci`|lockfile 기반 의존성 설치|재현 가능한 빌드|
|`docker compose logs`|로컬 컨테이너 로그|DB 시작 실패 조사|
|`docker build`|이미지 생성|배포 단위 패키징|
|`docker inspect`|이미지·컨테이너 상세|환경·네트워크·종료 상태 확인|
|`aws sts get-caller-identity`|계정·역할 확인|AWS 변경 전|
|`aws ecr get-login-password`|Docker registry 인증 토큰|ECR 로그인, 비밀번호 출력하지 않기|
|`aws ecr describe-images`|이미지 digest·태그 조회|배포 대상 확정|
|`aws ecs register-task-definition`|새 실행 설정 revision 생성|서비스 변경 전|
|`aws ecs update-service`|서비스 설정·revision 변경|배포·롤백|
|`aws ecs wait services-stable`|안정화 대기|이후 정확한 revision도 검사|
|`aws logs tail`|최근 로그 조회|장애·스모크 실패 분석|
|`curl --fail-with-body`|HTTP 오류를 실패 종료로 처리|CI 스모크 테스트|
|`terraform plan`|인프라 변경 예측|승인·검토 전|
|`terraform state list`|관리 중인 리소스 주소 조회|state 조사|

**Bash 함수 발췌**. 재사용할 명령을 이름으로 묶습니다. AWS 명령은 함수여서 달라지는 것이 아니라 같은 CLI를 실행합니다.

```bash
require_var() {
  local key="$1"
  if [ -z "${!key:-}" ]; then
    printf '필수 환경변수 누락: %s\n' "$key" >&2
    return 1
  fi
}
# Bash에서 실행. zsh의 간접 변수 문법과는 다름.
require_var CLUSTER || exit 1
require_var SERVICE || exit 1
aws ecs describe-services --cluster "$CLUSTER" --services "$SERVICE"
```

`"$VAR"`처럼 인용하면 공백·패턴 확장 문제를 줄입니다. `set -euo pipefail`은 유용하지만 모든 논리 오류를 막지는 않으며, if/조건문/파이프의 동작을 이해하고 명시적 성공 조건을 확인해야 합니다.

## 32단계: 매일 · 매주 · 릴리스마다 하는 일

|주기|업무|완료 증거|
|---|---|---|
|매일|실패한 CI·미처리 알람·핵심 지표 확인|원인과 담당자 연결|
|기능 개발마다|권한·검증·테스트·관측 항목 추가|PR과 검증 결과|
|릴리스 전|산출물·설정·DB 호환·복구 계획 확인|릴리스 체크리스트|
|릴리스 직후|revision·스모크·오류율·지연 확인|배포 기록과 대시보드|
|매주|취약점·비용·느린 쿼리·반복 장애 검토|우선순위가 있는 개선 작업|
|정기적으로|복원 훈련·권한 재검토·인증서·quota 확인|훈련 결과·권한 변경 이력|

릴리스 기록 양식:

```text
환경 / 서비스:
커밋 SHA / 이미지 digest / task definition ARN:
배포 시각 / 실행 링크 / 담당자:
변경 내용 / 사용자 영향:
DB migration / 설정 변경:
테스트 및 스모크 결과:
이전 정상 revision / 롤백 호환 여부:
관찰 지표 / 후속 조치:
```

좋은 운영 문서는 “명령어 모음”에서 끝나지 않고 실행 조건, 예상 결과, 실패했을 때 다음 행동을 포함합니다.

## 33단계: 혼자 완성해 보는 학습 과제

|단계|직접 할 일|통과 기준|
|---|---|---|
|1. 로컬|Spring·React·PostgreSQL 실행|할 일 생성→조회, 재시작 후 데이터 유지|
|2. 검증|정상·잘못된 입력·권한 테스트|오류를 의도적으로 넣으면 CI 실패|
|3. 이미지|Docker로 같은 앱 실행|IDE 없이 API 요청 성공|
|4. AWS 개발|OIDC·ECR·ECS·로그 연결|장기 키 없이 개발 배포|
|5. 배포 검증|잘못된 이미지·헬스 실패 주입|실패가 성공으로 표시되지 않음|
|6. 운영 연습|알람·롤백·복원 훈련|기록한 목표 내 복구·데이터 검증|
|7. 개선|권한·비용·속도 개선 1개씩|전후 수치와 변경 이유 설명|

면접·포트폴리오에서는 서비스 이름 나열보다 “왜 이 구조를 골랐고 어떤 실패를 재현했으며 어떻게 개선했나”를 설명합니다. 운영 계정 대신 개발 환경에서 장애를 주입합니다. 실제 사용자에게 영향을 주는 테스트는 별도 승인·범위·중단 조건이 필요합니다.

스스로 답해 보기: CI가 통과했는데 배포가 실패할 수 있는 이유는? 이전 이미지로 되돌렸는데 DB 오류가 계속되는 이유는? ECS가 stable인데 새 코드가 아닌 이유는? React 환경변수에 비밀을 넣으면 안 되는 이유는? 각각 관련 장의 성공 조건을 찾아 설명해 보세요.

## 예제 파일 · 검증 범위 · 공식 문서

[설정 템플릿과 배포 검증기 ZIP 다운로드](sample-files/devops-handbook-templates.zip). `README.md`에 적용 순서를 적었습니다. `.example` 파일은 내용을 검토한 후 실제 프로젝트 경로에 복사하며, 다운로드 자체로 CI나 AWS 배포가 실행되지는 않습니다.

포함 파일: Compose, `.env.example`, Git ignore, CI workflow 템플릿, Dockerfile, Docker ignore, VS Code 실행 설정 예시, OIDC 신뢰 정책, CD step 발췌, Python 배포 검증기와 단위 테스트.

**검증 범위**: 문서의 링크·레이아웃·검색과 로컬 검증기의 성공/실패 사례를 확인했습니다. 완성된 Spring/React 프로젝트 전체 빌드, GitHub hosted CI 실행, 실제 AWS 리소스 생성·배포·복원은 이 문서 작성에서 수행하지 않았습니다. 환경값·권한·quota·버전 호환성을 자신의 개발 환경에서 확인해야 합니다.

본문은 개념 설명과 학습용 구성 예시이며 공식 문서는 세부 조건 확인에 사용했습니다. 확인 기준일: **2026-10-05**. GitHub Actions/OIDC, AWS 플랫폼 지원 조건과 버전은 바뀔 수 있으므로 적용 시 링크의 현행 조건을 확인합니다.

- [GitHub Actions 문법](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)
- [AWS 인증 Action](https://github.com/aws-actions/configure-aws-credentials)
- [ECS 배포 Action](https://github.com/aws-actions/amazon-ecs-deploy-task-definition)
- [Spring Actuator](https://docs.spring.io/spring-boot/reference/actuator/endpoints.html)
- [Terraform S3 backend](https://developer.hashicorp.com/terraform/language/backend/s3)
- [AWS Well-Architected](https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html)
