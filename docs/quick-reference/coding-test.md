# 코딩 테스트 · 언어별 풀이 요약

## 문제를 읽고 풀이를 만드는 순서

**문제 조건 → 작은 예제 → 단순 풀이 → 복잡도 개선 → 구현 → 경계값 검증** 순서로 접근합니다. 여기서는 Java 17 이상 문법, Python 3, C17, C++17 네 언어를 비교합니다. 실제 제출 언어·버전·함수 이름은 채점 환경을 확인하세요.

1. 입력 개수, 값 범위, 중복·음수·빈 입력 가능 여부를 적습니다.
2. ‘무엇을 출력해야 하는가’를 한 문장으로 바꿉니다.
3. 손으로 작은 사례를 풀고 가장 단순한 방법부터 생각합니다.
4. 가장 많이 반복하는 연산과 필요한 자료구조를 고릅니다.
5. 반복문이 유지하는 조건이나 점화식으로 정답인 이유를 설명합니다.
6. 최소 입력, 최댓값, 중복, 음수, 답이 없는 경우를 확인합니다.

표준 입력 문제는 전체 프로그램을, 함수 완성형은 지정된 함수와 반환값을 제출합니다. 함수 완성형에서 임의로 입력 코드를 추가하지 마세요.

## 시간 · 공간 복잡도와 문제의 단서

N은 원소 수, Q는 질문 수, V·E는 정점·간선 수입니다. 시간 제한은 언어·상수·입출력에 따라 달라지므로 ‘초당 몇 번’ 같은 고정 규칙으로 판단하지 않습니다.

| 단서 | 먼저 검토할 방법 | 대표 비용 / 조건 |
|---|---|---|
| 작은 후보를 모두 시도 | 완전 탐색·백트래킹 | 후보 수와 깊이를 계산 |
| 중복·빈도·존재 여부 | 해시 맵·집합 | 일반적인 해시 구현에서 조회 평균 O(1) |
| 순서·순위·인접한 값 | 정렬 | 비교 정렬 보통 O(N log N) |
| 변하지 않는 배열의 구간 합 | 누적 합 | 전처리 O(N), 질의 O(1) |
| 정렬된 범위 또는 단조 조건 | 이분 탐색 | O(log N)번 판단 |
| 연속 구간 | 투 포인터·슬라이딩 윈도 | 포인터가 되돌아가지 않으면 O(N) |
| 같은 가중치의 최단 거리 | BFS | 인접 리스트 기준 O(V+E) |
| 연결·경로·모든 선택 탐색 | DFS·백트래킹 | 그래프 방문과 경로 열거는 비용이 다름 |
| 작은 답으로 큰 답 만들기 | 동적 계획법(DP) | 상태 수 × 상태당 전이 비용 |
| 가장 작은/큰 값 반복 추출 | 힙 | 삽입·삭제 O(log N) |

N=100,000이면 이중 반복의 N²은 100억 번입니다. O(N) 배열도 원소 타입과 객체 오버헤드에 따라 메모리 사용량이 달라집니다. 가중치가 서로 다른 그래프는 BFS 최단 거리 전제가 성립하지 않습니다.

## 자료구조를 언어별로 대응하기

| 목적 | Java | Python | C | C++ |
|---|---|---|---|---|
| 배열 | 배열·ArrayList | list | 배열·malloc | vector |
| 빈도 | HashMap | dict·Counter | 범위 배열·직접 해시 | unordered_map |
| 중복 제거 | HashSet | set | 정렬 후 제거 | set·unordered_set |
| 스택 | ArrayDeque | list append/pop | 배열+top | stack |
| 큐 | ArrayDeque | deque | 배열+head/tail | queue |
| 최소 힙 | PriorityQueue | heapq | 직접 구현 | priority_queue+greater |

C에서는 위 표의 힙을 직접 구현합니다. 외부 라이브러리 사용 여부는 채점 환경에서 확인하세요.

## 공통 문제 — 여러 구간의 합

**입력:** 첫 줄 N Q, 다음 N개의 정수, 이후 Q개의 `(L, R)` 질문. 배열의 위치는 1부터 시작하며 양 끝을 포함합니다. 조건은 `1 ≤ N ≤ 100000`, `0 ≤ Q ≤ 100000`, `|A[i]| ≤ 10⁹`, `1 ≤ L ≤ R ≤ N`입니다. 입력은 이 조건을 만족한다고 가정합니다.

```text
5 3
2 -1 3 5 4
1 3
2 5
4 4
```

```text
4
11
5
```

매번 구간을 더하면 최악 O(NQ)입니다. `P[i] = 처음 i개 원소의 합`, `P[0] = 0`으로 두면 **답 = P[R] - P[L-1]**입니다. 앞부분을 빼서 원하는 구간만 남기는 원리입니다. 예제 P는 `0, 2, 1, 4, 9, 13`입니다.

전처리 O(N) + 질문 처리 O(Q), 누적 합 저장 O(N)입니다. 아래 Python은 입력 전체와 출력을 저장하고 Java도 출력을 모으므로 전체 프로그램의 추가 메모리는 O(N+Q)까지 사용합니다. C·C++는 질문마다 바로 출력합니다. 값이 바뀌는 구간 합 문제라면 이 풀이를 그대로 쓰지 말고 갱신 비용을 따져야 합니다.

## Java — long · 컬렉션 · 출력 모으기

**핵심:** 입력은 버퍼로 읽고 토큰으로 나누며, 대량 출력은 `StringBuilder`로 모읍니다. 아래 파일은 `Main.java`, 클래스는 `Main`입니다.

```java
// 메서드 내부 발췌, import java.util.*; 필요
Map<Integer, Integer> freq = new HashMap<>();
freq.merge(3, 1, Integer::sum);
ArrayDeque<Integer> queue = new ArrayDeque<>();
queue.offerLast(10);
int first = queue.removeFirst();
PriorityQueue<Integer> heap = new PriorityQueue<>();
heap.offer(5);
heap.offer(2); // heap.peek() == 2
```

문자열 내용 비교는 `equals()`, 값 비교 정렬은 `Integer.compare(a,b)`를 사용합니다. 누적 합은 `long`, 큰 곱셈은 `1L * a * b`로 계산합니다. 큐가 비었는지 확인하고 꺼내세요.

### 구간 합 전체 풀이

[Main.java 내려받기](sample-files/coding-test/Main.java)

```java
import java.io.*;
import java.util.*;

public class Main {
    static class FastInput {
        final BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));
        StringTokenizer tokens;
        String next() throws IOException {
            while (tokens == null || !tokens.hasMoreTokens()) {
                String line = reader.readLine();
                if (line == null) throw new EOFException();
                tokens = new StringTokenizer(line);
            }
            return tokens.nextToken();
        }
        int nextInt() throws IOException { return Integer.parseInt(next()); }
        long nextLong() throws IOException { return Long.parseLong(next()); }
    }
    public static void main(String[] args) throws Exception {
        FastInput in = new FastInput();
        int n = in.nextInt(), q = in.nextInt();
        long[] prefix = new long[n + 1];
        for (int i = 1; i <= n; i++) prefix[i] = prefix[i - 1] + in.nextLong();
        StringBuilder out = new StringBuilder();
        for (int i = 0; i < q; i++) {
            int left = in.nextInt(), right = in.nextInt();
            out.append(prefix[right] - prefix[left - 1]).append('\n');
        }
        System.out.print(out);
    }
}
```

입력 줄바꿈 위치가 달라도 토큰 단위로 읽습니다. [Java 공식 컬렉션](https://dev.java/learn/api/collections-framework/intro/)

## Python — 빠른 입력 · dict · deque

**핵심:** `sys.stdin.buffer`, `dict`, `set`, `deque`, `heapq`를 익히세요. Python 정수는 고정 32비트 범위에 묶이지 않지만 큰 정수의 연산 비용은 증가합니다.

```python
from collections import Counter, deque
from heapq import heappush, heappop
freq = Counter([3, 1, 3])
print(freq[3])                 # 2
queue = deque([10])
queue.append(20)
print(queue.popleft())         # 10
heap = []
heappush(heap, 5)
heappush(heap, 2)
print(heappop(heap))            # 2
pairs = [(2, 3), (1, 5), (2, 1)]
print(sorted(pairs, key=lambda p: (p[0], p[1])))
```

`list.pop(0)`을 반복하는 큐는 원소 이동 비용이 큽니다. 깊은 재귀는 제한에 걸릴 수 있으므로 반복형 DFS도 준비하세요. 2차원 배열은 `[[0] * m for _ in range(n)]`으로 만들어 행을 분리합니다.

### 구간 합 전체 풀이

[prefix_sum.py 내려받기](sample-files/coding-test/prefix_sum.py)

```python
import sys

data = list(map(int, sys.stdin.buffer.read().split()))
it = iter(data)
n, q = next(it), next(it)
prefix = [0] * (n + 1)
for i in range(1, n + 1):
    prefix[i] = prefix[i - 1] + next(it)
answers = []
for _ in range(q):
    left, right = next(it), next(it)
    answers.append(str(prefix[right] - prefix[left - 1]))
sys.stdout.write("\n".join(answers))
```

`prefix[0]`을 0으로 두어 L=1도 같은 식으로 처리합니다. [공식 자료구조](https://docs.python.org/3/tutorial/datastructures.html) · [공식 heapq](https://docs.python.org/3/library/heapq.html)

## C — 메모리 · 정수 범위 · 비교 함수

**핵심:** 배열 크기, 인덱스, 메모리 해제, 출력 서식을 직접 관리합니다. 합계는 `long long`으로 저장하고 `%lld`로 읽고 씁니다.

```c
/* qsort용 비교 함수: <stdlib.h> 필요 */
int compare_int(const void *left, const void *right) {
    int a = *(const int *)left;
    int b = *(const int *)right;
    return (a > b) - (a < b);
}
/* qsort(values, n, sizeof values[0], compare_int); */
```

비교 함수에서 `a-b`를 반환하면 오버플로할 수 있습니다. 값 범위가 작으면 빈도 배열, 일반 값이면 정렬이나 별도 해시 구현을 검토합니다. 배열 큐는 넣을 때 `queue[tail++] = x`, 꺼낼 때 `x = queue[head++]`로 구현하되 용량을 확보합니다.

### 구간 합 전체 풀이

[prefix_sum.c 내려받기](sample-files/coding-test/prefix_sum.c)

```c
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    int n, q;
    if (scanf("%d %d", &n, &q) != 2) return 1;
    long long *prefix = calloc((size_t)n + 1, sizeof *prefix);
    if (prefix == NULL) return 1;
    for (int i = 1; i <= n; ++i) {
        long long value;
        if (scanf("%lld", &value) != 1) { free(prefix); return 1; }
        prefix[i] = prefix[i - 1] + value;
    }
    for (int i = 0; i < q; ++i) {
        int left, right;
        if (scanf("%d %d", &left, &right) != 2) { free(prefix); return 1; }
        printf("%lld\n", prefix[right] - prefix[left - 1]);
    }
    free(prefix);
    return 0;
}
```

`calloc()`으로 0으로 초기화하고 실패 여부를 검사한 뒤 `free()`로 해제합니다. [C 표준 초안 N1570: stdio·stdlib](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf)

## C++ — STL로 구현 줄이기

**핵심:** `vector`, `sort`, `lower_bound`, `queue`, `unordered_map`, `priority_queue`를 연결해 사용합니다.

```cpp
// 필요한 헤더: <algorithm>, <vector>, <queue>, <functional>
std::vector<int> a{4, 1, 4, 2};
std::sort(a.begin(), a.end());
a.erase(std::unique(a.begin(), a.end()), a.end());
auto it = std::lower_bound(a.begin(), a.end(), 3);
// it는 3 이상인 첫 값 4를 가리킴. end() 여부 확인 후 역참조.
std::priority_queue<int, std::vector<int>, std::greater<int>> heap;
heap.push(5);
heap.push(2); // heap.top() == 2
```

기본 `priority_queue<int>`는 최대 힙입니다. `lower_bound()`는 정렬된 범위에서 사용하세요. `int`끼리 곱한 뒤 long long에 저장하면 곱셈 단계에서 이미 넘칠 수 있으므로 `1LL * a * b`처럼 먼저 확장합니다.

### 구간 합 전체 풀이

[prefix_sum.cpp 내려받기](sample-files/coding-test/prefix_sum.cpp)

```cpp
#include <iostream>
#include <vector>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, q;
    cin >> n >> q;
    vector<long long> prefix(n + 1, 0);
    for (int i = 1; i <= n; ++i) {
        long long value;
        cin >> value;
        prefix[i] = prefix[i - 1] + value;
    }
    while (q--) {
        int left, right;
        cin >> left >> right;
        cout << prefix[right] - prefix[left - 1] << '\n';
    }
}
```

`sync_with_stdio(false)`를 썼다면 같은 프로그램에서 C의 stdio와 C++ 입출력을 섞지 않는 편이 명확합니다. [C++ 정렬 규정](https://eel.is/c++draft/alg.sort)

## 이분 탐색 · 투 포인터 풀이 패턴

아래부터는 알고리즘 원리를 보여주는 **독립 실행 가능한 Python 예제**입니다. 앞의 자료구조 표를 참고해 다른 언어로 옮겨 보세요.

```python
# target 이상인 첫 위치: 정렬된 배열, [left, right) 구간

def lower_bound(a, target):
    left, right = 0, len(a)
    while left < right:
        mid = (left + right) // 2
        if a[mid] < target:
            left = mid + 1
        else:
            right = mid
    return left

assert lower_bound([1, 2, 2, 5], 2) == 1
assert lower_bound([1, 2, 2, 5], 6) == 4
assert lower_bound([], 2) == 0
```

불변 조건은 ‘답 후보가 left부터 right 사이에 있다’입니다. 반환값이 배열 길이라면 해당 값이 없습니다. C/C++/Java에서 mid는 `left + (right-left)/2`로 계산해 덧셈 오버플로를 피할 수 있습니다.

```python
# 오름차순 배열에서 합이 target인 서로 다른 두 위치 찾기

def two_sum_sorted(a, target):
    left, right = 0, len(a) - 1
    while left < right:
        total = a[left] + a[right]
        if total == target:
            return left, right
        if total < target:
            left += 1
        else:
            right -= 1
    return None

assert two_sum_sorted([1, 2, 4, 7], 6) == (1, 2)
assert two_sum_sorted([1], 2) is None
```

정렬 비용을 제외하면 O(N)입니다. 정렬하면 원래 인덱스가 바뀌므로 원래 위치가 필요하면 함께 보관하세요. 연속 구간 합을 늘리고 줄이는 슬라이딩 윈도는 음수가 섞이면 단조성이 깨질 수 있습니다.

## BFS · DFS — 그래프 탐색

```python
from collections import deque

# 정점 0..3, 인접 리스트, 간선마다 비용 1
graph = [[1, 2], [0, 3], [0], [1]]
distance = [-1] * len(graph)
distance[0] = 0
queue = deque([0])
while queue:
    node = queue.popleft()
    for nxt in graph[node]:
        if distance[nxt] == -1:
            distance[nxt] = distance[node] + 1
            queue.append(nxt)
assert distance == [0, 1, 1, 2]

seen = [False] * len(graph)
seen[0] = True
stack = [0]
while stack:
    node = stack.pop()
    for nxt in graph[node]:
        if not seen[nxt]:
            seen[nxt] = True
            stack.append(nxt)
assert all(seen)
```

BFS는 큐, DFS는 스택을 사용합니다. **넣을 때 방문 표시**를 해 중복 삽입을 막습니다. BFS의 거리 -1은 도달하지 못한 정점입니다. DFS 방문 순서는 BFS 최단 거리를 대신하지 않습니다.

## DP · 그리디 · 백트래킹 구분

DP는 상태·초깃값·전이·계산 순서를 먼저 정합니다. 예: 한 번에 1칸 또는 2칸을 오를 때 N칸에 도착하는 방법 수.

```python
def ways(n):
    dp = [0] * (n + 1)
    dp[0] = 1
    for i in range(1, n + 1):
        dp[i] = dp[i - 1]
        if i >= 2:
            dp[i] += dp[i - 2]
    return dp[n]

assert ways(0) == 1
assert ways(4) == 5
```

마지막에 1칸 온 경우와 2칸 온 경우는 겹치지 않으므로 더합니다. 시간 O(N), 공간 O(N)이며 이전 두 값만 보관하면 공간 O(1)로 줄일 수 있습니다. 답이 매우 커지면 문제에서 지정한 나머지 연산이나 큰 정수가 필요합니다.

| 방법 | 판단 기준 | 흔한 실수 |
|---|---|---|
| DP | 같은 부분 문제가 반복되는가? | 상태 정의 없이 배열부터 만들기 |
| 그리디 | 지금의 선택이 최적해를 보존함을 증명할 수 있는가? | 예제 몇 개로 최적성 단정 |
| 백트래킹 | 모든 선택을 보되 불가능한 가지를 제거할 수 있는가? | 재귀 복귀 후 상태 복원 누락 |

동전 `{1,3,4}`로 6을 만들 때 큰 동전부터 고르면 `4+1+1`, 최적은 `3+3`입니다. 그리디는 조건 확인 없이 적용할 수 없습니다.

## 실행 방법 · 제출 전 점검 · 오답 기록

[예제 입력](sample-files/coding-test/input.txt)을 각 소스와 같은 폴더에 저장한 뒤 아래 명령을 실행합니다. Java JDK, Python 3, C/C++ 컴파일러는 해당 예제를 실행할 때 필요합니다.

```bash
python3 prefix_sum.py < input.txt
cc -std=c17 -O2 prefix_sum.c -o prefix_c
./prefix_c < input.txt
c++ -std=c++17 -O2 prefix_sum.cpp -o prefix_cpp
./prefix_cpp < input.txt
javac Main.java
java Main < input.txt
```

- 답만 출력하고 안내 문구·디버깅 출력을 제거했는가?
- 입력 범위에 따라 int/long/long long과 Python 정수를 골랐는가?
- 시작·끝 인덱스와 포함 범위를 확인했는가?
- 중복값·음수·원소 1개·질문 0개에서도 동작하는가?
- 시간·메모리 제한과 제출 함수/클래스 이름을 확인했는가?

오답 기록은 **문제의 단서 → 처음 접근 → 실패 입력 → 원인 → 수정한 원리 → 시간/공간 복잡도** 순서로 짧게 남깁니다. 정답 코드를 암기하기보다 같은 풀이를 다른 언어로 옮길 때 달라지는 자료구조와 숫자 범위를 비교하세요.
