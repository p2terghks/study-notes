# 기능별 폴더 분류

수강신청 앱과 독립 학사 도우미를 분리한 상태로 파일 위치를 정리했습니다. URL·DB 구조·업무 규칙은 변경하지 않았습니다.

## 수강신청 React

```text
frontend/src/
├── main.jsx / App.jsx / styles.css  # 실행·화면 전환·스타일 진입점
├── features/
│   ├── auth/          # 로그인·회원가입 + auth.css
│   ├── dashboard/     # 전체 화면·메뉴 + layout.css
│   ├── courses/       # 강의 목록·필터 + courses.css
│   ├── timetable/     # 시간표 + timetable.css·print.css
│   └── registration/  # 서버 상태·신청·취소·장바구니 요청 Hook
├── shared/
│   ├── api/           # 공통 HTTP·CSRF 처리
│   ├── ui/            # Icon·Modal + feedback.css
│   └── styles/        # common.css·responsive.css
└── tests/             # 화면 통합 테스트·테스트 초기화
```

한 기능의 JSX와 CSS를 같은 폴더에 보관합니다. styles.css에서 기존 순서로 CSS를 불러오므로 스타일 우선순위는 유지됩니다. 테스트는 여러 기능을 함께 검증하므로 tests에 모았습니다.

## 수강신청 Spring

`src/main/java/kr/ac/campus` 기준입니다.

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

수강신청 트랜잭션은 기존 CourseService에 유지합니다. enrollment/cart로 파일을 분류했다고 트랜잭션을 여러 서비스로 나누지는 않았습니다. api/ApiController는 회원가입·강의·장바구니를 연결하는 기존 공통 진입점입니다.

## 별도 학사 챗봇

```text
academic-advisor/
├── frontend/src/
│   ├── features/advisor/   # Advisor.jsx·advisor.css
│   ├── shared/api/         # HTTP·CSRF
│   └── tests/              # 화면 테스트
├── src/main/java/kr/ac/advisor/
│   ├── AdvisorApplication.java
│   ├── controller/
│   ├── service/
│   └── config/
└── src/main/resources/advising/  # 교육과정 자료
```

수강신청 서버의 advisor 패키지는 로컬 Python 상담 엔진과 연결되어 있습니다. 현재 수강신청 화면에는 상담 UI가 없으며 별도 챗봇 프로젝트는 기존 Java 구현을 유지합니다.

Python 원본: `src/main/resources/python/advisor.py`, 연결 코드: `advisor/service/PythonAdvisor.java`, Python 테스트: `src/test/python/test_advisor.py`.

## 그대로 유지한 위치

- docs/: 설명·요약 문서
- deploy/: AWS 배포 파일
- 각 프로젝트의 src/main/resources/static/: Vite 빌드 결과
- src/main/resources/db/migration/: 기존 Flyway SQL
- 루트의 pom.xml·Dockerfile·Maven Wrapper: 실행·빌드 진입점

생성물인 target/과 node_modules/는 직접 분류하지 않습니다. 프론트 원본은 frontend/src, 서버 원본은 src/main/java를 수정하세요.
