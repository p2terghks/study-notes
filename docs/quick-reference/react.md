# React 함수·Hook 요약

## 먼저 보는 기능 지도

**React Hook, 일반 JavaScript 함수, 브라우저 API를 구분해 사용합니다.** 함수 컴포넌트 기준이며 Action 관련 항목은 React 19 이상입니다. 코드 일부는 컴포넌트 내부에 넣는 발췌입니다. 필요한 Hook은 react에서 import합니다.

| 목적 | 기능 | 종류 |
|---|---|---|
| 화면 상태 | useState | React Hook |
| 외부 시스템 동기화 | useEffect | React Hook |
| DOM·변경 가능한 값 보관 | useRef | React Hook |
| 하위 트리에 값 공유 | createContext, useContext | API·Hook |
| 복잡한 상태 전환 | useReducer | Hook |
| 계산·함수 참조 캐시 | useMemo, useCallback | Hook |
| 렌더링 우선순위 | useTransition, useDeferredValue | Hook |
| 폼 작업 | useActionState, useFormStatus | React 19 Hook |
| 배열 변환 | map, filter, find | JavaScript |
| HTTP 요청 | fetch | 브라우저 API |

Hook은 컴포넌트 또는 사용자 정의 Hook의 최상위에서 호출합니다. 조건문·반복문·이벤트 핸들러 안에서 호출하지 않습니다. [공식 Hook 목록](https://react.dev/reference/react/hooks)

## useState — 상태 저장

**언제:** 입력값, 열림 여부, 목록처럼 화면에 영향을 주는 값.

```jsx
import { useState } from "react";

function Counter() {
  const [count, setCount] = useState(0);
  return (
    <button onClick={() => setCount(previous => previous + 1)}>
      {count}
    </button>
  );
}
```

| 요소 | 역할 |
|---|---|
| useState(0) | 초기값 설정 |
| count | 현재 렌더링에서의 값 |
| setCount | 다음 상태를 요청 |
| previous => previous + 1 | 이전 상태로 다음 상태 계산 |

setter를 불렀다고 현재 함수의 변수가 즉시 바뀌지는 않습니다. 객체·배열은 직접 수정하지 말고 새 값으로 교체합니다. [공식 useState](https://react.dev/reference/react/useState)

## useEffect — 외부 시스템과 동기화

**언제:** 타이머, 이벤트 구독, 외부 위젯 연결. 단순 계산은 렌더링에서 바로 처리합니다.

```jsx
import { useEffect, useState } from "react";

function Timer() {
  const [seconds, setSeconds] = useState(0);
  useEffect(() => {
    const timer = setInterval(() => setSeconds(s => s + 1), 1000);
    return () => clearInterval(timer);
  }, []);
  return <p>{seconds}초</p>;
}
```

| 의존성 | 동작 |
|---|---|
| 생략 | 매 커밋 후 실행 |
| [] | 마운트에 따른 설정, 해제 때 정리 |
| [id] | 초기 설정 후 id가 바뀌면 정리·재설정 |

개발 Strict Mode에서는 설정·정리를 추가 실행해 대칭성을 점검할 수 있습니다. ‘무조건 한 번 실행’으로 외우지 마세요. 사용한 반응형 값을 의존성에 포함하고, Effect 함수 자체를 async로 만들지 않습니다.

[공식 useEffect](https://react.dev/reference/react/useEffect)

## useRef — DOM 접근·렌더링 밖 값

```jsx
import { useRef } from "react";

function SearchBox() {
  const inputRef = useRef(null);
  return (
    <>
      <input ref={inputRef} />
      <button onClick={() => inputRef.current?.focus()}>입력창 이동</button>
    </>
  );
}
```

**기능:** ref 객체의 current에 DOM이나 타이머 ID 등을 보관합니다. current를 바꿔도 리렌더링을 요청하지 않습니다. 화면에 표시할 값은 state가 적합합니다. 렌더링 중 임의로 ref를 읽고 쓰기보다 이벤트나 Effect에서 사용하세요.

[공식 useRef](https://react.dev/reference/react/useRef)

## useContext — 트리에 값 공유

```jsx
import { createContext, useContext } from "react";

const ThemeContext = createContext("light");

function Toolbar() {
  const theme = useContext(ThemeContext);
  return <p>테마: {theme}</p>;
}

function App() {
  return (
    <ThemeContext.Provider value="dark">
      <Toolbar />
    </ThemeContext.Provider>
  );
}
```

**언제:** 테마, 로그인한 사용자 정보 등 여러 하위 컴포넌트에 전달할 값. 가장 가까운 상위 Provider 값을 읽습니다. Provider 값이 변하면 이를 구독하는 컴포넌트도 갱신될 수 있습니다. 브라우저의 로그인 정보 표시와 서버 권한 검사는 별개입니다.

[공식 useContext](https://react.dev/reference/react/useContext)

## useReducer — 상태 전환 규칙 모으기

```jsx
import { useReducer } from "react";

function reducer(state, action) {
  switch (action.type) {
    case "increase": return { count: state.count + 1 };
    case "reset": return { count: 0 };
    default: return state;
  }
}

function Counter() {
  const [state, dispatch] = useReducer(reducer, { count: 0 });
  return (
    <button onClick={() => dispatch({ type: "increase" })}>
      {state.count}
    </button>
  );
}
```

**기능:** dispatch가 작업을 전달하면 reducer가 다음 상태를 계산합니다. reducer는 네트워크 요청이나 기존 state 변경 없이 새 상태를 반환하는 순수 함수로 작성합니다.

[공식 useReducer](https://react.dev/reference/react/useReducer)

## useMemo·useCallback·memo — 최적화

| 기능 | 저장하는 것 | 주로 사용하는 상황 |
|---|---|---|
| useMemo | 계산 결과 | 비용이 큰 순수 계산 |
| useCallback | 함수 참조 | memo 자식에 전달하는 콜백 |
| memo | 컴포넌트 최적화 래퍼 | 같은 props로 불필요한 렌더 줄이기 |

```jsx
const visible = useMemo(
  () => todos.filter(todo => todo.title.includes(keyword)),
  [todos, keyword]
);

const onDelete = useCallback(id => {
  setTodos(previous => previous.filter(todo => todo.id !== id));
}, []);
```

todos, keyword, setTodos가 컴포넌트에 선언된 문맥의 발췌입니다. useCallback은 함수 실행 결과를 저장하지 않습니다. useMemo·memo는 정확성을 위한 조건이 아니라 성능 최적화입니다. 느린 지점을 확인한 후 사용하세요.

[useMemo](https://react.dev/reference/react/useMemo) · [useCallback](https://react.dev/reference/react/useCallback) · [memo](https://react.dev/reference/react/memo)

## useTransition·useDeferredValue — 반응성 유지

```jsx
const [tab, setTab] = useState("home");
const [isPending, startTransition] = useTransition();

function selectTab(nextTab) {
  startTransition(() => setTab(nextTab));
}
```

**useTransition:** 중요하지만 급하지 않은 상태 업데이트를 표시합니다. 타이핑 입력값 자체는 즉시 갱신하고, 무거운 화면 전환 등을 Transition으로 다룹니다.

```jsx
const [query, setQuery] = useState("");
const deferredQuery = useDeferredValue(query);
```

**useDeferredValue:** 최신 값보다 늦게 따라와도 되는 화면에 사용할 값을 제공합니다. 느린 목록 컴포넌트 등에 전달합니다. 고정 지연 시간의 debounce도, 네트워크 요청 횟수 제한도 아닙니다.

[useTransition](https://react.dev/reference/react/useTransition) · [useDeferredValue](https://react.dev/reference/react/useDeferredValue)

## React 19 — useActionState·useFormStatus

**언제:** 폼 작업의 결과·대기 상태를 관리할 때. 아래는 네트워크 없이 동작하는 입력 검사 예시입니다.

```jsx
import { useActionState } from "react";
import { useFormStatus } from "react-dom";

function SubmitButton() {
  const { pending } = useFormStatus();
  return <button disabled={pending}>확인</button>;
}

function NameForm() {
  const [message, action, pending] = useActionState(
    async (previous, formData) => {
      const name = String(formData.get("name") ?? "").trim();
      return name ? `${name}님, 반갑습니다.` : "이름을 입력하세요.";
    },
    ""
  );
  return (
    <form action={action}>
      <input name="name" />
      <SubmitButton />
      <p aria-live="polite">{pending ? "처리 중" : message}</p>
    </form>
  );
}
```

useFormStatus는 해당 form의 **자식 컴포넌트**에서 호출합니다. useActionState의 action을 form에 전달하면 Action 문맥으로 실행됩니다. 이것만으로 Spring API 호출이나 DB 저장이 생기지는 않습니다.

[useActionState](https://react.dev/reference/react/useActionState) · [useFormStatus](https://react.dev/reference/react-dom/hooks/useFormStatus)

## 이벤트·배열 함수 — React 전용이 아닌 것

| 함수·속성 | 역할 | 사용 예 |
|---|---|---|
| onClick | 클릭 처리 연결 | onClick={handleClick} |
| onChange | 입력값 갱신 | setTitle(e.target.value) |
| onSubmit | 폼 제출 처리 | handleSubmit |
| preventDefault() | 브라우저 기본 동작 취소 | 폼의 기본 이동 방지 |
| map() | 항목마다 새 값 생성 | 배열을 JSX 목록으로 |
| filter() | 조건에 맞는 항목 유지 | 삭제한 ID 제외 |
| find() | 첫 항목 조회 | 없으면 undefined |
| includes() | 포함 여부 | 문자열 검색 |

```jsx
setTodos(previous => [...previous, newTodo]);
setTodos(previous => previous.filter(todo => todo.id !== id));

// JSX 안에서 사용
{todos.map(todo => <li key={todo.id}>{todo.title}</li>)}
```

newTodo와 id는 이벤트 핸들러가 준비하는 값입니다. key는 형제 목록에서 안정적이고 고유한 ID를 사용합니다.

## fetch — Spring API 요청

```js
async function loadTodos(signal) {
  const response = await fetch("/api/todos", { signal });
  if (!response.ok) throw new Error("목록 조회 실패");
  return response.json();
}
```

```jsx
useEffect(() => {
  const controller = new AbortController();
  let active = true;
  setLoading(true);
  setError("");

  loadTodos(controller.signal)
    .then(data => { if (active) setTodos(data); })
    .catch(error => {
      if (active && error.name !== "AbortError") setError(error.message);
    })
    .finally(() => { if (active) setLoading(false); });

  return () => {
    active = false;
    controller.abort();
  };
}, []);
```

컴포넌트에 todos=[], loading=false, error=""의 useState가 선언되어 있다고 가정합니다. 상대 경로는 현재 화면 서버 기준이므로 개발 프록시 또는 적절한 서버 주소·CORS 구성이 필요합니다. Spring /todos가 HTML을 반환한다면 JSON 파싱에 사용할 수 없습니다.

fetch는 404·500만으로 reject되지 않으므로 response.ok를 검사합니다. Effect 요청은 해제·취소와 오래된 결과 처리를 고려합니다. [공식: Effect로 데이터 조회](https://react.dev/reference/react/useEffect#fetching-data-with-effects)

## 기능 선택 빠른 정리

| 질문 | 선택 |
|---|---|
| 값이 바뀌면 화면도 바뀌어야 하나? | useState / useReducer |
| 화면 표시와 무관하게 값을 기억하나? | useRef |
| props로 전달하기 너무 깊은가? | Context 검토 |
| 외부 시스템과 연결하는가? | useEffect |
| 현재 props·state로 바로 계산 가능한가? | 일반 계산, 필요할 때 useMemo |
| 서버 요청인가? | fetch 또는 데이터 조회 라이브러리 |

`useId`, `useOptimistic`, `useSyncExternalStore` 같은 추가 Hook은 폼 접근성 ID, 낙관적 UI, 외부 저장소 구독이 필요할 때 공식 레퍼런스에서 확장해 보세요. 이 요약은 모든 API 목록이 아니라 자주 쓰는 기능 중심입니다.
