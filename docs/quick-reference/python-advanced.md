# Python 문법 심화 과정

## 1. 학습 순서와 실행 환경

함수·리스트·딕셔너리·반복문을 배운 뒤 읽는 과정입니다. 예제는 **Python 3.11 이상**을 대상으로 합니다. TaskGroup은 3.11부터 지원합니다. 각 Python 코드 블록은 독립적으로 실행할 수 있으며, `assert`가 통과하면 출력 없이 끝나는 예제도 있습니다.

| 단계 | 주제 | 확인할 능력 |
| --- | --- | --- |
| 1 | 객체·함수·클로저 | 값이 공유되는 이유 설명 |
| 2 | 이터레이터·데코레이터 | 지연 계산과 함수 확장 |
| 3 | 클래스·컨텍스트·타입 | 데이터와 책임 분리 |
| 4 | 비동기·통합 예제 | 실행 흐름과 오류 검증 |

```bash
python3 --version
python3 -m venv .venv
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python example.py
```

기초가 부족하면 [Python 입문 가이드](../python-syntax-guide.html)를 먼저 읽으세요. 외부 패키지는 필요하지 않습니다.

## 2. 객체 참조와 얕은 복사·깊은 복사

변수는 객체에 붙인 이름입니다. 대입은 객체 복제가 아니며 `==`는 값, `is`는 같은 객체인지를 비교합니다. `None` 확인에는 `is None`을 사용합니다.

```python
from copy import deepcopy
original = [[1], [2]]
alias = original
shallow = original.copy()
deep = deepcopy(original)
original[0].append(9)
assert alias is original
assert shallow == [[1, 9], [2]]  # 내부 리스트는 공유
assert deep == [[1], [2]]
assert shallow is not original
```

튜플도 내부에 리스트를 담으면 그 리스트는 바뀔 수 있습니다. 깊은 복사는 필요한 경계에서만 사용하고, 가능한 한 데이터 구조를 단순하게 만드세요. [공식 문서: copy](https://docs.python.org/3.12/library/copy.html)

## 3. 함수 인자와 가변 기본값

`/` 앞은 위치 전용, `*` 뒤는 키워드 전용입니다. `*args`는 나머지 위치 인자를 튜플로, `**kwargs`는 나머지 키워드 인자를 딕셔너리로 받습니다.

```python
def discount(price, /, *, rate=0.1):
    return price * (1 - rate)
assert discount(100, rate=0.2) == 80

def collect(value, bucket=None):
    if bucket is None:
        bucket = []
    bucket.append(value)
    return bucket
assert collect(1) == [1]
assert collect(2) == [2]

def describe(*args, **kwargs):
    return args, kwargs
assert describe(1, 2, name="Kim") == ((1, 2), {"name": "Kim"})
```

`bucket=[]`를 기본값으로 쓰면 함수 정의 시 만든 리스트를 호출마다 공유합니다. `None`으로 구분한 뒤 호출 안에서 생성하세요. [공식 문서: 함수 인자](https://docs.python.org/3.12/tutorial/controlflow.html#more-on-defining-functions)

## 4. 스코프·클로저·늦은 바인딩

이름은 보통 지역 → 바깥 함수 → 모듈 전역 → 내장 영역 순서로 찾습니다. 클로저는 바깥 함수의 변수를 기억하는 함수입니다. 바깥 변수에 다시 대입하려면 `nonlocal`을 사용합니다.

```python
def counter():
    count = 0
    def increase():
        nonlocal count
        count += 1
        return count
    return increase
c = counter()
assert (c(), c()) == (1, 2)

wrong = [lambda: i for i in range(3)]
right = [lambda i=i: i for i in range(3)]
assert [f() for f in wrong] == [2, 2, 2]
assert [f() for f in right] == [0, 1, 2]
```

첫 리스트의 함수들은 호출할 때 같은 `i`를 읽습니다. 기본 인자로 값을 저장하면 각 함수가 생성된 시점의 값을 사용할 수 있습니다. [공식 문서: 스코프](https://docs.python.org/3.12/tutorial/classes.html#python-scopes-and-namespaces)

## 5. 컴프리헨션과 언패킹

짧은 변환·필터에는 컴프리헨션이 유용합니다. 조건과 중첩이 길어지면 일반 반복문으로 분리하세요. 리스트 컴프리헨션은 결과 전체를 즉시 만들고, 제너레이터 표현식은 요청할 때 계산합니다.

```python
scores = {"Kim": 90, "Lee": 55, "Park": 80}
passed = {name: score for name, score in scores.items() if score >= 60}
assert list(passed) == ["Kim", "Park"]
first, *middle, last = [1, 2, 3, 4]
assert middle == [2, 3]
assert sum(n * n for n in range(4)) == 14
```

`zip`은 기본적으로 짧은 입력에 맞춰 끝납니다. 길이가 같아야 하는 입력에는 `zip(a, b, strict=True)`를 사용해 누락을 탐지하세요. [공식 문서: 자료구조](https://docs.python.org/3.12/tutorial/datastructures.html)

## 6. 이터러블·이터레이터·제너레이터

이터러블은 `iter()`로 이터레이터를 얻을 수 있는 객체입니다. 이터레이터는 `next()`로 다음 항목을 꺼내며 끝나면 `StopIteration`이 발생합니다. 제너레이터는 `yield`로 중간 실행 상태를 보존하는 이터레이터입니다.

```python
def even_squares(limit):
    for n in range(limit):
        if n % 2 == 0:
            yield n * n
stream = even_squares(6)
assert next(stream) == 0
assert list(stream) == [4, 16]
assert list(stream) == []  # 이미 소비됨
assert next(stream, "끝") == "끝"

def flatten(rows):
    for row in rows:
        yield from row
assert list(flatten([[1, 2], [3]])) == [1, 2, 3]
```

지연 계산은 중간 결과 메모리를 줄일 수 있지만 소비된 이터레이터를 자동으로 되돌리지는 않습니다. 다시 읽어야 하면 새로 생성하세요. [공식 문서: 제너레이터](https://docs.python.org/3.12/tutorial/classes.html#generators)

## 7. 데코레이터와 functools.wraps

데코레이터는 함수를 받아 확장한 함수를 반환합니다. `@decorate`는 함수 정의 후 `f = decorate(f)`를 적용하는 표현입니다. 아래는 호출 결과에 접두어를 붙이는 데코레이터 팩터리입니다.

```python
from functools import wraps

def prefix(text):
    def decorate(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            return text + func(*args, **kwargs)
        return wrapped
    return decorate

@prefix("안녕, ")
def greet(name):
    return name
assert greet("Python") == "안녕, Python"
assert greet.__name__ == "greet"
```

`wraps`는 원래 함수의 이름·문서 등 메타데이터를 보존합니다. 비동기 함수를 감싸는 경우에는 별도의 `async def` 래퍼에서 `await func(...)`가 필요할 수 있습니다. [공식 문서: wraps](https://docs.python.org/3.12/library/functools.html#functools.wraps)

## 8. 클래스·프로퍼티·특수 메서드

인스턴스 상태는 `self`에 저장합니다. 클래스 변수는 공유되므로 인스턴스별 리스트를 클래스 본문에 두지 마세요. 프로퍼티는 속성 접근 형태로 계산값을 제공할 때 유용합니다.

```python
class Basket:
    def __init__(self):
        self.items = []
    def add(self, price):
        if price < 0:
            raise ValueError("가격은 0 이상")
        self.items.append(price)
    @property
    def total(self):
        return sum(self.items)
    def __len__(self):
        return len(self.items)
    def __repr__(self):
        return f"Basket(items={self.items!r})"
a, b = Basket(), Basket()
a.add(3000)
assert a.total == 3000 and len(a) == 1
assert len(b) == 0
```

`__repr__`는 개발자가 상태를 파악하는 표현, `__len__`는 `len()`의 동작을 정의합니다. 상속은 실제로 같은 종류인 관계에 쓰고, 기능 조합에는 객체를 멤버로 담는 구성을 고려하세요. [공식 문서: 데이터 모델](https://docs.python.org/3.12/reference/datamodel.html)

## 9. dataclass로 데이터 모델 만들기

`dataclass`는 필드 선언을 바탕으로 초기화·표현·동등 비교 메서드 등을 생성합니다. 리스트는 `default_factory`로 인스턴스마다 새로 생성하세요.

```python
from dataclasses import dataclass, field

@dataclass
class Student:
    name: str
    scores: list[int] = field(default_factory=list)
    def __post_init__(self):
        if not self.name.strip():
            raise ValueError("이름이 필요합니다")
a, b = Student("Kim"), Student("Lee")
a.scores.append(90)
assert b.scores == []
assert Student("Kim", [90]) == a
```

타입 선언만으로 입력 검증은 수행되지 않습니다. `frozen=True`는 필드 재대입을 막지만 필드 안의 리스트까지 불변으로 만들지는 않습니다. [공식 문서: dataclasses](https://docs.python.org/3.12/library/dataclasses.html)

## 10. 예외 처리와 컨텍스트 매니저

예외는 처리할 수 있는 범위에서 구체적으로 잡으세요. `else`는 예외 없이 끝났을 때, `finally`는 정상 종료·예외 모두에서 정리 작업에 쓰입니다. `raise ... from exc`는 원인을 보존합니다.

```python
from contextlib import contextmanager
from io import StringIO

def parse_age(text):
    try:
        return int(text)
    except ValueError as exc:
        raise ValueError("나이는 정수여야 합니다") from exc

@contextmanager
def text_buffer(text):
    buffer = StringIO(text)
    try:
        yield buffer
    finally:
        buffer.close()

with text_buffer("42") as buffer:
    assert parse_age(buffer.read()) == 42
assert buffer.closed
```

`@contextmanager` 함수는 정확히 한 번 `yield`해야 합니다. 실제 파일은 `with open(path, encoding="utf-8") as f:`로 관리하세요. `except Exception: pass`로 실패를 숨기지 마세요. [공식 문서: contextlib](https://docs.python.org/3.12/library/contextlib.html)

## 11. 타입 힌트·제네릭·Protocol

타입 힌트는 코드 이해와 정적 검사에 도움을 주지만 Python 실행기가 자동으로 타입을 강제하지는 않습니다. `str | None`은 문자열 또는 None, `list[int]`는 정수 리스트를 뜻합니다.

```python
from typing import Protocol, TypeVar

T = TypeVar("T")
def first(values: list[T]) -> T | None:
    return values[0] if values else None

class HasTotal(Protocol):
    def total(self) -> int: ...

class Bill:
    def total(self) -> int:
        return 1200

def checkout(bill: HasTotal) -> int:
    return bill.total()
assert first([3, 4]) == 3
assert first([]) is None
assert checkout(Bill()) == 1200
```

Protocol은 요구 메서드의 형태로 호환성을 표현합니다. `Bill`은 명시적으로 상속하지 않아도 정적 검사에서 구조가 맞으면 사용할 수 있습니다. `Any`를 남발하면 검사 효과가 줄어듭니다. [공식 문서: typing](https://docs.python.org/3.12/library/typing.html)

## 12. 표준 라이브러리로 간결하게 풀기

| 도구 | 용도 | 주의 |
| --- | --- | --- |
| Counter | 빈도 계산 | 없는 키는 0 |
| defaultdict | 그룹별 누적 | 키 조회가 새 항목을 만들 수 있음 |
| deque | 양끝 큐 | 중간 무작위 접근용이 아님 |
| lru_cache | 반복 계산 재사용 | 인자는 해시 가능해야 함 |

```python
from collections import Counter, defaultdict, deque
from functools import lru_cache
assert Counter("banana")["a"] == 3
groups = defaultdict(list)
for name, team in [("Kim", "A"), ("Lee", "A")]:
    groups[team].append(name)
assert groups["A"] == ["Kim", "Lee"]
queue = deque([1, 2])
assert queue.popleft() == 1

@lru_cache(maxsize=128)
def fib(n):
    if n < 0:
        raise ValueError("n은 0 이상")
    return n if n < 2 else fib(n - 1) + fib(n - 2)
assert fib(10) == 55
```

캐시는 외부 상태에 따라 바뀌는 결과를 오래 보관할 수 있습니다. 부작용 없는 계산에 적용하고, 필요하면 `cache_clear()`로 비우세요. 위 재귀 예제는 큰 n에서 재귀 한계가 있으므로 반복문을 고려하세요. [collections](https://docs.python.org/3.12/library/collections.html) · [lru_cache](https://docs.python.org/3.12/library/functools.html#functools.lru_cache)

## 13. match 패턴과 입력 검증

`match`는 단순 값 비교를 넘어 자료의 구조를 분해합니다. `case` 안의 새 이름은 보통 값을 비교하는 상수가 아니라 값을 받는 변수입니다. `_`는 나머지 패턴입니다.

```python
def command(payload):
    match payload:
        case {"action": "add", "value": int(value)} if not isinstance(value, bool):
            return value + 1
        case {"action": "quit"}:
            return None
        case _:
            raise ValueError("알 수 없는 명령")
assert command({"action": "add", "value": 4}) == 5
assert command({"action": "quit"}) is None
```

단순 캡처만으로 타입 검증은 되지 않습니다. 위에서는 `int(value)` 클래스 패턴과 가드로 검증합니다. 매핑 패턴은 명시하지 않은 추가 키를 허용합니다. [공식 문서: match](https://docs.python.org/3.12/tutorial/controlflow.html#match-statements)

## 14. async·await와 TaskGroup

`async def` 호출은 코루틴 객체를 만들며, `await` 또는 태스크 예약을 통해 실행됩니다. 비동기는 대기 시간을 활용하는 동시성 도구이며 CPU 계산을 자동 병렬화하지 않습니다.

```python
import asyncio

async def fetch_score(name, score):
    await asyncio.sleep(0.01)  # 네트워크 대기 모의
    return name, score

async def main():
    async with asyncio.TaskGroup() as group:
        tasks = [group.create_task(fetch_score(name, score))
                 for name, score in [("Kim", 90), ("Lee", 80)]]
    results = [task.result() for task in tasks]
    assert results == [("Kim", 90), ("Lee", 80)]

if __name__ == "__main__":
    asyncio.run(main())
```

TaskGroup을 나갈 때 작업 완료를 기다립니다. 작업 하나가 취소 이외의 예외로 실패하면 다른 작업을 취소하고, 실패를 예외 그룹으로 전달합니다. 취소 예외를 함부로 삼키지 마세요. 이벤트 루프 안에서 `time.sleep()`이나 긴 동기 작업을 호출하면 다른 작업도 지연됩니다. 노트북처럼 이미 루프가 실행되는 곳에서는 `asyncio.run()` 대신 `await main()`을 사용하세요. [공식 문서: asyncio 태스크](https://docs.python.org/3.11/library/asyncio-task.html)

## 15. 모듈 분리와 실행 진입점

모듈은 책임별 파일, 패키지는 모듈을 묶은 구조입니다. `if __name__ == "__main__":`는 직접 실행했을 때만 진입 함수를 호출하게 합니다. import만 했는데 서버가 실행되거나 파일이 바뀌는 부작용을 피하세요.

```python
from pathlib import Path

def main():
    current = Path(__file__).resolve().parent
    print("이 스크립트의 폴더:", current)

if __name__ == "__main__":
    main()
```

파일로 저장해 실행하는 예제입니다. 대화형 환경에서는 `__file__`이 없을 수 있습니다. 파일명을 `typing.py`, `json.py`, `asyncio.py`처럼 표준 라이브러리와 같게 만들면 import가 가려질 수 있습니다. [공식 문서: 모듈](https://docs.python.org/3.12/tutorial/modules.html)

## 16. 복습 문제와 다음 단계

1. 얕은 복사 뒤 내부 리스트를 바꾸면 원본도 바뀌는 이유는? **내부 객체의 참조를 공유하기 때문입니다.**
2. 제너레이터를 두 번 `list()`로 감싸면? **첫 호출이 소비했으므로 다음은 빈 리스트입니다.**
3. `frozen=True`와 타입 힌트만으로 모든 입력이 안전한가? **아닙니다. 내부 객체 변경과 실행 시 검증은 별도입니다.**
4. 비동기 함수 안의 `time.sleep()`은 왜 문제인가? **이벤트 루프 스레드를 막아 다른 작업도 기다리게 합니다.**
5. 클로저와 데코레이터는 어떻게 연결되는가? **래퍼 함수가 원래 함수와 옵션을 바깥 스코프에서 기억합니다.**

직접 바꿔보기: 성적 목록을 dataclass로 만들고, 제너레이터로 합격자를 선택한 뒤 Counter로 등급별 인원을 집계하세요. 빈 입력, 잘못된 점수, 학생별 리스트 독립성을 확인하세요. 파일 기반 실습은 기존 별도 `실습` 폴더에서 진행하고 이 문서는 개념과 짧은 예제를 찾아보는 데 사용하세요.
