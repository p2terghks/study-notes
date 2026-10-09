# Python 심화과정 — 원리부터 실전까지

## 1. 학습 방법과 실행 환경

이 과정의 목표는 어려운 문법을 많이 외우는 것이 아니라, **코드가 어떤 순서로 실행되고 어떤 객체가 바뀌는지 설명하는 것**입니다. 함수·반복문·리스트·딕셔너리를 사용해 본 사람을 대상으로 합니다. 낯설다면 [Python 기초 가이드](../python-syntax-guide.html)를 먼저 읽으세요.

| 구간 | 내용 | 해결하게 되는 문제 |
| --- | --- | --- |
| 2~5장 | 객체, 복사, 인자, 스코프 | 다른 변수의 값이 왜 함께 바뀌는가? |
| 6~9장 | 클로저, 데코레이터, 지연 평가 | 함수를 재사용하고 실행 시점을 제어하는 법 |
| 10~13장 | 클래스, dataclass, 구성, 특수 메서드 | 데이터를 책임 있는 객체로 묶는 법 |
| 14~17장 | 예외, 자원 관리, 타입, 표준 도구 | 실패를 추적하고 의도를 표현하는 법 |
| 18~21장 | 패턴, 모듈, 비동기, 성능 | 실제 프로그램의 실행 방식을 설계하는 법 |
| 22~24장 | 통합 프로젝트, 테스트, 연습 해설 | 배운 문법을 하나의 프로그램에 연결하는 법 |

한 장을 읽을 때는 ① 실행 전에 출력 예상 → ② 직접 실행 → ③ 예상과 다른 부분의 참조·실행 순서 그리기 → ④ 빈 값·경계값·잘못된 값 넣기 → ⑤ 언제 쓰는지 자기 말로 설명하기 순서로 공부하세요.

문법 기준은 **Python 3.11 이상**입니다. `TaskGroup`, `asyncio.timeout`, `except*`는 3.11부터 지원합니다. 예제는 표준 라이브러리만 사용합니다. 22~23장의 파일 실습을 제외한 각 `python` 블록은 독립적으로 실행할 수 있습니다. `text` 블록은 출력·파일 구조이며 실행 코드가 아닙니다. 일부 예제는 출력 대신 `assert`로 결과를 확인합니다.

```bash
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python example.py
```

Windows PowerShell:

```powershell
py -3 --version
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python example.py
```

가상환경은 프로젝트별 패키지 공간을 분리합니다. 활성화가 어려우면 macOS/Linux는 `.venv/bin/python example.py`, Windows는 `.venv\Scripts\python.exe example.py`로 환경의 실행기를 직접 사용해도 됩니다. 터미널 명령을 Python의 `>>>` 프롬프트에 입력하지 않습니다.

> `assert 조건`은 거짓일 때 `AssertionError`를 발생시킵니다. 학습 결과와 테스트에 유용하지만 `python -O`에서는 제거될 수 있습니다. 사용자 입력 검증은 `if`와 `raise`로 작성하세요.

## 2. 변수는 객체를 가리키는 이름

### 왜 알아야 하나

리스트를 함수에 넘겼더니 원본이 바뀌거나, 복사했다고 생각한 데이터가 같이 바뀌는 문제는 대부분 **이름과 객체를 구분하지 않아서** 생깁니다. 객체에는 값·타입·정체성이 있고, 변수는 그 객체에 연결된 이름입니다.

```python
a = [10, 20]
b = a
b.append(30)
print(a)
print(a is b)
b = [99]
print(a)
print(b)
print(a is b)
```

```text
[10, 20, 30]
True
[10, 20, 30]
[99]
False
```

1. `a = [10, 20]`은 리스트 하나를 만들고 이름 `a`를 연결합니다.
2. `b = a`는 같은 리스트에 이름 `b`도 연결합니다. 복제하지 않습니다.
3. `b.append(30)`은 두 이름이 함께 가리키는 리스트 자체를 변경합니다.
4. `b = [99]`는 새 리스트를 만들고 `b`의 연결만 바꿉니다. `a`는 그대로입니다.

```text
처음:       a ─┐
              ├→ [10, 20]
            b ─┘
재대입 후:  a ──→ [10, 20, 30]
            b ──→ [99]
```

### 변경과 재대입은 다르다

리스트의 `append`, 딕셔너리의 항목 대입은 객체 변경입니다. 변수에 `=`로 다른 객체를 연결하는 것은 재대입입니다. 정수·문자열·튜플은 불변 객체라서 객체 자체의 값을 바꿀 수 없습니다.

```python
def update(number, items):
    number += 1
    items.append("추가")
    items = ["함수 안의 새 리스트"]
    return number, items

n = 10
data = []
result = update(n, data)
print(n, data)
print(result)
```

```text
10 ['추가']
(11, ['함수 안의 새 리스트'])
```

매개변수도 같은 객체에 붙는 지역 이름입니다. `number += 1`은 새 정수를 지역 이름에 연결합니다. `items.append`는 공유 리스트를 변경합니다. 마지막 `items = ...`는 지역 이름만 재연결합니다. 함수에 전달한다고 무조건 복사되는 것은 아닙니다.

### `==`와 `is`

`==`는 값이 같은지, `is`는 같은 객체인지 비교합니다. 작은 정수나 문자열은 실행기가 객체를 재사용할 수 있으므로 `is`로 값 비교를 하지 않습니다. `None` 확인에는 `value is None`을 씁니다.

**확인 질문:** `a = [1]; b = [1]`에서 `a == b`는 참이고 `a is b`는 거짓인 이유는? 값이 같은 서로 다른 리스트를 만들었기 때문입니다.

## 3. 얕은 복사·깊은 복사와 중첩 자료구조

얕은 복사는 바깥 컨테이너를 새로 만들지만 안쪽 객체의 참조는 재사용합니다. 깊은 복사는 내부 객체를 재귀적으로 복사합니다. 단, 함수·클래스처럼 그대로 반환되는 객체 유형도 있으므로 모든 객체가 무조건 새 객체로 바뀐다는 뜻은 아닙니다.

```python
from copy import deepcopy
original = [[1], [2]]
shallow = original.copy()
deep = deepcopy(original)
print(shallow is original)
print(shallow[0] is original[0])
print(deep[0] is original[0])
original[0].append(9)
print(original)
print(shallow)
print(deep)
shallow.append([3])
assert len(original) == 2
assert len(shallow) == 3
```

```text
False
True
False
[[1, 9], [2]]
[[1, 9], [2]]
[[1], [2]]
```

`shallow.append([3])`는 새 바깥 리스트에만 항목을 더합니다. `shallow[0].append(...)`는 공유하는 안쪽 리스트를 바꿉니다. **어느 깊이의 객체를 바꾸는지**를 확인해야 합니다.

### 자주 하는 실수: 리스트 곱셈

```python
wrong = [[0] * 2] * 3
wrong[0][0] = 7
print(wrong)
right = [[0] * 2 for _ in range(3)]
right[0][0] = 7
print(right)
```

```text
[[7, 0], [7, 0], [7, 0]]
[[7, 0], [0, 0], [0, 0]]
```

첫 표현식은 한 행의 참조를 세 번 반복합니다. 두 번째는 반복마다 새 행을 만듭니다. 튜플 안에 리스트를 넣어도 그 리스트는 변경 가능합니다. 튜플의 불변성은 튜플 자체의 항목 연결을 바꾸지 못한다는 뜻입니다.

### 선택 기준

평평한 리스트에서 항목 추가·삭제만 독립적으로 하려면 얕은 복사로 충분할 수 있습니다. 중첩 데이터를 서로 독립적으로 편집하려면 깊은 복사를 고려합니다. 파일·소켓처럼 복제하기 어려운 자원을 포함하면 필요한 데이터만 새로 구성하세요. 깊은 복사에도 시간과 메모리가 들어갑니다.

[공식 문서: copy](https://docs.python.org/3.11/library/copy.html)

## 4. 함수 인자와 기본값의 생성 시점

매개변수는 함수 정의의 이름이고, 인자는 호출할 때 전달하는 값입니다. 위치 인자는 순서로, 키워드 인자는 이름으로 연결됩니다.

```python
def quote(price, /, quantity=1, *, discount=0):
    if price < 0 or quantity < 1:
        raise ValueError("가격은 0 이상, 수량은 1 이상이어야 합니다")
    if not 0 <= discount <= 100:
        raise ValueError("할인율은 0~100이어야 합니다")
    return price * quantity * (100 - discount) // 100

print(quote(1000, 2, discount=10))
print(quote(1000, quantity=3))
```

```text
1800
3000
```

| 구분 | 이 함수에서 | 의미 |
| --- | --- | --- |
| `/` 앞 | `price` | 위치로만 전달 |
| `/`와 `*` 사이 | `quantity` | 위치 또는 키워드로 전달 |
| `*` 뒤 | `discount` | 키워드로만 전달 |

`quote(price=1000)`이나 `quote(1000, 2, 10)`은 `TypeError`입니다. `/`와 `*`는 값을 받는 이름이 아니라 호출 규칙을 정하는 표시입니다.

### 가변 기본값이 호출 사이에 남는 이유

```python
def wrong_collect(value, bucket=[]):
    bucket.append(value)
    return bucket

print(wrong_collect(1))
print(wrong_collect(2))

def collect(value, bucket=None):
    if bucket is None:
        bucket = []
    bucket.append(value)
    return bucket

print(collect(1))
print(collect(2))
shared = []
assert collect(3, shared) is shared
```

```text
[1]
[1, 2]
[1]
[2]
```

기본값 표현식은 **호출할 때가 아니라 `def` 문이 실행될 때** 계산됩니다. 첫 함수는 리스트 하나를 계속 사용합니다. 두 번째는 인자가 생략된 호출마다 본문에서 새 리스트를 만듭니다. `bucket = bucket or []`는 사용자가 명시적으로 전달한 빈 리스트까지 새 객체로 바꾸므로 의도와 달라질 수 있습니다.

### 모으기와 펼치기: `*args`, `**kwargs`

```python
def total(*scores, bonus=0):
    return sum(scores) + bonus
scores = [70, 80]
options = {"bonus": 5}
print(total(*scores, **options))

def inspect(*args, **kwargs):
    print(args)
    print(kwargs)
inspect(1, 2, name="Kim")
```

```text
155
(1, 2)
{'name': 'Kim'}
```

정의에서 `*scores`는 남은 위치 인자를 모으고, 호출에서 `*scores`는 리스트를 여러 인자로 펼칩니다. `**`는 키워드에 대해 같은 관계입니다. 옵션이 정해져 있다면 명시적인 매개변수를 우선하세요. 모든 것을 `**kwargs`로 받으면 오타와 지원 옵션을 파악하기 어렵습니다.

[공식 문서: 함수 인자](https://docs.python.org/3.11/tutorial/controlflow.html#more-on-defining-functions)

## 5. 스코프와 LEGB — 이름은 어디에서 찾나

일반적인 함수에서 이름은 **Local → Enclosing → Global → Builtins** 순서로 찾습니다. 현재 함수, 바깥 함수, 현재 모듈, `len` 같은 내장 이름의 영역입니다. 클래스 본문 등에는 추가 규칙이 있으므로 모든 코드에 기계적으로 적용하지는 않습니다.

```python
label = "전역"
def outer():
    label = "바깥 함수"
    def inner():
        print(label)
    inner()
outer()
print(label)
```

```text
바깥 함수
전역
```

`inner`에 `label`이 없으므로 바깥 함수의 이름을 읽습니다. `outer`의 지역 이름은 전역 이름을 덮어쓰지 않습니다.

### 읽기와 대입은 다르다

```python
count = 10
def wrong():
    count += 1
try:
    wrong()
except UnboundLocalError:
    print("지역 변수에 값이 연결되기 전에 읽었습니다")

def better(count):
    return count + 1
count = better(count)
print(count)
```

```text
지역 변수에 값이 연결되기 전에 읽었습니다
11
```

함수 안에서 이름에 대입하면 보통 그 함수의 지역 이름으로 취급합니다. `count += 1`은 읽기와 대입을 모두 하므로 아직 값이 없는 지역 이름을 읽다가 실패합니다. `global count`를 선언하면 전역에 대입할 수 있지만 공유 상태가 늘어납니다. 입력을 받아 결과를 반환하면 테스트하기 쉽습니다.

`nonlocal`은 바깥 함수에 이미 존재하는 이름을 재대입할 때 사용합니다. `list = [...]`처럼 내장 이름을 변수명으로 쓰면 나중에 `list(...)`를 호출할 때 문제가 생길 수 있습니다.

**확인 질문:** 전역 리스트의 `append`를 호출할 때 항상 `global`이 필요한가? 아닙니다. 이름의 재대입이 아니라 객체 변경이기 때문입니다.

[공식 문서: 스코프](https://docs.python.org/3.11/tutorial/classes.html#python-scopes-and-namespaces)

## 6. 함수도 객체다 — 고차 함수와 클로저

함수는 변수에 저장하거나 다른 함수에 전달하거나 반환할 수 있습니다. **`func`는 함수 객체, `func()`는 호출 결과**입니다. 이 구분이 콜백·정렬 기준·데코레이터의 출발점입니다.

```python
def double(value):
    return value * 2
def apply(func, value):
    return func(value)
operation = double
print(apply(operation, 5))
students = [("Kim", 90), ("Lee", 80), ("Park", 95)]
print(sorted(students, key=lambda student: student[1], reverse=True))
```

```text
10
[('Park', 95), ('Kim', 90), ('Lee', 80)]
```

`apply(double, 5)`는 함수를 전달합니다. `apply(double(5), 5)`는 정수 10을 전달하므로 내부에서 호출하려다 실패합니다. `lambda`는 짧은 표현식 하나로 함수를 만듭니다. 조건과 설명이 길어지면 `def`로 이름을 붙이세요.

### 클로저의 생성과 호출을 따로 보기

```python
def make_multiplier(factor):
    def multiply(value):
        return value * factor
    return multiply

times_two = make_multiplier(2)
times_three = make_multiplier(3)
print(times_two(10))
print(times_three(10))
```

```text
20
30
```

1. `make_multiplier(2)`에서 지역 이름 `factor`가 2를 가리킵니다.
2. 내부 함수 `multiply`를 만들지만 그 본문은 아직 실행하지 않습니다.
3. `return multiply`로 함수 객체를 반환합니다. 괄호가 없다는 점이 중요합니다.
4. 반환된 함수는 자신이 사용할 바깥 변수의 연결을 유지합니다.
5. 나중에 `times_two(10)`을 호출하면 기억한 `factor`로 계산합니다.

이처럼 바깥 함수의 변수를 사용하는 내부 함수를 클로저라고 합니다. 바깥 함수의 실행이 끝나도 필요한 연결은 유지됩니다. 설정을 기억하는 작은 함수에 유용합니다.

### 상태를 바꾸는 클로저와 `nonlocal`

```python
def make_counter(start=0):
    count = start
    def increase():
        nonlocal count
        count += 1
        return count
    return increase

a = make_counter()
b = make_counter(100)
print(a(), a(), b(), a())
```

```text
1 2 101 3
```

`nonlocal count`는 새 지역 변수가 아니라 바깥 함수의 `count`를 재대입하겠다는 선언입니다. 두 번의 `make_counter` 호출은 별도의 상태를 만듭니다. 여러 메서드와 복잡한 상태가 필요하면 클래스로 바꾸는 편이 읽기 쉬울 수 있습니다.

## 7. 늦은 바인딩 — 만든 함수가 같은 값만 읽는 이유

클로저는 바깥 변수의 값을 무조건 사진처럼 복사하는 장치가 아닙니다. 해당 변수를 **함수 호출 시점에 읽는 경우**가 있어서 반복문과 결합하면 예상 밖의 결과가 나옵니다.

```python
wrong = []
for i in range(3):
    wrong.append(lambda: i)
print([func() for func in wrong])
fixed = []
for i in range(3):
    fixed.append(lambda i=i: i)
print([func() for func in fixed])
```

```text
[2, 2, 2]
[0, 1, 2]
```

첫 반복문은 “0을 반환하는 함수, 1을 반환하는 함수”가 아니라 “나중에 `i`를 읽는 함수” 세 개를 만듭니다. 호출 시점은 반복문이 끝난 뒤이고 그때 `i`는 2입니다. 두 번째의 기본값 `i=i`는 각 함수가 생성될 때 평가됩니다.

### 분명한 해결책: 팩터리 함수

```python
def make_reader(value):
    def read():
        return value
    return read
readers = [make_reader(i) for i in range(3)]
assert [read() for read in readers] == [0, 1, 2]
```

호출마다 별도의 `value`가 생깁니다. 버튼 콜백, 나중에 실행하는 작업, 반복문 안에서 등록하는 함수에 주의하세요. 기본값으로 리스트를 저장해도 그 리스트 자체는 이후에 바뀔 수 있습니다. 현재 참조를 저장하는 것과 데이터를 깊은 복사하는 것은 다릅니다.

**직접 바꾸기:** 6장의 `make_multiplier`로 2배·3배·4배 함수를 만들고 10에 적용하세요. 결과는 `[20, 30, 40]`이어야 합니다.

## 8. 데코레이터 — 기존 함수를 감싸서 기능 추가하기

여러 함수에 로그·시간 측정·권한 확인을 넣을 때 같은 코드를 반복하면 수정 지점이 늘어납니다. 데코레이터는 함수 객체를 받아 다른 함수 객체 등을 반환하여 공통 처리를 묶습니다.

```python
from functools import wraps

def trace(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print("시작:", func.__name__)
        result = func(*args, **kwargs)
        print("종료:", result)
        return result
    return wrapper

@trace
def add(a, b):
    """두 수를 더합니다."""
    return a + b

print(add(2, b=3))
assert add.__name__ == "add"
assert add.__doc__ == "두 수를 더합니다."
```

```text
시작: add
종료: 5
5
```

`@trace`는 정의 직후 `add = trace(add)`를 적용하는 것과 같습니다. 호출 시에는 래퍼가 실행되고, 클로저로 기억한 원래 함수를 호출합니다. `return result`를 빠뜨리면 `None`을 반환합니다. 원래 함수가 예외를 내면 “종료” 로그도 실행되지 않습니다. 성공 여부와 무관한 정리 작업은 `try/finally`를 사용해야 합니다.

`wraps`는 원래 이름·문서 등의 메타데이터와 `__wrapped__` 연결을 보존해 디버깅을 돕습니다. 잘못 작성한 래퍼의 동작까지 고쳐 주지는 않습니다.

### 옵션이 있는 데코레이터: 세 층의 역할

```python
from functools import wraps

def prefix(text):
    def decorate(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return text + func(*args, **kwargs)
        return wrapper
    return decorate

@prefix("안녕, ")
def greet(name):
    return name
print(greet("Python"))
```

```text
안녕, Python
```

`prefix("안녕, ")`는 설정을 기억하는 데코레이터를 만들고, `decorate(greet)`는 원래 함수를 기억하는 래퍼를 만듭니다. 실제 호출에서 래퍼 본문이 실행됩니다. 전체 적용은 `greet = prefix("안녕, ")(greet)`입니다.

### 중첩 순서와 사용 경계

`@outer` 아래에 `@inner`를 쓰면 적용은 `outer(inner(func))`입니다. 호출할 때는 바깥 래퍼부터 들어가므로 로그가 `outer 시작 → inner 시작 → 원래 함수 → inner 종료 → outer 종료`처럼 나올 수 있습니다. 권한 검사·캐시 순서도 동작에 영향을 줍니다.

결제·메일 발송 등에 무조건 재시도 데코레이터를 붙이면 중복 처리 위험이 있습니다. 또한 `async def`의 완료를 감싸려면 비동기 래퍼 안에서 `await func(...)`해야 합니다. 동기 래퍼는 코루틴 객체를 만드는 시간만 측정할 수 있습니다.

[공식 문서: wraps](https://docs.python.org/3.11/library/functools.html#functools.wraps)

## 9. 컴프리헨션·이터레이터·제너레이터 — 언제 계산하는가

### 일반 반복문에서 출발하기

```python
scores = [50, 80, 90]
passed = []
for score in scores:
    if score >= 60:
        passed.append(score + 5)
compact = [score + 5 for score in scores if score >= 60]
assert compact == passed == [85, 95]
```

컴프리헨션은 `for`로 값을 꺼내고, `if`로 남길 항목을 선택한 뒤, 앞쪽 표현식으로 결과를 만듭니다. 중첩이 많으면 일반 반복문으로 풀어 쓰세요. 출력·파일 쓰기 같은 부작용만을 위해 리스트를 만들지는 않습니다.

| 용어 | 의미 | 예 |
| --- | --- | --- |
| 이터러블 | `iter()`로 순회 도구를 얻는 객체 | 리스트, 문자열, `range` |
| 이터레이터 | `next()`로 다음 값을 꺼내는 객체 | `iter([1, 2])`, 파일 객체 |
| 제너레이터 | `yield`로 상태를 보존하는 이터레이터 | 제너레이터 함수 호출 결과 |

```python
values = [10, 20]
cursor = iter(values)
print(next(cursor))
print(next(cursor))
print(next(cursor, "끝"))
print(list(cursor))
print(list(values))
```

```text
10
20
끝
[]
[10, 20]
```

소비된 것은 리스트가 아니라 커서입니다. 리스트에서 새 커서를 얻으면 다시 읽을 수 있지만 같은 이터레이터는 처음으로 돌아가지 않습니다. 기본값 없는 `next(cursor)`는 끝에서 `StopIteration`을 냅니다. `for`는 이 신호를 처리하며 반복을 끝냅니다.

### `yield`는 실행을 잠시 멈춘다

```python
def squares(limit):
    print("본문 시작")
    for n in range(limit):
        print("계산:", n)
        yield n * n
stream = squares(3)
print("생성 완료")
print(next(stream))
print(next(stream))
print(list(stream))
print(list(stream))
```

```text
생성 완료
본문 시작
계산: 0
0
계산: 1
1
계산: 2
[4]
[]
```

호출 시에는 제너레이터 객체만 만들고 `next` 시점에 본문을 실행합니다. `yield`에서 값을 전달한 뒤 위치와 지역 상태를 보존합니다. 다음 요청에서 다음 줄부터 이어집니다. `return`은 제너레이터를 끝냅니다. 내부에서 종료를 위해 직접 `raise StopIteration`을 쓰지 않습니다.

### 지연 계산의 이점과 한계

`[n*n for n in range(...)]`는 결과를 즉시 리스트로 만들고, `(n*n for n in range(...))`는 요청받을 때 계산합니다. `sum(n*n for n in range(...))`은 중간 결과 리스트를 만들지 않습니다. 그러나 `list(generator)`는 결국 전체 결과를 메모리에 올립니다. 입력 변경이나 오류도 소비 시점에 드러날 수 있습니다.

```python
def flatten(rows):
    for row in rows:
        yield from row
assert list(flatten([[1, 2], [3]])) == [1, 2, 3]
names = ["Kim", "Lee"]
scores = [90]
try:
    list(zip(names, scores, strict=True))
except ValueError:
    print("이름과 점수의 개수가 다릅니다")
```

`yield from row`는 내부 iterable의 값을 차례대로 전달합니다. `zip`은 기본적으로 짧은 입력에서 멈추므로 길이가 같아야 하면 `strict=True`를 사용하세요. 이것도 실제로 소비할 때 불일치를 발견합니다.

[공식 문서: 이터레이터와 제너레이터](https://docs.python.org/3.11/tutorial/classes.html#iterators)

## 10. 클래스와 인스턴스 — 상태와 행동을 묶기

함수만으로 충분한 계산도 많지만, 장바구니처럼 상태와 관련 동작이 함께 움직이면 클래스로 묶는 것이 자연스럽습니다. 클래스는 객체의 동작을 정의하고, 인스턴스는 실제 개별 객체입니다. `self`는 메서드가 동작할 대상 인스턴스입니다.

```python
class Basket:
    currency = "KRW"

    def __init__(self, owner):
        self.owner = owner
        self.items = []

    def add(self, price):
        if type(price) is not int or price < 0:
            raise ValueError("가격은 0 이상의 정수여야 합니다")
        self.items.append(price)

    @property
    def total(self):
        return sum(self.items)

a = Basket("Kim")
b = Basket("Lee")
a.add(3000)
a.add(2000)
print(a.owner, a.total, a.currency)
print(b.owner, b.total)
assert a.items is not b.items
```

```text
Kim 5000 KRW
Lee 0
```

`Basket("Kim")`으로 인스턴스를 만들면 `__init__`이 초기 상태를 설정합니다. 엄밀히 말하면 객체 생성 자체는 `__new__`가 담당하고 `__init__`은 초기화입니다. 보통의 애플리케이션에서는 `__init__`부터 익히면 됩니다. `a.add(3000)`은 일반 인스턴스 메서드에서 `Basket.add(a, 3000)`에 대응합니다.

`@property`가 붙은 `total`은 `a.total`로 읽습니다. 호출할 때마다 합계를 계산하므로 별도 합계 필드와 항목 목록이 서로 어긋나는 문제를 줄입니다. 비싼 네트워크 호출처럼 예상하기 어려운 작업은 속성보다 명시적인 메서드로 표현하는 편이 좋습니다.

### 클래스 변수와 인스턴스 변수

`currency`는 클래스 변수입니다. 인스턴스에서 같은 이름을 따로 설정하지 않았다면 클래스의 값을 읽습니다. `self.items`는 인스턴스마다 만든 리스트입니다. 클래스 본문에 `items = []`를 두면 여러 인스턴스가 리스트를 공유할 수 있습니다.

```python
class WrongBasket:
    items = []
a = WrongBasket()
b = WrongBasket()
a.items.append(1000)
assert b.items == [1000]
```

인스턴스별 데이터는 대체로 `__init__`에서 만드세요. `_items`처럼 밑줄로 시작하는 이름은 내부 구현이라는 관례입니다. 외부 접근을 강제로 차단하는 보안 장치는 아닙니다.

### 인스턴스·클래스·정적 메서드

| 형태 | 자동으로 전달되는 것 | 주로 쓰는 상황 |
| --- | --- | --- |
| 일반 메서드 | `self` | 현재 인스턴스의 상태 읽기·수정 |
| `@classmethod` | `cls` | 다른 입력 형태로 객체를 만드는 대체 생성자 |
| `@staticmethod` | 없음 | 클래스에 관련 있지만 상태가 필요 없는 도우미 |

```python
class User:
    def __init__(self, name):
        self.name = name

    @classmethod
    def from_text(cls, text):
        return cls(text.strip())

    @staticmethod
    def valid_name(name):
        return bool(name.strip())

user = User.from_text(" Kim ")
assert user.name == "Kim"
assert User.valid_name(user.name)
```

`cls(...)`를 사용하면 상속받은 클래스에서 호출했을 때도 그 클래스로 생성할 수 있습니다. 도우미를 꼭 클래스 안에 넣을 필요는 없습니다. 관련성이 낮으면 모듈 함수로 두세요.

## 11. dataclass — 데이터 모델과 입력 검증

학생·좌표·설정처럼 필드가 중심인 객체에서 `__init__`, `__repr__`, `__eq__`를 반복 작성하기 번거롭습니다. `dataclass`는 필드 선언을 바탕으로 이런 메서드를 생성합니다.

```python
from dataclasses import dataclass, field

@dataclass
class Student:
    name: str
    scores: list[int] = field(default_factory=list)

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("이름은 비어 있지 않은 문자열이어야 합니다")
        self.name = self.name.strip()
        self.scores = list(self.scores)
        if any(type(score) is not int or not 0 <= score <= 100
               for score in self.scores):
            raise ValueError("점수는 0~100 정수여야 합니다")

a = Student(" Kim ")
b = Student("Lee")
a.scores.append(90)
print(a)
assert b.scores == []
assert a == Student("Kim", [90])
```

```text
Student(name='Kim', scores=[90])
```

- `default_factory=list`는 인스턴스를 생성할 때마다 `list()`를 호출합니다. `default_factory=list()`처럼 결과를 넘기면 안 됩니다.
- `__post_init__`은 생성된 초기화 메서드 뒤에 호출됩니다. 정리·검증을 넣을 수 있습니다.
- `list(self.scores)`는 호출자가 전달한 바깥 리스트와 분리합니다. 점수가 불변 정수이므로 이 예제에서는 얕은 복사로 충분합니다.
- 기본 동등 비교는 같은 클래스의 필드를 비교합니다. 모든 데이터 모델에 동일한 비교 의미가 적합한 것은 아닙니다.

검증은 여기서는 **생성 시점에만** 실행됩니다. 이후 `a.scores.append(999)`는 막지 못합니다. 지속적인 제약이 필요하면 변경 메서드에서 검증하거나 불변 구조를 사용하세요.

### `frozen=True`는 어디까지 막나

```python
from dataclasses import dataclass, FrozenInstanceError

@dataclass(frozen=True)
class Snapshot:
    name: str
    scores: tuple[int, ...]

snapshot = Snapshot("Kim", (90, 80))
try:
    snapshot.name = "Lee"
except FrozenInstanceError:
    print("필드 재대입 금지")
```

`frozen=True`는 일반적인 필드 재대입을 막습니다. 필드가 리스트라면 리스트 내부 변경까지 막지는 않습니다. 위처럼 내부도 불변인 자료를 사용하면 의도를 더 잘 지킬 수 있습니다. `slots=True`는 인스턴스의 속성 저장 방식을 제한하여 많은 객체에서 메모리를 줄일 수 있지만, 입력 검증 기능은 아닙니다. 필요를 측정한 뒤 선택하세요.

[공식 문서: dataclasses](https://docs.python.org/3.11/library/dataclasses.html)

## 12. 상속과 구성 — 관계를 먼저 생각하기

상속은 공통 동작을 확장하는 방법입니다. 그러나 코드 몇 줄을 재사용하려고 무조건 상속하면 부모 클래스 변경이 자식에게 영향을 주고 관계가 복잡해집니다. “같은 종류인가?”를 먼저 확인하세요.

```python
class Notification:
    def __init__(self, recipient):
        self.recipient = recipient

    def format(self, message):
        return f"{self.recipient}: {message}"

class UrgentNotification(Notification):
    def format(self, message):
        return "[긴급] " + super().format(message)

print(UrgentNotification("Kim").format("점검 예정"))
```

```text
[긴급] Kim: 점검 예정
```

`super()`는 메서드 탐색 순서(MRO)에서 다음 구현으로 위임합니다. 단순 상속에서는 부모 호출처럼 보이지만 다중 상속에서는 단순히 “부모 클래스 하나”를 뜻하지 않습니다. 다중 상속을 쓸 때는 각 클래스의 협력 방식과 인자 규칙까지 설계해야 합니다.

### 구성: 다른 객체를 가지고 일을 맡긴다

```python
class ConsoleSender:
    def send(self, message):
        print(message)

class ReportService:
    def __init__(self, sender):
        self.sender = sender

    def publish(self, title):
        self.sender.send(f"보고서: {title}")

ReportService(ConsoleSender()).publish("성적 분석")
```

```text
보고서: 성적 분석
```

보고서 서비스는 전송기의 한 종류가 아닙니다. 전송기를 **가지고 사용**합니다. 콘솔 대신 파일·메일 전송기로 교체해도 서비스의 보고서 처리 부분은 유지할 수 있습니다. 테스트에서는 메시지를 리스트에 모으는 가짜 전송기를 넣을 수 있습니다.

| 질문 | 우선 고려할 방법 |
| --- | --- |
| 기존 객체가 필요한 메서드를 이미 제공하는가? | 그대로 사용하거나 Protocol로 요구사항 표현 |
| 동작을 교체 가능한 부품으로 만들고 싶은가? | 구성과 의존성 전달 |
| 부모 대신 사용해도 의미가 일관적인 같은 종류인가? | 상속 검토 |

## 13. 특수 메서드와 Python 데이터 모델

`len(obj)`, `for x in obj`, `obj[key]` 같은 문법은 객체의 정해진 특수 메서드와 연결됩니다. 특수 메서드를 사용하면 자신이 만든 클래스도 Python의 기본 도구와 자연스럽게 결합됩니다.

```python
class ScoreBook:
    def __init__(self, scores):
        self._scores = tuple(scores)

    def __len__(self):
        return len(self._scores)

    def __iter__(self):
        return iter(self._scores)

    def __getitem__(self, index):
        return self._scores[index]

    def __repr__(self):
        return f"ScoreBook({self._scores!r})"

book = ScoreBook([80, 90, 100])
print(len(book), book[0], sum(book))
print(book)
assert list(book) == [80, 90, 100]
```

```text
3 80 270
ScoreBook((80, 90, 100))
```

`__iter__`는 호출할 때마다 새 이터레이터를 돌려주므로 `book`을 여러 번 순회할 수 있습니다. 객체 자체가 커서인 이터레이터를 구현한다면 `__iter__`가 자신을 반환하고 `__next__`가 진행 상태를 관리합니다. 컨테이너와 커서를 섞으면 예상치 못한 재순회 문제가 생깁니다.

`__repr__`는 개발자가 상태를 파악하기 위한 표현, `__str__`는 사용자에게 보여 줄 문자열 표현입니다. `__str__`이 없으면 `print`에서 `__repr__`를 사용할 수 있습니다. `!r`는 해당 값의 `repr` 표현을 넣습니다.

### 동등 비교와 해시

딕셔너리 키·집합 원소는 해시 가능해야 합니다. 같은 값으로 비교되는 두 객체는 같은 해시를 가져야 하며, 키로 쓰는 동안 해시와 비교에 사용하는 상태가 안정적이어야 합니다. 리스트·딕셔너리는 가변이라 해시 불가능합니다. 튜플도 안에 해시 불가능한 항목이 있으면 키로 쓸 수 없습니다.

`__eq__`만 직접 바꾸고 `__hash__` 관계를 고려하지 않으면 집합·딕셔너리 사용에서 문제가 생깁니다. 단순한 불변 데이터라면 `frozen=True`인 dataclass와 불변 필드를 우선 검토하세요. 다만 필드가 실제로 해시 가능한지는 별도로 확인해야 합니다.

[공식 문서: 데이터 모델](https://docs.python.org/3.11/reference/datamodel.html)

## 14. 예외 처리 — 실패를 숨기지 않고 다루기

예외는 정상 결과를 반환할 수 없는 상황을 호출자에게 알리는 수단입니다. “값이 없다”를 뜻하는 `None`과 “계산 자체가 실패했다”는 예외를 구분해야 호출자가 올바르게 대응할 수 있습니다.

```python
def parse_score(text):
    try:
        score = int(text)
    except ValueError as exc:
        raise ValueError("점수는 정수 문자열이어야 합니다") from exc
    else:
        if not 0 <= score <= 100:
            raise ValueError("점수 범위는 0~100입니다")
        return score
    finally:
        print("파싱 시도 종료")

print(parse_score("90"))
try:
    parse_score("abc")
except ValueError as exc:
    print(exc)
    assert isinstance(exc.__cause__, ValueError)
```

```text
파싱 시도 종료
90
파싱 시도 종료
점수는 정수 문자열이어야 합니다
```

| 구문 | 실행 조건 | 역할 |
| --- | --- | --- |
| `try` | 먼저 실행 | 실패 가능성이 있는 좁은 범위 |
| `except` | 맞는 예외 발생 | 회복·변환·안내 |
| `else` | `try`가 예외 없이 종료 | 성공 후속 처리 |
| `finally` | 블록을 벗어나는 정상·예외 경로 | 자원 정리 |

`else`의 코드는 앞의 `except`가 잡지 않습니다. `raise ... from exc`는 사용자에게 더 의미 있는 메시지를 주면서 원인 연결을 유지합니다. 같은 예외를 그대로 다시 전달하려면 `raise`만 씁니다. `finally`에 `return`을 넣으면 기존 반환값이나 예외를 덮어쓸 수 있으므로 피하세요. 프로세스 강제 종료까지 정리를 보장한다는 뜻도 아닙니다.

### 어떤 예외를 어디에서 잡을까

변환 함수는 잘못된 데이터를 감지해 예외를 내고, 사용자 인터페이스는 그 예외를 잡아 안내할 수 있습니다. 처리가 불가능한 계층에서 무조건 잡으면 실패가 숨겨집니다. `except Exception: pass`는 데이터 누락을 정상 결과처럼 보이게 만들 수 있습니다. 반대로 너무 넓은 `try`는 의도하지 않은 코드의 버그까지 같은 입력 오류로 오해하게 합니다.

사용자 정의 예외는 `class InvalidScore(ValueError): pass`처럼 의미를 붙일 때 유용합니다. `KeyboardInterrupt`, `SystemExit`, `asyncio.CancelledError` 등은 일반적인 `Exception` 처리와 구분해야 합니다. `BaseException` 전체를 습관적으로 잡지 않습니다.

[공식 문서: 오류와 예외](https://docs.python.org/3.11/tutorial/errors.html)

## 15. 컨텍스트 매니저 — 시작과 정리를 한 쌍으로

파일을 열고 닫는 코드에서 중간에 예외가 나면 닫기 호출을 건너뛸 수 있습니다. `with`는 자원을 사용하는 범위를 표시하고, 그 범위를 벗어날 때 정리하도록 만듭니다.

```python
from contextlib import contextmanager
from io import StringIO

@contextmanager
def text_buffer(text):
    buffer = StringIO(text)
    print("준비")
    try:
        yield buffer
    finally:
        buffer.close()
        print("정리")

try:
    with text_buffer("90") as buffer:
        print(buffer.read())
        raise ValueError("중간 실패")
except ValueError:
    print("호출자가 오류 처리")
assert buffer.closed
```

```text
준비
90
정리
호출자가 오류 처리
```

1. `with`에 들어갈 때 제너레이터를 `yield`까지 실행합니다.
2. `yield buffer`의 값이 `as buffer`에 연결됩니다.
3. `with` 본문을 실행합니다.
4. 정상 종료하면 `yield` 다음으로 진행합니다. 예외가 나면 `yield` 지점에 예외가 전달됩니다.
5. `finally`에서 정리하고, 처리되지 않은 예외는 호출자에게 전달합니다.

`@contextmanager` 함수는 정확히 한 번 `yield`해야 합니다. 예외를 잡은 뒤 다시 내보내지 않으면 예외를 처리한 것으로 간주될 수 있습니다. 단순히 정리하려는 목적이면 `try/finally`를 사용하세요.

실제 파일은 `with open(path, encoding="utf-8") as file:`로 다룹니다. 클래스 형태에서는 `__enter__`, `__exit__`를 구현하며, `__exit__`가 참인 값을 반환하면 예외가 억제됩니다. `with`가 모든 작업을 자동으로 되돌리는 것은 아닙니다. 파일 닫기와 데이터베이스 롤백은 서로 다른 책임입니다.

**제너레이터와 결합할 때:** 파일을 읽는 제너레이터 내부에서 `with`를 사용하면 제너레이터가 멈춰 있는 동안 파일도 열려 있을 수 있습니다. 조기에 순회를 중단할 가능성이 있으면 호출자가 파일 범위를 소유하거나 명시적으로 제너레이터를 닫는 방식을 고려하세요. 22장의 프로젝트는 파일 범위를 호출자가 소유합니다.

[공식 문서: contextlib](https://docs.python.org/3.11/library/contextlib.html)

## 16. 타입 힌트·제네릭·Protocol

타입 힌트는 개발 도구와 사람이 입력·출력의 계약을 이해하도록 돕습니다. **Python 실행기가 자동으로 타입을 강제하지는 않습니다.** 정적 검사는 실행 전에 코드 관계를 검사하고, 실행 시 검증은 실제 외부 데이터를 검사합니다. 둘 다 필요할 수 있습니다.

```python
def add_one(value: int) -> int:
    return value + 1

assert add_one(3) == 4
assert add_one(2.5) == 3.5  # 힌트와 달라도 실행 자체는 허용
```

정적 검사기는 마지막 호출을 지적할 수 있지만 실행기는 힌트 때문에 거부하지 않습니다. `int("abc")` 같은 오류는 타입 힌트가 아니라 실제 연산에서 생깁니다.

| 표기 | 뜻 | 주의 |
| --- | --- | --- |
| `list[int]` | 정수 항목 리스트 | 항목을 자동 검증하지 않음 |
| `str \| None` | 문자열 또는 None | 사용 전 None 여부 확인 |
| `tuple[int, ...]` | 길이 제한 없는 정수 튜플 | `...`는 반복되는 항목 타입 |
| `Any` | 정적 검사에서 다양한 사용 허용 | 과용하면 검사 효과 감소 |
| `object` | 어떤 객체든 받을 수 있음 | 사용할 연산은 타입을 좁혀야 함 |

### 제네릭은 입력과 출력 타입의 관계를 보존한다

```python
from collections.abc import Sequence
from typing import TypeVar
T = TypeVar("T")

def first(values: Sequence[T]) -> T | None:
    return values[0] if values else None

assert first([10, 20]) == 10
assert first(("a", "b")) == "a"
assert first([]) is None
```

`T`는 호출에 따라 달라지는 타입을 나타냅니다. 정수 시퀀스를 넣으면 정수 또는 None, 문자열 시퀀스를 넣으면 문자열 또는 None을 돌려준다는 관계를 표현합니다. `Sequence`는 길이와 인덱스 접근이 가능한 계약입니다. 단순 순회만 필요하면 `Iterable`처럼 더 넓은 계약을 사용할 수 있습니다.

### Protocol은 필요한 행동으로 호환성을 표현한다

```python
from typing import Protocol

class Sender(Protocol):
    def send(self, message: str) -> None: ...

class MemorySender:
    def __init__(self):
        self.messages: list[str] = []
    def send(self, message: str) -> None:
        self.messages.append(message)

def notify(sender: Sender, message: str) -> None:
    sender.send(message)

sender = MemorySender()
notify(sender, "완료")
assert sender.messages == ["완료"]
```

`MemorySender`는 `Sender`를 명시적으로 상속하지 않아도 필요한 메서드 형태가 맞으면 정적 검사에서 호환됩니다. “어느 부모를 상속했나”보다 “어떤 행동이 필요한가”를 표현합니다. 일반 Protocol을 곧바로 `isinstance`에 사용할 수는 없습니다. `@runtime_checkable`도 멤버 존재 여부를 확인하는 제한된 검사이며 완전한 타입·서명 검증은 아닙니다.

정적 검사를 추가하고 싶으면 가상환경에 mypy 같은 도구를 설치한 뒤 검사할 수 있습니다. 이 과정의 실행 예제에는 별도 설치가 필요하지 않습니다. 외부 JSON·CSV·API 입력에는 타입 힌트와 별개로 실제 값 검증을 작성하세요.

[공식 문서: typing](https://docs.python.org/3.11/library/typing.html)

## 17. 표준 라이브러리 — 직접 구현하기 전에 찾기

### 빈도와 그룹화

```python
from collections import Counter, defaultdict, deque

counts = Counter(["A", "B", "A", "C", "A"])
print(counts.most_common(2))
print(counts["없는 등급"])
groups = defaultdict(list)
for name, team in [("Kim", "A"), ("Lee", "A"), ("Park", "B")]:
    groups[team].append(name)
print(dict(groups))
queue = deque(["첫 작업", "두 번째 작업"])
print(queue.popleft())
```

```text
[('A', 3), ('B', 1)]
0
{'A': ['Kim', 'Lee'], 'B': ['Park']}
첫 작업
```

`Counter`는 수량을 세고, `defaultdict(list)`는 처음 만난 키의 리스트를 만들어 줍니다. `groups[missing]` 조회 자체가 새 키를 만들 수 있지만 `groups.get(missing)`은 기본 팩터리를 호출하지 않습니다. 큐에서 앞쪽을 반복 제거할 때 리스트의 `pop(0)`은 나머지 항목을 이동시킵니다. `deque.popleft()`는 이런 사용에 적합합니다.

### 캐시: 같은 계산을 다시 하지 않기

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def square(number):
    print("실제 계산:", number)
    return number * number

print(square(4))
print(square(4))
assert square.cache_info().hits == 1
square.cache_clear()
```

```text
실제 계산: 4
16
16
```

캐시는 입력을 키로 결과를 저장합니다. 인자는 해시 가능해야 하므로 리스트는 그대로 넘길 수 없습니다. 파일 내용·현재 시간·외부 API처럼 결과가 바뀌는 함수를 캐시하면 오래된 값을 돌려줄 수 있습니다. 반환값이 가변 객체이면 호출자들이 같은 객체를 받아 변경을 공유할 수 있습니다. `async def`에 일반 `lru_cache`를 붙이면 완료 결과 대신 코루틴 객체가 캐시되므로 적합하지 않습니다.

### 파일 경로와 데이터 형식

`pathlib.Path`는 경로 결합·파일 읽기를 표현하고, `json`은 JSON 구조 변환, `csv`는 구분자·따옴표가 있는 행을 처리합니다. CSV를 단순 `split(",")`로 나누면 `"Kim, Jr"`처럼 값 안에 쉼표가 있을 때 깨집니다. CSV 파일은 `newline=""`, 텍스트는 명시적인 인코딩을 사용하세요. 이 도구들은 22장의 통합 프로젝트에서 연결합니다.

[collections](https://docs.python.org/3.11/library/collections.html) · [functools](https://docs.python.org/3.11/library/functools.html) · [csv](https://docs.python.org/3.11/library/csv.html)

## 18. match 패턴 매칭과 데이터 검증

`if`가 조건의 참·거짓을 검사한다면 `match`는 값의 **구조를 분해하면서** 분기할 수 있습니다. 명령 딕셔너리나 이벤트처럼 구조가 여러 종류일 때 유용합니다.

```python
def command(payload):
    match payload:
        case {"action": "add", "value": int(value)} if not isinstance(value, bool):
            return value + 1
        case {"action": "quit"}:
            return None
        case _:
            raise ValueError("지원하지 않는 명령 또는 잘못된 값")

print(command({"action": "add", "value": 4}))
print(command({"action": "quit"}))
for invalid in [{"action": "add", "value": True}, {"action": "add", "value": "4"}]:
    try:
        command(invalid)
    except ValueError:
        print("거부")
```

```text
5
None
거부
거부
```

- 매핑 패턴은 해당 키가 있는지와 그 값의 형태를 확인합니다. 지정하지 않은 추가 키는 허용합니다.
- `int(value)`는 여기서 변환 함수 호출이 아니라 **클래스 패턴**입니다. 정수와 호환되는 값을 매칭하고 이름 `value`로 받습니다. 문자열 `"4"`를 정수로 바꾸지 않습니다.
- `bool`은 `int`의 하위 타입이므로 추가 가드 `if not isinstance(value, bool)`로 제외합니다.
- 위에서 아래로 검사하여 처음 맞는 `case`를 실행합니다. `_`는 나머지를 받는 와일드카드입니다.

### 실수하기 쉬운 캡처 패턴

`case expected:`는 대체로 `expected`라는 상수와 비교하는 것이 아니라 값을 새 이름으로 받는 캡처입니다. 특정 문자열은 `case "quit":`, Enum 등은 `case Action.QUIT:`처럼 작성합니다. 같은 키와 값 비교만 하는 간단한 조건이라면 `if/elif`가 더 분명할 수도 있습니다. 패턴 매칭이 전체 입력 스키마 검증을 대신한다고 생각하지 마세요.

[공식 문서: match](https://docs.python.org/3.11/tutorial/controlflow.html#match-statements)

## 19. 모듈·패키지·실행 진입점

코드가 커지면 데이터를 정의하는 부분, 데이터를 읽는 부분, 사용자와 상호작용하는 부분을 분리합니다. 모듈은 보통 Python 파일 하나이고, 일반 패키지는 모듈을 묶은 디렉터리입니다. 아래는 구조 예시이며 각 파일은 함께 사용합니다.

```text
project/
├── score_app/
│   ├── __init__.py
│   ├── models.py       # Student 같은 데이터 모델
│   ├── service.py      # 분석 규칙
│   └── __main__.py     # 명령행 진입점
└── tests/
    └── test_service.py
```

`project` 폴더에서 `python -m score_app`을 실행하면 `score_app/__main__.py`가 실행됩니다. 패키지 안에서는 `from .models import Student`처럼 상대 import를 사용할 수 있습니다. 상대 import가 있는 파일을 `python score_app/service.py`처럼 직접 실행하면 패키지 맥락을 잃을 수 있으므로 `-m` 방식과 진입점을 일관되게 정하세요.

### import할 때 실행되는 것

```python
from pathlib import Path

def main():
    directory = Path(__file__).resolve().parent
    print("스크립트 폴더:", directory)

if __name__ == "__main__":
    main()
```

이 예제는 파일에 저장해 실행하세요. 직접 실행하면 `__name__`이 `"__main__"`이므로 `main()`을 호출합니다. 다른 모듈에서 import하면 함수는 정의되지만 진입점 호출은 하지 않습니다. 대화형 환경에서는 `__file__`이 없을 수 있습니다.

import는 최초 로딩 때 모듈 최상위 코드를 실행하고 일반적으로 같은 프로세스의 이후 import에서는 캐시된 모듈을 사용합니다. 최상위에 서버 실행·파일 변경·긴 계산을 넣으면 import만 해도 부작용이 발생합니다. 진입점 아래에 실행을 모으고, 핵심 계산은 호출 가능한 함수로 분리하세요.

`json.py`, `typing.py`, `asyncio.py` 같은 파일명은 표준 라이브러리를 가릴 수 있습니다. 프로젝트에서 import 오류가 나면 파일명·실행 폴더·선택된 Python 환경을 먼저 확인합니다. 순환 import는 두 모듈이 서로를 로딩하다 초기화가 덜 된 이름을 읽는 문제를 만들 수 있습니다. 공통 모델을 별도 모듈로 옮기거나 의존 방향을 단순하게 만드세요.

[공식 문서: 모듈](https://docs.python.org/3.11/tutorial/modules.html)

## 20. async·await — 대기 시간을 겹쳐 쓰기

### 동시성과 병렬성부터 구분하기

동시성은 여러 작업의 진행을 겹쳐 관리하는 것이고, 병렬성은 같은 순간에 여러 작업을 실제로 실행하는 것입니다. 하나의 이벤트 루프는 작업이 I/O를 기다리는 동안 다른 작업을 진행할 수 있습니다. CPU 계산을 자동으로 여러 코어에 나눠 주지는 않습니다.

식당 비유로 보면 동기 실행은 주문 하나의 조리가 끝날 때까지 다음 주문을 기다리는 방식입니다. 비동기는 조리를 기다리는 동안 다음 주문을 받는 방식입니다. 요리사를 여러 명 두는 병렬성과는 구분됩니다.

### 코루틴 함수·객체·태스크

| 용어 | 생성 방법 | 의미 |
| --- | --- | --- |
| 코루틴 함수 | `async def work()` | 비동기 실행 절차의 정의 |
| 코루틴 객체 | `work()` | 아직 실행 완료되지 않은 절차 객체 |
| 태스크 | `create_task(...)` 등 | 이벤트 루프에 실행을 예약한 코루틴 |
| `await` | `await work()` | 완료를 기다리며 필요하면 실행권 양보 |

`async def`를 호출했다고 함수 본문이 곧바로 실행되는 것은 아닙니다. 기다리지도 예약하지도 않은 코루틴은 실행되지 않고 경고가 날 수 있습니다. `await`가 언제나 다른 작업으로 전환된다는 뜻도 아닙니다. 이미 완료된 결과는 즉시 이어질 수 있습니다.

### 순차 await와 동시 예약

```python
import asyncio

async def fetch(name):
    print("시작", name)
    await asyncio.sleep(0.02)
    print("완료", name)
    return name

async def main():
    print("순차")
    sequential = [await fetch("A"), await fetch("B")]
    print("동시")
    async with asyncio.TaskGroup() as group:
        a = group.create_task(fetch("A"))
        b = group.create_task(fetch("B"))
    assert sequential == [a.result(), b.result()] == ["A", "B"]

if __name__ == "__main__":
    asyncio.run(main())
```

순차 부분은 반드시 `시작 A → 완료 A → 시작 B → 완료 B`입니다. 동시 부분은 A와 B가 각각 대기하며 진행을 겹칩니다. 흔히 두 “시작”이 두 “완료”보다 먼저 출력되지만 완료 순서에 의존하는 코드를 작성하지 마세요. 위처럼 결과를 입력 순서의 태스크 참조로 모으면 완료 순서와 구분할 수 있습니다.

두 요청이 각각 약 0.02초를 기다린다면 순차 대기는 약 0.04초, 겹친 대기는 약 0.02초에 추가 실행 비용이 더해집니다. 이는 구조 설명용 근사치이며 실제 시간은 환경·외부 서비스에 따라 달라집니다.

### TaskGroup의 실패와 취소

```python
import asyncio

async def fail():
    await asyncio.sleep(0)
    raise ValueError("잘못된 응답")

async def main():
    try:
        async with asyncio.TaskGroup() as group:
            group.create_task(fail())
            group.create_task(asyncio.sleep(1))
    except* ValueError as group_error:
        print("입력 오류 수:", len(group_error.exceptions))

asyncio.run(main())
```

```text
입력 오류 수: 1
```

그룹을 벗어날 때 작업 완료를 기다립니다. 일반적인 작업 실패가 발생하면 나머지 작업을 취소하고 정리가 끝날 때까지 기다린 뒤 실패들을 예외 그룹으로 전달합니다. `except*`는 그룹 안의 해당 유형 예외를 처리합니다. `KeyboardInterrupt`·`SystemExit` 등에는 별도 규칙이 있습니다. 한 `try`에서 일반 `except`와 `except*`를 함께 쓰지 않습니다.

취소는 작업에 중단 요청을 보내는 협력적 절차입니다. 자원 정리는 `try/finally`로 작성하고, `CancelledError`를 잡았다면 보통 정리 후 다시 전달해야 합니다. 이를 삼키면 그룹이나 타임아웃이 기대대로 종료되지 않을 수 있습니다.

### 타임아웃과 동시 작업 수 제한

```python
import asyncio

async def main():
    limit = asyncio.Semaphore(2)

    async def fetch(number):
        async with limit:
            await asyncio.sleep(0.01)
            return number * 10

    async with asyncio.timeout(1):
        async with asyncio.TaskGroup() as group:
            tasks = [group.create_task(fetch(n)) for n in range(5)]
    print([task.result() for task in tasks])

asyncio.run(main())
```

```text
[0, 10, 20, 30, 40]
```

세마포어는 보호 구간에 동시에 들어가는 작업을 최대 2개로 제한합니다. 모든 태스크 생성 수 자체를 줄이는 것은 아니므로 수백만 항목에는 큐·작업자 방식도 고려합니다. 제한 시간이 지나면 `asyncio.timeout` 바깥에서 `TimeoutError`를 처리할 수 있습니다. 타임아웃은 외부 시스템의 부작용까지 되돌리거나 모든 스레드를 강제 종료한다는 뜻이 아닙니다.

### 자주 하는 실수

- `await fetch("A"); await fetch("B")`만 쓰고 병렬로 실행됐다고 생각하기: 예약을 겹치지 않았습니다.
- 비동기 함수 안에서 `time.sleep()` 사용하기: 이벤트 루프 스레드를 막습니다. 대기에는 `await asyncio.sleep()`을 씁니다.
- 긴 동기 I/O를 그대로 호출하기: 적절한 비동기 라이브러리나 `await asyncio.to_thread(...)`를 검토합니다. 스레드 작업의 취소에는 한계가 있습니다.
- 노트북에서 `asyncio.run()` 중첩하기: 이미 이벤트 루프가 실행 중이면 최상위에서 `await main()`을 사용합니다.
- 코루틴 객체를 두 번 await하기: 코루틴을 다시 생성하거나 여러 번 기다릴 수 있는 태스크의 결과를 사용해야 합니다.

[공식 문서: 코루틴·태스크·취소·타임아웃](https://docs.python.org/3.11/library/asyncio-task.html)

## 21. 성능·스레드·프로세스 — 도구를 고르는 기준

성능은 문법이 짧다고 좋아지는 것이 아닙니다. 먼저 입력 크기와 연산 횟수, 그다음 I/O 대기·메모리·객체 생성 비용을 봅니다. 작은 입력에서 빠른 코드가 큰 입력에서도 빠르다는 보장은 없습니다.

| 상황 | 우선 검토 | 이유와 한계 |
| --- | --- | --- |
| 보통의 순차 작업 | 일반 함수 | 가장 단순하고 추적하기 쉬움 |
| 비동기 API의 많은 I/O 대기 | asyncio | 대기를 겹치지만 이벤트 루프를 막으면 효과 감소 |
| 기존 동기 I/O 함수의 병행 실행 | 스레드 풀 | 호환성이 좋지만 공유 상태·작업 수 관리 필요 |
| Python 코드 중심의 큰 CPU 계산 | 프로세스 풀 | 여러 프로세스 실행, 직렬화·시작 비용 발생 |
| 중간 결과가 매우 큼 | 제너레이터 | 중간 리스트를 줄이지만 최종 수집 시 메모리 사용 |
| 같은 순수 계산 반복 | 캐시 | 재계산 감소, 메모리와 오래된 결과 문제 고려 |

일반적인 GIL 활성 CPython에서는 여러 스레드가 Python 바이트코드를 동시에 실행하는 데 제약이 있습니다. 다만 I/O나 GIL을 해제하는 확장 라이브러리, free-threaded 빌드 등은 다르게 동작할 수 있습니다. “Python은 어떤 환경에서도 스레드 병렬 실행이 불가능하다”로 일반화하지 마세요.

프로세스 풀은 전달하는 함수·데이터의 직렬화 가능성, 큰 데이터 복사 비용을 확인해야 합니다. 특히 생성 방식에 따라 자식 프로세스가 모듈을 다시 불러올 수 있으므로 `if __name__ == "__main__":` 진입점 보호가 중요합니다.

### 알고리즘 개선이 먼저인 예

```python
allowed_list = [10, 20, 30]
allowed_set = set(allowed_list)
queries = [20, 99, 10]
assert [q in allowed_list for q in queries] == [q in allowed_set for q in queries]
```

리스트 검색은 최악에 항목 전체를 확인합니다. 집합 검색은 일반적인 해시 조건에서 평균적으로 빠르지만 집합 생성과 메모리 비용이 있습니다. 한 번만 검색한다면 변환 비용이 더 클 수도 있습니다. 성능 설명에는 평균·최악·준비 비용을 구분하세요.

`time.perf_counter()`로 구간 시간을 재고, 작은 연산 비교는 `timeit`, 전체 프로그램의 병목은 `cProfile`로 확인할 수 있습니다. 여러 번 측정하고 같은 입력·환경에서 비교하세요. 0.001초 차이 하나를 근거로 설계를 복잡하게 만들지 않습니다.

[공식 문서: 스레딩과 GIL](https://docs.python.org/3/library/threading.html#gil-and-performance-considerations) · [concurrent.futures](https://docs.python.org/3.11/library/concurrent.futures.html) · [timeit](https://docs.python.org/3.11/library/timeit.html)

## 22. 통합 프로젝트 — CSV 성적 분석기

앞에서 배운 기능을 연결해 **CSV 읽기 → 행 검증 → 학생 객체 생성 → 통계 집계 → JSON 보고서 저장** 프로그램을 만듭니다. 웹 계정·외부 패키지 없이 실행할 수 있습니다.

### 목표와 설계

CSV 컬럼은 `name,team,score`입니다. 이름·팀은 비어 있으면 안 되고, 점수는 0~100 정수입니다. 잘못된 행을 만나면 줄 번호를 포함한 예외를 내며 보고서를 저장하지 않습니다. 빈 데이터는 인원 0, 평균 `null`, 합격자 빈 목록으로 표현합니다. 평균을 무조건 0으로 두면 “학생이 없다”와 “학생들의 평균이 0이다”를 구분할 수 없기 때문입니다.

| 역할 | 사용 개념 | 분리 이유 |
| --- | --- | --- |
| `Student` | frozen dataclass, property | 검증된 한 학생의 상태 표현 |
| `read_students` | csv, generator, 예외 연결 | 읽기·변환 실패 위치 추적 |
| `summarize` | Iterable, Counter, defaultdict | 파일 없이도 통계 테스트 가능 |
| `analyze_file` | Path, with | 파일 자원 범위를 명확히 소유 |
| `main` | argparse, JSON, 진입점 | 사용자 입력·출력을 핵심 규칙과 분리 |

실습 파일은 [성적 분석기](sample-files/python-advanced/analyzer.py), [테스트](sample-files/python-advanced/test_analyzer.py), [샘플 CSV](sample-files/python-advanced/students.csv), [실행 안내](sample-files/python-advanced/README.md)에서 받을 수 있습니다. **이 장과 다음 장은 서로 함께 사용하는 파일 예제**입니다. 나머지 짧은 예제와 달리 테스트는 `analyzer.py`가 같은 폴더에 있어야 합니다.

### 전체 코드: analyzer.py

```python
import argparse
import csv
import json
from collections import Counter, defaultdict
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO


class InvalidRow(ValueError):
    """CSV 형식 또는 행의 값이 잘못되었습니다."""


@dataclass(frozen=True)
class Student:
    name: str
    team: str
    score: int

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("이름은 비어 있지 않은 문자열이어야 합니다")
        if not isinstance(self.team, str) or not self.team.strip():
            raise ValueError("팀은 비어 있지 않은 문자열이어야 합니다")
        if type(self.score) is not int or not 0 <= self.score <= 100:
            raise ValueError("점수는 0~100 정수여야 합니다")

    @property
    def grade(self) -> str:
        if self.score >= 90:
            return "A"
        if self.score >= 80:
            return "B"
        if self.score >= 60:
            return "C"
        return "F"


def read_students(source: TextIO) -> Iterator[Student]:
    reader = csv.DictReader(source, strict=True)
    try:
        if reader.fieldnames != ["name", "team", "score"]:
            raise InvalidRow("헤더는 name,team,score 순서여야 합니다")
        for row in reader:
            try:
                if None in row or any(value is None for value in row.values()):
                    raise ValueError("컬럼 개수가 다릅니다")
                yield Student(
                    name=row["name"].strip(),
                    team=row["team"].strip(),
                    score=int(row["score"]),
                )
            except (TypeError, ValueError) as exc:
                raise InvalidRow(f"{reader.line_num}행: {exc}") from exc
    except csv.Error as exc:
        raise InvalidRow(f"{reader.line_num}행: CSV 형식 오류: {exc}") from exc


def summarize(students: Iterable[Student]) -> dict[str, object]:
    count = 0
    total = 0
    grades: Counter[str] = Counter()
    teams: defaultdict[str, int] = defaultdict(int)
    passed: list[str] = []
    for student in students:
        count += 1
        total += student.score
        grades[student.grade] += 1
        teams[student.team] += 1
        if student.score >= 60:
            passed.append(student.name)
    return {
        "count": count,
        "average": round(total / count, 2) if count else None,
        "grades": dict(sorted(grades.items())),
        "teams": dict(sorted(teams.items())),
        "passed": passed,
    }


def analyze_file(path: Path) -> dict[str, object]:
    with path.open(encoding="utf-8-sig", newline="") as source:
        return summarize(read_students(source))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CSV 성적 분석기")
    parser.add_argument("input", type=Path, help="입력 CSV 경로")
    parser.add_argument("--output", type=Path, default=Path("report.json"))
    args = parser.parse_args(argv)
    try:
        report = analyze_file(args.input)
        text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        args.output.write_text(text, encoding="utf-8")
    except (OSError, UnicodeError, InvalidRow) as exc:
        parser.exit(2, f"오류: {exc}\n")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

### 실행하기

위 파일들과 CSV를 같은 폴더에 저장하고 그 폴더에서 실행합니다. 입력 CSV는 다음과 같습니다.

```csv
name,team,score
Kim,A,90
Lee,A,80
Park,B,50
```

```bash
python analyzer.py students.csv --output report.json
python -m unittest -v
```

터미널 출력과 `report.json` 내용:

```json
{
  "count": 3,
  "average": 73.33,
  "grades": {
    "A": 1,
    "B": 1,
    "F": 1
  },
  "teams": {
    "A": 2,
    "B": 1
  },
  "passed": [
    "Kim",
    "Lee"
  ]
}
```

### 한 행이 처리되는 과정을 추적하기

1. `main`이 입력 경로를 받고 `analyze_file`을 호출합니다.
2. `with`가 파일을 엽니다. `utf-8-sig`는 UTF-8 BOM이 있는 입력도 처리합니다.
3. `read_students(source)`는 아직 행 전체를 읽지 않은 제너레이터입니다.
4. `summarize`의 `for`가 다음 학생을 요청하면 그때 CSV 행을 읽고 변환합니다.
5. `Student` 생성 시 범위를 검증하고, 성공하면 `yield`로 전달합니다.
6. 집계 함수가 총점·등급·팀별 수·합격자를 누적합니다.
7. 순회가 끝나면 파일을 닫고 완성된 보고서를 반환합니다.
8. 분석이 성공한 뒤에만 JSON 파일을 기록합니다. 잘못된 행은 줄 번호를 포함해 오류 종료합니다.

`reader.line_num`은 읽은 **물리적 줄 수**라서 따옴표 안의 여러 줄 필드에서는 레코드 시작 줄과 다를 수 있습니다. 빈 줄은 CSV reader가 건너뛸 수 있습니다. 이 예제의 컬럼 이름·순서는 정확히 일치해야 합니다.

### 메모리와 검증 범위까지 이해하기

학생 객체 전체를 리스트로 저장하지는 않지만, 합격자 이름 목록은 저장하므로 메모리가 항상 일정한 것은 아닙니다. 인원·평균·등급 수만 필요하면 `passed` 수집을 제거할 수 있습니다. `Student`는 생성 시 검증하지만 점수 입력의 문자열 변환은 CSV 계층이 담당합니다.

입력 분석 실패 때는 출력 파일을 건드리지 않습니다. 다만 기존 출력 파일이 있으면 정상 실행 시 덮어씁니다. 출력 도중 디스크 오류가 나면 부분 파일이 남을 수 있으므로 운영용으로 확장할 때는 임시 파일에 쓴 뒤 원자적 교체를 검토하세요. 학습 예제에서 추가하지 않은 운영 책임도 구분하는 것이 중요합니다.

## 23. 테스트·디버깅 — 정상 결과만 확인하지 않기

테스트는 “코드가 실행된다”뿐 아니라 “정한 계약대로 동작한다”를 확인합니다. 특히 빈 입력·경계값·잘못된 입력·자원 정리를 확인해야 합니다. 표준 라이브러리 `unittest`를 사용하므로 추가 설치가 필요하지 않습니다.

### 전체 코드: test_analyzer.py

```python
import json
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from analyzer import InvalidRow, Student, analyze_file, main, read_students, summarize


class AnalyzerTests(unittest.TestCase):
    def test_report(self):
        source = StringIO("name,team,score\nKim,A,90\nLee,A,80\nPark,B,50\n")
        self.assertEqual(summarize(read_students(source)), {
            "count": 3, "average": 73.33,
            "grades": {"A": 1, "B": 1, "F": 1},
            "teams": {"A": 2, "B": 1}, "passed": ["Kim", "Lee"],
        })

    def test_empty_rows(self):
        report = summarize(read_students(StringIO("name,team,score\n")))
        self.assertEqual(report, {
            "count": 0, "average": None, "grades": {}, "teams": {}, "passed": [],
        })

    def test_grade_boundaries(self):
        for score, grade in [(0, "F"), (59, "F"), (60, "C"), (79, "C"),
                             (80, "B"), (89, "B"), (90, "A"), (100, "A")]:
            with self.subTest(score=score):
                self.assertEqual(Student("Kim", "A", score).grade, grade)

    def test_invalid_model(self):
        for name, team, score in [("", "A", 90), ("Kim", " ", 90),
                                  ("Kim", "A", -1), ("Kim", "A", 101),
                                  ("Kim", "A", True), ("Kim", "A", 90.0)]:
            with self.subTest(name=name, team=team, score=score):
                with self.assertRaises(ValueError):
                    Student(name, team, score)

    def test_invalid_rows_include_line(self):
        for row in ["Kim,A,abc", "Kim,A,101", "Kim,A", "Kim,A,90,extra", ",A,90"]:
            with self.subTest(row=row):
                with self.assertRaisesRegex(InvalidRow, "2행"):
                    list(read_students(StringIO("name,team,score\n" + row + "\n")))

    def test_invalid_header(self):
        for content in ["", "name,score,team\n", "name,team,score,extra\n"]:
            with self.subTest(content=content):
                with self.assertRaisesRegex(InvalidRow, "헤더"):
                    list(read_students(StringIO(content)))

    def test_quoted_name(self):
        source = StringIO('name,team,score\n"Kim, Jr",A,90\n')
        self.assertEqual(summarize(read_students(source))["passed"], ["Kim, Jr"])

    def test_csv_format_error(self):
        with self.assertRaisesRegex(InvalidRow, "CSV 형식 오류"):
            list(read_students(StringIO('name,team,score\n"Kim,A,90\n')))

    def test_cli_output_and_bom(self):
        with TemporaryDirectory() as directory:
            source = Path(directory) / "students.csv"
            output = Path(directory) / "report.json"
            source.write_text("name,team,score\nKim,A,90\n", encoding="utf-8-sig")
            with redirect_stdout(StringIO()):
                self.assertEqual(main([str(source), "--output", str(output)]), 0)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")),
                             analyze_file(source))

    def test_invalid_input_preserves_existing_output(self):
        with TemporaryDirectory() as directory:
            source = Path(directory) / "students.csv"
            output = Path(directory) / "report.json"
            source.write_text("name,team,score\nKim,A,999\n", encoding="utf-8")
            output.write_text("previous report", encoding="utf-8")
            with self.assertRaises(SystemExit) as error:
                main([str(source), "--output", str(output)])
            self.assertEqual(error.exception.code, 2)
            self.assertEqual(output.read_text(encoding="utf-8"), "previous report")


if __name__ == "__main__":
    unittest.main()
```

### 왜 이 조건들을 확인하나

정상 예제는 전체 출력 계약을, 경계값은 `>=`와 `>`의 혼동을, `True`와 소수는 타입 처리 실수를 확인합니다. 따옴표가 있는 CSV는 단순 문자열 분할의 문제를, 기존 출력 유지 테스트는 실패 도중 생기는 부작용을 확인합니다.

`subTest`는 여러 입력 중 어떤 입력에서 실패했는지 알려 줍니다. 예외를 테스트할 때는 “어떤 오류든 났다”보다 예상한 예외 유형과 중요한 메시지를 확인하세요. 테스트에서 구현의 지역 변수 이름이나 내부 호출 횟수까지 고정하면 정상적인 리팩터링도 깨질 수 있습니다. 먼저 외부에서 관찰하는 계약을 검사합니다.

### 오류 메시지를 읽는 순서

1. Traceback 마지막 줄에서 예외 유형과 메시지를 읽습니다.
2. 위로 올라가 자신의 파일에서 어떤 연산이 실패했는지 찾습니다.
3. 해당 값의 타입·범위·내용을 확인합니다. `repr(value)`를 쓰면 공백도 잘 보입니다.
4. 입력이 생성된 지점까지 추적합니다. 마지막 줄만 임시로 고치면 원인은 남을 수 있습니다.
5. 재현 입력을 작은 테스트로 남기고 수정합니다.

예외 연결이 있으면 마지막의 도메인 오류와 그 원인 오류를 함께 봅니다. `breakpoint()`로 중단한 뒤 변수와 호출 스택을 살펴볼 수도 있습니다. 로그에는 비밀번호·인증 토큰 같은 민감한 값을 넣지 않습니다.

**연습:** 합격 기준을 60에서 70으로 바꿔 보세요. 먼저 69·70의 기대 결과를 테스트에 추가한 뒤 구현을 수정하면 바꾸려는 규칙이 명확해집니다.

[공식 문서: unittest](https://docs.python.org/3.11/library/unittest.html) · [pdb](https://docs.python.org/3.11/library/pdb.html)

## 24. 연습 문제·해설·다음 학습 순서

답을 먼저 보지 말고 출력 또는 설계를 적은 뒤 확인하세요. 모든 문제는 앞의 개념을 다시 연결하는 목적입니다.

### 문제 1 — 공유 객체와 재대입

```python
a = [[1]]
b = a.copy()
b[0].append(2)
b = []
print(a)
```

**해설:** 출력은 `[[1, 2]]`입니다. 얕은 복사는 내부 리스트를 공유합니다. `b = []`는 이름 `b`만 재연결하며 이미 일어난 내부 변경을 취소하지 않습니다. `deepcopy(a)`로 만든 별도 내부 리스트라면 공유 변경을 피할 수 있습니다.

### 문제 2 — 기본값과 명시적 빈 리스트

“항목을 리스트에 넣는 함수에서 인자가 없을 때는 새 리스트를 만들고, 빈 리스트가 명시적으로 전달되면 그 리스트를 수정하라.” 어떤 조건을 써야 할까요?

**해설:** 기본값은 `None`, 분기는 `if bucket is None:`입니다. `if not bucket:`은 사용자가 전달한 빈 리스트까지 새로 만들 수 있습니다. `None`도 유효한 입력인 API라면 `MISSING = object()`처럼 별도의 센티널 객체를 만들어 생략 여부와 구분합니다.

### 문제 3 — 클로저가 기억하는 것

```python
def make_reader():
    value = 1
    def read():
        return value
    value = 5
    return read
print(make_reader()())
```

**해설:** 5입니다. 클로저는 생성 순간의 값 1을 무조건 복사하는 것이 아닙니다. 바깥 변수의 연결을 유지하고 호출할 때 읽습니다. `lambda value=value: value` 같은 기본값 저장은 평가 시점이 다릅니다.

### 문제 4 — 데코레이터의 반환값

래퍼에서 `func(*args, **kwargs)`만 호출하고 `return`을 쓰지 않으면 어떻게 될까요?

**해설:** 원래 함수가 10을 반환해도 래퍼는 `None`을 반환합니다. 로그·계측을 추가하는 데코레이터는 정상 반환·예외·인자 전달·메타데이터 중 어떤 계약을 보존할지 확인해야 합니다.

### 문제 5 — 이터레이터를 두 번 사용하기

```python
stream = (n * n for n in range(4))
print(sum(stream))
print(list(stream))
```

**해설:** 첫 출력은 14, 다음은 `[]`입니다. `sum`이 이미 소비했습니다. 다시 계산하려면 제너레이터를 새로 만들고, 결과를 반복 사용하려면 메모리 비용을 감수해 처음에 리스트로 저장할 수 있습니다.

### 문제 6 — frozen과 가변 필드

`@dataclass(frozen=True)`인 객체의 필드가 `list[int]`이면 `obj.scores.append(90)`이 금지될까요?

**해설:** 일반적으로 허용됩니다. 필드 재대입을 막는 것과 그 필드가 가리키는 객체의 내부 변경을 막는 것은 다릅니다. 불변 스냅샷에는 `tuple[int, ...]` 같은 내부 구조도 고려합니다. 타입 힌트만으로 튜플 입력이 자동 강제되지는 않습니다.

### 문제 7 — await를 연달아 쓰면 동시 실행인가

`a = await fetch("A")` 다음 `b = await fetch("B")`를 쓰면 두 대기가 겹칠까요?

**해설:** 이 코드 자체는 A 완료 후 B를 시작합니다. 여러 작업을 겹치려면 `TaskGroup` 등으로 둘 다 예약해야 합니다. 단, 함수 내부에서 별도 태스크를 만드는 등 다른 동작이 있다면 전체 프로그램 구조도 확인해야 합니다.

### 문제 8 — Protocol과 상속

테스트용 전송기가 실제 전송기와 같은 `send(message)`를 제공할 때 꼭 같은 부모 클래스를 상속해야 할까요?

**해설:** 아닙니다. Python에서는 필요한 행동이 있으면 사용할 수 있습니다. Protocol로 그 요구 형태를 정적 타입 계약으로 표현할 수 있습니다. 실제 데이터나 호출의 안전성을 자동으로 완전히 보장하는 장치는 아닙니다.

### 문제 9 — 통합 프로젝트 확장

팀별 평균을 보고서에 추가하되 학생 전체를 저장하지 않고 처리해 보세요. 각 팀의 점수 합계와 인원 수를 각각 누적하면 됩니다. 팀 A 90·80, 팀 B 50 입력의 기대 결과는 `{"A": 85.0, "B": 50.0}`입니다. 팀별 빈 데이터의 표현 규칙도 먼저 결정하세요.

**해설 방향:** `team_totals[team] += score`, `team_counts[team] += 1`을 같은 순회에서 수행하고 마지막에 나눕니다. `sum(...) / len(...)`을 팀마다 반복하려고 전체 학생을 여러 번 순회할 필요가 없습니다.

### 문제 10 — 오류 행을 건너뛰는 정책

현재는 잘못된 행 하나가 있으면 전체 분석을 실패시킵니다. 오류 행만 건너뛰려면 어디를 바꿀까요?

**해설 방향:** 단순히 `except: pass`를 넣지 않습니다. “정상 행 스트림과 오류 목록을 함께 반환할 것인가”, “오류를 콜백으로 수집할 것인가” 같은 인터페이스를 먼저 정합니다. 보고서에 성공·실패 행 수를 표시하고 오류 줄 번호를 남겨야 데이터 누락을 알 수 있습니다. 검증 규칙과 실패 정책은 서로 다른 결정입니다.

### 다음 학습 순서

1. 2~9장을 다시 읽고 코드 출력의 이유를 설명합니다.
2. 22장의 분석기에 팀별 평균을 추가하고 23장의 테스트를 확장합니다.
3. 파일을 모델·서비스·CLI로 분리해 import와 진입점을 연습합니다.
4. 메타클래스·디스크립터 같은 더 깊은 기능은 실제 요구가 생길 때 공부합니다. 먼저 함수·객체·프로토콜의 계약을 안정적으로 다루는 것이 중요합니다.
5. 비동기는 실제 I/O가 있는 작은 작업으로 연습하고, 동시 수 제한·취소·타임아웃·실패 정책을 함께 설계합니다.

### 마지막 점검표

- 이름 재대입과 객체 변경을 구분할 수 있는가?
- 함수 생성 시점과 호출 시점의 차이를 설명할 수 있는가?
- 제너레이터가 언제 실행되고 언제 소비되는지 아는가?
- 데이터 생성 검증과 이후 변경 검증의 차이를 아는가?
- 예외를 어느 계층이 처리해야 하는지 정했는가?
- 타입 힌트와 실행 시 검증을 구분하는가?
- 비동기와 CPU 병렬 계산의 선택 기준을 설명할 수 있는가?
- 정상 입력뿐 아니라 빈 입력·경계값·실패 경로를 테스트했는가?

공식 문서 링크 확인: 2026-10-10. 이 과정은 Python 3.11 이상의 공통 문법을 중심으로 작성했습니다. 실행 환경에 따라 달라질 수 있는 동시성·성능 조건은 해당 장의 공식 자료도 함께 확인하세요.
