# CAMPUS · Spring 수강신청

Spring Boot 3.5.16 / Java 17+ / Spring Security / Spring Data JPA / H2로 만든 실행 가능한 수강신청 사이트입니다. React + Vite 프론트엔드를 빌드하여 Spring에서 정적 파일과 API를 함께 제공합니다.

## 코드 읽기

기능별 위치는 [폴더 분류 안내](docs/FOLDER_STRUCTURE.md)를 참고하세요.

빠르게 파일 역할을 찾으려면 [코드 읽기 안내](docs/CODE_GUIDE.md), 코드 예시와 순서도로 학습하려면 [React·Spring 상세 가이드](docs/FRONTEND_SPRING_GUIDE.md)를 참고하세요. 프론트 원본은 `frontend/src`에 있고 React 컴포넌트와 Hook으로 구현되어 있습니다. 주요 처리 이유는 소스의 한국어 주석에도 정리했습니다.

## AWS 배포

ECS Fargate + RDS PostgreSQL 배포 파일과 절차는 [deploy/README.md](deploy/README.md)에 있습니다. 운영 프로필은 PostgreSQL·Flyway·DB 공유 세션·HTTPS 쿠키를 사용하고 체험 데이터를 생성하지 않습니다. CloudFormation은 ALB, Fargate, RDS, Secrets Manager, ECR, 네트워크를 구성합니다. AWS에 실제 배포한 상태는 아닙니다.

## 실행

```sh
npm --prefix frontend ci
npm --prefix frontend run build
./mvnw spring-boot:run
```

Node.js 22.12 이상과 Python 3.10 이상이 필요합니다. Windows에서는 npm 명령 실행 후 `mvnw.cmd spring-boot:run`을 사용합니다. 첫 실행에는 Maven과 의존성을 받기 위한 인터넷 연결이 필요합니다.

브라우저에서 http://localhost:8080 접속 후 **체험 계정으로 둘러보기**를 누르세요.

- 학번: `20260001`
- 비밀번호: `campus1234`
- 샘플 강의 12개, 신청 강의 3개, 장바구니 2개가 최초 실행 시 생성됩니다.
- 회원가입으로 별도 계정을 만들면 빈 시간표로 시작합니다. 학번은 8~12자리, 비밀번호는 8~64자입니다.
- 데이터는 `data/campus.mv.db`에 저장되어 재시작 후 유지됩니다.
- 다른 포트: `PORT=8081 ./mvnw spring-boot:run`

### 프론트 개발 중 자동 새로고침

Spring 서버를 8080에서 실행하고 다른 터미널에서 `npm --prefix frontend run dev`를 실행합니다. Vite가 안내하는 주소(기본 5173)로 접속하면 `/api`가 Spring으로 프록시되어 세션·CSRF가 유지됩니다.

프론트 수정 후 `npm --prefix frontend run build`로 생성물을 갱신한 다음 JAR를 빌드하세요. `src/main/resources/static`은 빌드 결과이므로 직접 편집하지 않습니다. Docker는 Node 빌드 단계에서 자동으로 React를 빌드합니다. 프론트 테스트는 `npm --prefix frontend test`입니다.

## 기능

- 회원가입, BCrypt 비밀번호 해싱, 세션 로그인/로그아웃, CSRF 보호
- 사용자별 시간표, 신청 내역 및 장바구니
- 수강신청 즉시 시간표·학점·잔여 정원 갱신
- 강의 행에 마우스를 올리거나 키보드 초점을 맞추면 점선으로 시간표 미리보기
- 시간 충돌 미리보기 및 서버 측 중복·정원·시간 충돌·18학점 제한 검증
- 신청 취소 확인 및 정원 반환
- 장바구니 담기/삭제, 신청 성공 시 장바구니에서 자동 삭제
- 강의명·학수번호·교수 검색, 학과·이수구분·신청 가능 여부 필터
- 20초 간격 신청 현황 갱신, 인쇄/PDF 저장, 모바일 레이아웃

## 동시 신청 처리

`CourseService`의 신청·취소·장바구니 변경을 트랜잭션으로 처리합니다.

1. 사용자 행을 `SELECT ... FOR UPDATE`로 잠급니다. 같은 사용자의 서로 다른 강의 신청도 직렬화하여 시간 충돌과 학점 초과를 방지합니다.
2. 강의 행을 잠급니다. 서로 다른 사용자가 마지막 자리에 신청할 때 정원을 초과할 수 없습니다.
3. 중복, 정원, 학점, 시간 충돌을 검사한 뒤 신청 레코드와 수강 인원을 같은 트랜잭션에서 변경합니다.
4. 실패 시 변경 전체를 롤백합니다. 잠금 순서는 항상 사용자 → 강의입니다.
5. `(student_id, course_id)` 기본 키와 인원 체크 제약으로 DB에서도 일관성을 보호합니다.

선착순은 DB 잠금 획득 순서로 처리하며 네트워크 도착 시각 기준의 엄격한 순번 큐는 제공하지 않습니다. 기본 H2 파일 DB는 로컬 단일 서버 실행용입니다. 운영 프로필에서는 PostgreSQL 행 잠금과 DB 공유 세션을 사용합니다. 실제 목표 트래픽에 대한 부하 테스트는 별도로 필요합니다.

## 검증

```sh
./mvnw test
./mvnw package
java -jar target/campus-1.0.0.jar
```

`CampusIntegrationTest`는 독립된 메모리 DB에서 아래 통합 시나리오를 검증합니다.

- 장바구니 중복 방지 → 신청 → 취소 및 인원 일관성
- 시간 충돌 롤백과 바로 이어지는 수업 허용
- 최대 학점 제한
- 20명 동시 신청 시 3자리만 등록
- 한 학생의 동시 중복 신청
- 한 학생의 서로 다른 시간 중복 강의 동시 신청
- 한 학생의 동시 신청에 따른 학점 초과 방지
- 동시 취소/재신청의 인원 일관성
- 로그인 성공·실패, 인증·CSRF, 사용자별 데이터 격리
- 회원가입 입력 검증·중복 학번·비밀번호 해싱

## API

| 요청 | 용도 |
| --- | --- |
| `GET /api/csrf` | CSRF 토큰 및 헤더명 |
| `POST /api/register` | JSON `studentNo`, `name`, `password` |
| `POST /api/login` | form `username`, `password` |
| `POST /api/logout` | 로그아웃 |
| `GET /api/state` | 로그인 사용자, 강의, 신청/장바구니 ID |
| `POST /api/enrollments/{id}` | 수강신청 |
| `DELETE /api/enrollments/{id}` | 신청 취소 |
| `POST /api/cart/{id}` | 장바구니 추가 |
| `DELETE /api/cart/{id}` | 장바구니 삭제 |

변경 요청에는 `/api/csrf`가 반환한 헤더명과 토큰, 세션 쿠키가 필요합니다. 로그인 후 CSRF 토큰을 다시 발급받습니다. 신청 불가 상태는 `409`, 존재하지 않는 강의는 `404`, 인증되지 않은 요청은 `401`입니다.

## 구성 및 운영 범위

- `src/main/java/kr/ac/campus`: `auth`, `student`, `course`, `enrollment`, `cart`, `advisor` 기능별 패키지와 공통 설정. [구조 설명](docs/CODE_GUIDE.md#패키지-구조) 참고.
- 업무 DB 접근은 Spring Data JPA입니다. 운영 로그인 세션 저장은 Spring Session JDBC를 유지합니다.
- `frontend/src`: React 컴포넌트·Hook·CSS 원본
- `src/main/resources/static`: Vite가 생성한 배포용 HTML·JS·CSS
- `src/main/resources/schema.sql`: DB 테이블·제약
- `src/test/java/kr/ac/campus`: 통합·동시성 테스트
- `DEMO_ENABLED=false`: 최초 샘플 계정/강의 생성 비활성화. 이미 저장된 데이터는 유지합니다.

현재 학기와 수강 기간 표시는 샘플 고정값입니다. 실제 대학 학사 시스템 연동, 관리자 강의 관리, 학적 검증, 신청 기간 제어 및 대규모 대기열은 포함되어 있지 않습니다. 공개 운영 시 실제 인증 체계, HTTPS 및 운영용 DB를 연결해야 합니다.

참고: [Spring Boot 공식 문서](https://docs.spring.io/spring-boot/3.5/reference/index.html).

## 프론트·백엔드 코드 요약본

- [프론트엔드: 폴더·컴포넌트·함수·CSS·챗봇](docs/REACT_SUMMARY.md)
- [백엔드: 폴더·API·서비스·JPA·동시 신청·챗봇](docs/BACKEND_SUMMARY.md)

기존 요약본과 같은 코드 예시와 해설 형식으로 정리했습니다.

## Python 챗봇

질문 분석, 시간표 안내, 수업 추천, 졸업요건 답변은 `src/main/resources/python/advisor.py`에서 처리합니다. Python 표준 라이브러리만 사용하므로 pip 설치나 AI API 키가 필요하지 않습니다. 로그인·학적 저장·DB 조회는 Spring이 담당하고 인증된 사용자 데이터만 로컬 Python 프로세스로 전달합니다. 기존 `/api/advisor/chat` 주소와 응답 구조를 유지합니다. 현재 수강신청 React에는 상담 UI가 없으며, 별도 `academic-advisor` 화면은 기존 Java 서버를 사용합니다.

```sh
python3 --version
./mvnw spring-boot:run
```

Python 실행 파일이 다른 위치에 있으면 `APP_ADVISOR_PYTHON_EXECUTABLE=/absolute/path/to/python3` 환경 변수를 지정하세요. Windows에서는 설치된 환경에 따라 `APP_ADVISOR_PYTHON_EXECUTABLE=python`을 사용하세요. Docker 실행 이미지에도 Python을 포함합니다. 엔진 실행 실패나 10초 초과 시 상담 API는 503을 반환합니다.

Python 검증: `python3 -m unittest discover -s src/test/python`
