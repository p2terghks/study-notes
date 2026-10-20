# 고급AI프로그래밍 — AI·Python 요약

**범위: 실습 1~6 · AI 기초, Python, NumPy, 함수·클래스, 그래프·파일, PyTorch**

## 1. AI 핵심 개념

| 개념 | 의미 |
|---|---|
| 인공지능 | 인식·판단·문제 해결 같은 지능적 작업을 수행하는 기술 |
| 머신러닝 | 데이터에서 규칙이나 패턴을 학습하는 방법 |
| 딥러닝 | 여러 층의 신경망을 사용하는 머신러닝 방법 |
| 지도학습 | 입력과 정답을 함께 사용해 학습 |
| 비지도학습 | 정답 없이 데이터의 구조나 패턴을 학습 |
| 분류 | 범주를 예측 |
| 회귀 | 연속적인 수치를 예측 |

예를 들어 **스팸 여부는 분류**, **집값 예측은 회귀**, **비슷한 고객끼리 묶기는 군집화**야.

## 2. Python 자료구조

| 자료구조 | 특징 | 예시 |
|---|---|---|
| `list` | 순서가 있고 수정 가능 | `[1, 2, 3]` |
| `tuple` | 순서가 있고 원소 교체 불가 | `(1, 2, 3)` |
| `dict` | 키와 값으로 저장 | `{"name": "민수"}` |
| `set` | 중복 없는 원소 집합 | `{1, 2, 3}` |

```python
x = [10, 20, 30, 40]

x[0]       # 10: Python 인덱스는 0부터
x[-1]      # 40: 마지막 원소
x[1:3]     # [20, 30]: 끝 인덱스 3은 제외
x.append(50)
```

**R은 1부터, Python은 0부터** 시작한다는 점이 가장 많이 헷갈려.

## 3. 연산·조건문·반복문

```python
7 / 2       # 3.5: 나눗셈
7 // 2      # 3: 몫을 내림
7 % 2       # 1: 나머지
2 ** 3      # 8: 거듭제곱

score = 85
if score >= 90:
    grade = "A"
elif score >= 80:
    grade = "B"
else:
    grade = "C"

total = 0
for i in range(1, 11):
    if i % 2 == 0:
        total += i
# total = 30
```

- `range(1, 11)`은 **1부터 10까지**.
- `break`는 반복 종료, `continue`는 현재 반복의 나머지를 건너뛰기.
- Python은 **들여쓰기**로 코드 블록을 구분해.

## 4. 함수와 클래스

```python
def add(a, b):
    return a + b

class Student:
    def __init__(self, name, score):
        self.name = name
        self.score = score

    def passed(self):
        return self.score >= 60

s = Student("민수", 80)
s.passed()                  # True
```

- **함수**: 재사용할 작업을 묶음.
- **클래스**: 객체의 데이터와 동작을 정의.
- **객체**: 클래스로 만든 개별 대상.
- **`self`**: 해당 객체 자신.
- **`__init__`**: 객체 초기화 메서드.
- **`return`**은 값을 돌려주고, **`print()`**는 화면에 출력해.

## 5. NumPy

NumPy는 배열과 수치 연산을 위한 라이브러리야.

```python
import numpy as np

a = np.array([1, 2, 3])
a * 2                         # [2, 4, 6]
a.mean()                      # 2.0

b = np.arange(6).reshape(2, 3)
# [[0, 1, 2],
#  [3, 4, 5]]

b.shape                       # (2, 3)
b.ndim                        # 2
b.sum(axis=0)                 # [3, 5, 7]: 행 방향을 줄여 열별 합
b.sum(axis=1)                 # [3, 12]: 열 방향을 줄여 행별 합
```

**리스트 `[1, 2] * 2`는 반복**, **NumPy 배열에 `* 2`는 각 원소의 곱셈**이야.

## 6. 그래프와 파일 처리

```python
import matplotlib.pyplot as plt

plt.plot([1, 2, 3], [2, 4, 6])
plt.xlabel("x")
plt.ylabel("y")
plt.show()
```

`plot()`은 선 그래프, `scatter()`는 산점도, `bar()`는 막대그래프, `hist()`는 히스토그램을 그려.

```python
with open("memo.txt", "w", encoding="utf-8") as f:
    f.write("Python 공부")

with open("memo.txt", "r", encoding="utf-8") as f:
    text = f.read()
```

파일 모드 **`r`은 읽기, `w`는 덮어쓰기, `a`는 뒤에 추가**야. `with`를 사용하면 블록을 벗어날 때 파일이 닫혀.

## 7. PyTorch와 텐서

- **텐서**: 스칼라·벡터·행렬 등을 포함하는 다차원 데이터 구조.
- **PyTorch**: 텐서 연산, 자동 미분, 신경망 학습에 사용하는 라이브러리.
- **손실 함수**: 예측과 정답 사이의 차이를 수치화.
- **역전파**: 손실에 대한 매개변수의 기울기를 계산.
- **옵티마이저**: 기울기를 사용해 매개변수를 갱신.

```python
import torch

x = torch.tensor(2.0, requires_grad=True)
y = x ** 2
y.backward()

print(x.grad)     # tensor(4.): dy/dx = 2x
```

학습의 기본 흐름은 다음과 같아.

**입력 → 예측 → 손실 계산 → 기울기 계산 → 가중치 갱신 → 반복**

**시험 직전 암기:**  
**인덱스 0부터 / 슬라이스 끝 제외 / `=` 대입·`==` 비교 / `**` 거듭제곱 / NumPy=배열 계산 / PyTorch=텐서·자동 미분**

---

작성 기준: 이전 학습 자료 요약을 바탕으로 정리한 복습 노트입니다. 원본 사진·PDF 전체를 다시 대조한 정답지는 아닙니다.
