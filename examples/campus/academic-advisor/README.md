# 학사 도우미 — 독립 시제품

상위 수강신청 프로젝트와 별도 실행하는 React + Spring 앱입니다. 상위 pom.xml의 모듈이 아니며, 수강신청 DB·로그인·시간표·신청 API를 사용하지 않습니다. 상위 Docker 배포에서도 제외합니다.

## 실행

이 폴더에서 실행하세요. Node.js 22.12 이상, Java 17 이상이 필요합니다.

```sh
npm --prefix frontend ci
npm --prefix frontend run build
./mvnw spring-boot:run
```

주소: http://localhost:8081 (수강신청 사이트 8080과 별도).
개발 중에는 서버를 실행한 상태에서 `npm --prefix frontend run dev`로 5174 화면을 사용합니다.

## 자료와 해석

- 자료 파일: `src/main/resources/advising/kornu-2024.json`
- 2024학번·트랙 연결과 졸업 요건은 사용자 설명에 근거합니다. 첨부 사진에는 제목이 잘려 있으므로 공식 원문 확인 완료로 표시하지 않습니다.
- 사진 11.24.12 → 인공지능빅데이터, 11.24.28 → 정보통신보안, 11.24.37 → 스마트미디어로 과목 구성을 대조했습니다.
- **졸업하려는 트랙의 파란색 과목 중 21학점을 선택 이수**합니다. 파란색 전체가 필수라는 뜻이 아닙니다.
- `category`는 표의 이수구분, `blue`는 파란색 표시입니다. 전공선택으로 인쇄된 파란색 과목도 선택 후보에 포함하되 이수구분을 바꾸지 않습니다.
- 전공필수 칸 합계 27학점과 사용자 요약의 최소 12학점 차이는 그대로 안내합니다. 졸업 충족 자동 판정은 하지 않습니다.
- 정보통신보안의 이름 없는 3학점 행은 과목으로 만들지 않았습니다. 2학기 이름 있는 과목 합계 28과목·85학점과 표 하단 27과목·82학점 차이도 기록했습니다.
- 누적 이수내역, 개설 여부, 선수과목·중복 인정 규칙이 없어 개인 졸업 잔여 학점이나 신청 가능한 수업을 계산하지 않습니다.
- 외부 생성형 AI는 사용하지 않습니다. 등록된 자료를 조건으로 조회하는 규칙형 챗봇입니다.

## 구조

- `frontend/src/features/advisor/Advisor.jsx`: 학적·트랙 선택, 질문, 대화 표시
- `src/main/java/kr/ac/advisor/service/CurriculumService.java`: 조건별 자료 조회
- `controller/AdvisorController.java`: 별도 브라우저 세션의 프로필·질문 API
- `config/SecurityConfig.java`: CSRF 보호 유지

로그인 없는 로컬 시제품으로 127.0.0.1에만 바인딩합니다. 프로필은 임시 서버 세션에, 대화는 브라우저 메모리에 저장합니다. 쿠키 이름도 ADVISORSESSION으로 분리했습니다. 공개 배포 전 인증·사용량 제한 등이 필요합니다.

## 검증

```sh
npm --prefix frontend test
./mvnw test
```
