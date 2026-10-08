# React 코드 설명 요약본

프론트엔드 설명입니다. 서버 코드는 [백엔드 Spring·JPA·Python 요약본](BACKEND_SUMMARY.md)을 참고하세요.

수강2의 실제 React 코드를 기준으로 정리했습니다. 짧게 읽을 수 있도록 일부 코드는 핵심만 발췌하거나 간추렸습니다. 수강신청 프론트 원본은 `frontend/src`, 별도 학사 챗봇은 `academic-advisor/frontend/src`이며 서로 연결하지 않았습니다.

### 2026-10-08 챗봇 변경 반영

이번 Python 전환에서 `frontend/src`와 `academic-advisor/frontend/src`의 React 코드는 수정하지 않았습니다. 수강신청 서버의 상담 처리는 Java → 로컬 Python 호출로 바뀌었지만, 현재 수강신청 React 화면에는 상담 API 호출 UI가 없습니다. 별도 챗봇 화면의 `Advisor.send()`는 별도 Spring 서버의 `CurriculumService.answer()`를 계속 호출하므로 Python 엔진에 연결된 화면으로 해석하면 안 됩니다.

```text
수강신청 화면 → 기존 수강신청 Spring API
수강신청 서버의 상담 API → AdvisorService → PythonAdvisor → advisor.py
별도 챗봇 화면 → 별도 AdvisorController → Java CurriculumService
```

상담 API 주소·응답 형식은 유지했으며 Python 전환을 위한 신규 JSX·CSS·프론트 의존성은 없습니다. Python 상담 엔진의 함수와 실행 설정은 백엔드 요약본 11절에 정리했습니다.

## 1. 파일 구조

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

`src/main/resources/static`은 React 빌드 결과입니다. 화면 수정은 `frontend/src`에서 합니다.

## 2. React 시작 — main.jsx

```jsx
import { createRoot } from 'react-dom/client';
import App from './App';
import './styles.css';
createRoot(document.getElementById('root')).render(<App />);
```

HTML의 `<div id="root">` 안에 `App` 컴포넌트를 표시합니다. `<App />`처럼 JavaScript 안에 쓰는 화면 문법을 **JSX**라고 합니다. 컴포넌트는 화면의 한 부분을 만드는 함수입니다.

## 3. 로그인 화면 전환 — App.jsx

핵심 조건부 렌더링을 간추린 코드입니다.

```jsx
const campus = useCampus();
return campus.state
  ? <Dashboard {...campus} />
  : <AuthPage login={campus.login} demoEnabled={campus.demoEnabled} />;
```

`campus.state`에 서버의 사용자 정보가 있으면 메인 화면, 없으면 로그인 화면을 표시합니다. 실제 코드에는 로딩 화면과 오류·알림 처리도 있습니다. `{...campus}`는 객체의 각 값을 자식 컴포넌트에 **props**로 전달합니다. `login={campus.login}`처럼 함수도 전달할 수 있습니다.

## 4. 화면 상태 — useState

Dashboard에서 사용하는 상태 선언을 읽기 쉽게 분리한 예시입니다.

```jsx
const [tab, setTab] = useState('all');
const [previewId, setPreviewId] = useState(null);

function changeTab(value) {
  setTab(value);
  setPreviewId(null);
}
```

`tab`은 현재 선택한 탭이고 `setTab()`은 그 값을 바꿉니다. 상태가 바뀌면 React가 다시 렌더링합니다. `previewId`는 미리 볼 강의 ID입니다. 이 값만 바꿔서는 서버에 수강신청되지 않습니다.

```jsx
<button onClick={() => changeTab('cart')}>장바구니</button>
```

`onClick`은 클릭할 때 실행할 함수를 받습니다. 여기서는 장바구니 탭으로 전환합니다.

## 5. 검색 입력과 객체 갱신

검색 연결을 간추린 예시입니다.

```jsx
<input
  value={filters.search}
  onChange={e => updateFilter('search', e.target.value)}
/>
```

입력값을 React 상태로 관리하는 방식입니다. `e.target.value`는 사용자가 입력한 현재 문자열입니다.

실제 갱신 함수는 다음과 같습니다.

```jsx
function updateFilter(key, value) {
  setFilters((f) => ({ ...f, [key]: value }));
  setPreviewId(null);
}
```

`...f`는 기존 필터를 복사하고 `[key]: value`는 변경한 조건만 덮어씁니다. 기존 상태 객체를 직접 수정하지 않습니다.

## 6. 강의 목록과 미리보기 — CourseRows.jsx

목록 렌더링의 핵심을 간추린 예시입니다.

```jsx
{courses.map(c => (
  <tr
    key={c.id}
    tabIndex={0}
    onMouseEnter={() => onPreview(c.id)}
    onFocus={() => onPreview(c.id)}
  >
    <td>{c.name}</td>
    <td>{c.credits}</td>
  </tr>
))}
```

`map()`으로 각 강의를 한 행으로 만듭니다. `key`는 React가 항목을 구별하는 안정적인 ID입니다. 마우스 진입과 키보드 초점 모두 같은 미리보기를 실행합니다. 실제 코드에서는 마우스나 초점이 행을 벗어나면 미리보기를 해제합니다. `{c.name}`은 텍스트로 출력되므로 강의명을 HTML로 해석하지 않습니다.

## 7. 시간표 — Schedule.jsx

```jsx
const selected = chosen(state);
const preview = state.courses.find(
  c => c.id === previewId && !state.enrolledIds.includes(c.id)
);
```

`selected`는 신청 완료 강의, `preview`는 아직 신청하지 않은 미리보기 강의입니다. 둘을 구분해서 그리므로 커서를 올리는 동작이 실제 신청 내역을 바꾸지 않습니다.

시간표 좌표 계산을 간추린 예시입니다.

```jsx
style={{
  left: `calc(${m.day * 20}% + 2px)`,
  top: `calc(${(m.start - 540) / 540 * 100}% + 2px)`,
  height: `calc(${(m.end - m.start) / 540 * 100}% - 4px)`
}}
```

월~금은 각각 너비 20%입니다. 현재 시간표 범위는 09:00~18:00이고, 시간은 자정부터 지난 분으로 저장합니다. 첫 번째 540은 시작 시각 09:00, 나누는 540은 전체 9시간을 뜻합니다.

## 8. 수강신청과 서버 통신 — useCampus.js

실제 변경 처리의 핵심 발췌입니다.

```jsx
await request(`/api/${config[0]}/${id}`, config[1]);
committed = true;
await refresh();
notify(config[2]);
```

`config`는 신청·취소·장바구니별 URL과 HTTP 메서드를 담습니다. 신청 요청이면 `POST /api/enrollments/{id}`를 호출합니다. 성공 후 `refresh()`가 `/api/state`를 다시 조회하여 목록·학점·시간표를 함께 갱신합니다.

```text
버튼 클릭 → API 요청 → Spring 업무 검증·DB 저장
         → 최신 상태 조회 → React 상태 갱신 → 화면 반영
```

`useCampus`는 관련 상태와 함수를 묶은 **커스텀 Hook**입니다. `useEffect`로 최초 조회·20초 갱신·알림 타이머를 관리하고 정리 함수로 타이머를 해제합니다. `useRef`에는 요청 잠금 등 렌더링 자체를 유발할 필요가 없는 값을 보관합니다.

`api.js`는 세션 쿠키와 CSRF 토큰을 처리합니다. 세션 만료 시 개인 화면을 제거하고, 실패한 변경 요청은 자동 재전송하지 않습니다. 서버 저장 성공 후 화면 조회만 실패한 상황도 구별해서 안내합니다. 동시 신청의 정원·학점·시간 검증은 Spring 서버가 최종 책임집니다.

## 9. CSS 분리

```css
@import "./shared/styles/common.css";
@import "./features/dashboard/layout.css";
@import "./features/courses/courses.css";
@import "./features/timetable/timetable.css";
@import "./shared/ui/feedback.css";
@import "./features/auth/auth.css";
@import "./shared/styles/responsive.css";
@import "./features/timetable/print.css";
```

`styles.css`는 파일을 불러오는 진입점입니다. 실제 스타일은 해당 기능의 폴더에서 수정합니다. 기존 적용 순서를 보존하기 위해 반응형 규칙은 `shared/styles/responsive.css`, 인쇄 규칙은 마지막 `features/timetable/print.css`에 두었습니다. 순서를 바꾸면 같은 선택자의 최종 스타일이 달라질 수 있습니다.

## 10. 수정 후 실행

프로젝트 루트 `수강2`에서 실행합니다.

```sh
npm --prefix frontend run build
./mvnw spring-boot:run
```

프론트 개발 중에는 Spring 서버를 8080에서 켜고 별도 터미널에서 다음 명령을 실행합니다.

```sh
npm --prefix frontend run dev
```

Vite 화면(기본 5173)의 `/api`는 Spring 8080으로 전달됩니다. 이미 실행 중인 JAR는 파일 변경만으로 갱신되지 않으므로 배포용 JAR도 다시 빌드하고 재시작해야 합니다.

더 자세한 설명은 [React·Spring 상세 가이드](FRONTEND_SPRING_GUIDE.md)를 참고하세요.

## 11. 파일별 함수 찾아보기

2026-10-07 기준입니다. 아래 경로는 `frontend/src/` 기준이며, 컴포넌트 함수는 JSX를 반환하고 일반 함수는 계산·요청을 담당합니다.

| 파일 | 함수 | 기능 |
| --- | --- | --- |
| `App.jsx` | `App()` | 로딩·로그인·메인 화면을 고르고 알림을 표시 |
| `features/auth/AuthPage.jsx` | `AuthPage()` | 로그인·회원가입 폼 표시 |
| 같은 파일 | `toggle()` | 로그인/회원가입 전환 및 오류 초기화 |
| 같은 파일 | `authenticate(studentNo, password, name)` | 전달받은 login 실행, 처리 중 상태와 오류 관리 |
| 같은 파일 | `submit(e)` | 기본 폼 이동 방지, FormData에서 입력을 꺼내 authenticate 호출 |
| `features/dashboard/Dashboard.jsx` | `Dashboard()` | 메뉴·검색·강의 목록·시간표·확인창 조합 |
| 같은 파일 | `changeTab(value)` | 전체/장바구니/신청 내역 전환, 미리보기 해제 |
| 같은 파일 | `updateFilter(key, value)` | 검색 조건 하나 변경 |
| 같은 파일 | `resetFilters()` | 검색 조건과 미리보기 초기화 |
| 같은 파일 | `print()` | flushSync로 미리보기를 먼저 없애고 인쇄 창 열기 |
| 같은 파일 | `closeCancel()` | 취소 확인창 닫기, 자동 갱신 제한 해제 |
| 같은 파일 | `onAction(action, course)` | 취소는 확인창을 열고, 다른 변경은 mutate 실행 |
| `features/courses/CourseRows.jsx` | `CourseRows()` | 강의 행·정원·충돌·버튼 상태와 미리보기 이벤트 표시 |
| `features/timetable/Schedule.jsx` | `Schedule()` | 신청 강의와 미리보기 강의를 시간 좌표로 배치 |
| `shared/ui/Icon.jsx` | `Icon({ name })` | 이름에 대응하는 SVG 아이콘 표시 |
| `shared/ui/Modal.jsx` | `Modal()` | native dialog를 열고 Escape 처리·닫힌 뒤 이전 초점 복원 |

```jsx
function submit(e) {
  e.preventDefault();
  const values = Object.fromEntries(new FormData(e.currentTarget));
  authenticate(values.studentNo, values.password, registering ? values.name : undefined);
}
```

`preventDefault()`는 브라우저의 기본 페이지 이동을 막습니다. `FormData`는 폼의 name 속성을 기준으로 값을 읽습니다. 이름을 전달하면 회원가입 후 로그인, 전달하지 않으면 로그인만 수행합니다.

## 12. 상태 관리 Hook의 함수와 변수

파일: [useCampus.js](../frontend/src/features/registration/useCampus.js)

| 함수 | 하는 일 |
| --- | --- |
| `notify(message, error)` | 성공/실패 알림 저장, effect가 4.5초 후 제거 |
| `expire()` | 사용자 상태·CSRF·진행 중 조회 참조 초기화, 이전 응답 무효화 |
| `refresh()` | `/api/state` 조회. 진행 중인 조회를 공유하고 현재 세대 응답만 반영 |
| `login(studentNo, password, name)` | 선택적 회원가입 → 로그인 → CSRF 재조회 → 사용자 상태 조회 |
| `logout()` | 서버 로그아웃 후 개인 상태 제거 |
| `mutate(action, id)` | 신청·취소·장바구니 변경과 최신 상태 조회 |
| 반환 객체의 `refresh` | 버튼에서 사용하는 새로고침 래퍼. 변경 중에는 조회를 시작하지 않음 |
| `onDialogChange(value)` | 취소 확인창이 열린 동안 주기적 조회 제한 |

| 상태·참조 | 의미 |
| --- | --- |
| `state` | student, courses, enrolledIds, cartIds를 가진 서버 응답 |
| `loading`, `busy` | 첫 로딩 여부 / 변경 요청 처리 여부 |
| `demoEnabled`, `error`, `notice` | 체험 로그인 표시 여부 / 초기 오류 / 알림 |
| `epoch` | 로그인 상태가 바뀌기 전 시작된 조회 응답을 무시할 기준값 |
| `lock` | 변경 요청 중복 실행을 막는 프론트 잠금 |
| `pending` | 진행 중인 상태 조회 Promise |
| `dialog` | 취소 확인창 열림 여부 |

```js
const generation = epoch.current;
const task = request('/api/state').then((value) => {
  if (epoch.current === generation) setState(value);
});
```

핵심 발췌입니다. 로그아웃 직후 늦게 도착한 이전 사용자의 응답이 개인 화면을 다시 띄우지 않게 합니다. `lock`은 현재 브라우저의 중복 클릭을 막을 뿐이며, 다른 사용자의 동시 신청은 서버 DB 잠금으로 처리합니다.

## 13. 계산 함수와 HTTP 함수

| 파일 | 함수 | 입력 → 결과 |
| --- | --- | --- |
| `features/courses/courses.js` | `time(minute)` | 540 → `09:00` |
| 같은 파일 | `chosen(state)` | 신청 ID에 포함된 강의 배열 |
| 같은 파일 | `credits(state)` | 신청 완료 강의의 학점 합계 |
| 같은 파일 | `overlaps(course, selected)` | 요일·시간이 겹치는 강의가 있으면 true |
| 같은 파일 | `filterCourses(state, tab, filters)` | 탭·검색어·학과·이수구분·신청 가능 조건으로 필터링 |
| `shared/api/api.js` | `getCsrf()` | 서버에서 토큰과 헤더 이름을 받아 모듈 변수에 보관 |
| 같은 파일 | `clearCsrf()` | 저장된 토큰 제거 |
| 같은 파일 | `request(url, method, body)` | 세션 쿠키·CSRF·본문 형식을 처리하고 응답 데이터 반환 |

```js
// overlaps 내부의 시간 충돌 조건
 a.day === b.day && a.start < b.end && b.start < a.end
```

같은 요일에 두 시간 구간이 겹치는지 검사합니다. 10:00 종료와 10:00 시작은 겹치지 않습니다. 신청 가능 필터는 화면 안내이며 서버가 같은 기준을 다시 검증합니다.

```js
const response = await fetch(url, {
  method, headers, body, credentials: 'same-origin'
});
```

동일 출처 세션 쿠키를 전송합니다. 일반 객체 본문은 JSON, 로그인용 URLSearchParams는 폼 형식입니다. 실패하면 status를 붙인 Error를 던져 상위 함수가 안내합니다.

## 14. CSS·설정·테스트 폴더

| 파일 | 담당 범위 |
| --- | --- |
| `shared/styles/common.css` | 공통 색상·기본 요소 |
| `features/auth/auth.css` | 로그인·회원가입 |
| `features/dashboard/layout.css` | 전체 배치·사이드바 |
| `features/courses/courses.css` | 검색·목록·강의 행 |
| `features/timetable/timetable.css` | 시간표 격자와 강의 블록 |
| `features/timetable/print.css` | 인쇄 화면 |
| `shared/ui/feedback.css` | 알림·모달 등 피드백 |
| `shared/styles/responsive.css` | 화면 폭에 따른 배치 조정 |
| `tests/App.test.jsx`, `tests/setup.js` | 화면 동작 테스트와 테스트 환경 초기화 |
| `frontend/vite.config.js` | React 플러그인, API 프록시, 빌드 출력, 테스트 환경 |
| `frontend/package.json` | 의존성과 dev/build/test 명령 |

설정·package.json 경로만 프로젝트 루트 기준입니다. node_modules는 설치 결과, 서버의 static 폴더는 빌드 결과입니다.

## 15. 별도 챗봇 React

원본은 `academic-advisor/frontend/src/`입니다. 수강신청 React의 App에 연결하지 않은 별도 실행 앱입니다.

```text
main.jsx                         # 소개 화면과 Advisor 렌더링
features/advisor/Advisor.jsx      # 학적 폼·대화·추천 질문
features/advisor/advisor.css      # 챗봇 패널 스타일
shared/api/api.js                # HTTP·CSRF 공통 처리
styles.css                      # 소개 화면 기본 스타일
tests/                          # 챗봇 화면 테스트
```

| 함수·상태 | 기능 |
| --- | --- |
| `Advisor()` | 학적 정보 폼과 대화 패널 구성 |
| `fail(e)` | 오류 표시, 401이면 전달받은 세션 만료 콜백 실행 |
| `toggle()` | 패널 열기/닫기, 열 때 서버 프로필 조회 |
| `close()` | 패널 닫기, 실행 버튼으로 초점 복원 |
| `save(e)` | 프로필 PUT 요청, 대화·추천 질문 초기화 |
| `send(value)` | 공백 검사 → 질문 표시 → POST 요청 → 답변 표시 |
| `open`, `editing`, `profile` | 패널·프로필 수정 영역·학적 정보 |
| `messages`, `question`, `suggestions` | 현재 대화·입력·추천 질문 |
| `busy`, `error`, `inFlight` | 처리 표시·오류·중복 요청 제한 |
| `input`, `launcher`, `log` | 질문 입력·실행 버튼·대화 목록 DOM 참조 |
| `active` | 화면 제거 후 비동기 결과 반영 방지 |
| `topic` | 이전 주제 전달용 값. 현재 독립 서버에서는 사용하지 않음 |

```jsx
const answer = await request('/api/advisor/chat', 'POST', {
  message: text,
  previousTopic: topic,
});
setMessages((m) => [...m, { role: 'assistant', ...answer }]);
```

핵심 발췌입니다. 기존 대화 배열에 새 답변을 추가합니다. 현재 독립 서버의 Question은 message만 받고 Answer에는 topic이 없으므로, 이전 대화의 맥락을 이해하는 기능으로 해석하면 안 됩니다. 프로필은 서버 세션에, 대화는 브라우저 메모리에 보관합니다. 새로고침하면 대화가 사라집니다.

## 16. 기능별로 코드 따라 읽기

```text
로그인: AuthPage.submit → authenticate → useCampus.login → request → Spring Security
신청: CourseRows 버튼 → Dashboard.onAction → useCampus.mutate → API → refresh
취소: Dashboard.onAction → Modal 확인 → mutate('cancel', id) → API → refresh
미리보기: CourseRows.onMouseEnter/onFocus → previewId → Schedule
검색: 입력 onChange → updateFilter → filterCourses → CourseRows
챗봇: Advisor.send → request → 독립 AdvisorController.chat → CurriculumService.answer
```

백엔드 처리는 [Spring·JPA·Python 코드 설명 요약본](BACKEND_SUMMARY.md), 전체 파일 분류는 [폴더 구조 안내](FOLDER_STRUCTURE.md)를 이어서 읽으면 됩니다.
