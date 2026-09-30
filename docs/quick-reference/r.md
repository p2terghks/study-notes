# R 언어 · 문법과 데이터 처리 요약

## 시작하기 — R과 Rscript

R은 통계 계산과 데이터 분석에 사용하는 언어입니다. 이 문서는 추가 패키지 없이 기본 R로 실습합니다. `.R` 파일에 코드를 저장하고 터미널에서 실행하세요.

```bash
Rscript --version
Rscript hello.R
```

```r
# hello.R
message <- "R 공부 시작"
print(message)
cat("합계:", sum(c(10, 20, 30)), "\n")
```

`print()`는 객체를 확인할 때, `cat()`은 원하는 출력 형식을 만들 때 사용합니다. `?mean` 또는 `help("mean")`으로 함수 도움말을 봅니다. R 콘솔의 `>` 표시는 파일에 복사하지 않습니다. 설치는 [R 공식 사이트](https://www.r-project.org/)에서 운영체제에 맞게 진행합니다.

## 변수 · 타입 · 연산자

```r
score <- 85            # double: 기본 숫자
count <- 3L            # integer: L을 붙인 정수
name <- "민수"         # character
passed <- TRUE         # logical
print(typeof(score))   # "double"
print(as.numeric("42") + 1) # 43
print(7 %/% 2)         # 3: 몫
print(7 %% 2)          # 1: 나머지
print(2 ^ 3)           # 8: 거듭제곱
```

`<-`는 대입, `==`는 비교입니다. `/`는 나눗셈이며 `!`는 부정입니다. 원자 벡터는 한 타입으로 맞춰지므로 `c(1, "2")`는 문자열 벡터가 됩니다. 숫자 연산 전 타입을 확인하세요.

## 벡터 — 여러 값을 한 번에 계산하기

```r
x <- c(60, 80, 100)
print(x + 5)           # 65 85 105
print(x >= 80)         # FALSE TRUE TRUE
print(sum(x))          # 240
print(mean(x))         # 80
print(length(x))       # 3
print(seq(2, 8, by = 2)) # 2 4 6 8
print(rep(0, 3))       # 0 0 0
```

`c()`로 값을 묶고 벡터 연산으로 각 원소를 처리합니다. 길이가 다른 벡터를 연산하면 짧은 쪽이 반복되는 **재활용 규칙**이 적용됩니다. `c(1,2,3,4) + c(10,20)`은 `11 22 13 24`이므로 의도한 길이인지 확인하세요.

## 인덱스 — 첫 원소는 1번

```r
x <- c(10, 20, 30, 40)
print(x[1])            # 10
print(x[c(1, 3)])      # 10 30
print(x[-1])           # 첫 원소 제외: 20 30 40
print(x[x >= 25])      # 30 40
print(which(x >= 25))  # 위치: 3 4
print(x[0])            # numeric(0): 빈 벡터
```

Python·C와 달리 R은 **1부터 시작**합니다. 음수 인덱스는 뒤에서 세는 것이 아니라 해당 위치를 제외합니다. 양수와 음수 인덱스를 함께 섞지 마세요. 범위를 벗어난 벡터 원소 조회는 `NA`가 될 수 있습니다. [공식: 인덱싱](https://stat.ethz.ch/R-manual/R-devel/library/base/html/Extract.html)

## 결측값 — NA · NULL · NaN

```r
x <- c(70, NA, 90)
print(is.na(x))            # FALSE TRUE FALSE
print(mean(x))             # NA
print(mean(x, na.rm = TRUE)) # 80
print(x[!is.na(x)])         # 70 90
print(is.null(NULL))        # TRUE
print(is.nan(0 / 0))        # TRUE
```

| 값 | 의미 | 확인 |
|---|---|---|
| NA | 값이 누락되거나 알려지지 않음 | is.na(x) |
| NULL | 객체/성분이 없음을 표현 | is.null(x) |
| NaN | 정의되지 않은 수치 연산 결과 | is.nan(x) |

`x == NA`로 검사하지 않습니다. `is.na()`는 NaN도 참으로 판단합니다. 결측값을 제외할지는 분석 목적에 따라 정하세요. [공식: NA](https://stat.ethz.ch/R-manual/R-devel/library/base/html/NA.html)

## 조건문 · 반복문

```r
score <- 75
if (score >= 60) {
  print("합격")
} else {
  print("재도전")
}
x <- c(3, 5, 7)
for (i in seq_along(x)) {
  cat(i, x[i], "\n")
}
print(ifelse(x >= 5, "큼", "작음"))
```

`if`에는 결측이 아닌 논리값 하나를 넣습니다. 벡터별 선택은 `ifelse()`를 사용합니다. `&`·`|`는 원소별 논리 연산, `&&`·`||`는 단일 조건의 단락 평가입니다. `while (조건) { ... }`, `break`, `next`도 사용할 수 있습니다. 빈 벡터까지 고려하려면 `1:length(x)` 대신 `seq_along(x)`, 횟수 반복은 `seq_len(n)`을 사용하세요. `1:0`은 빈 벡터가 아닙니다.

## 함수와 반복 처리

```r
add_bonus <- function(score, bonus = 5) {
  pmin(score + bonus, 100)
}
print(add_bonus(c(60, 98))) # 65 100
values <- list(c(1, 2), c(3, 4))
print(lapply(values, sum))
print(vapply(values, sum, numeric(1))) # 3 7
```

함수는 마지막 식의 값을 반환하며 `return()`으로 일찍 반환할 수도 있습니다. `lapply()`는 리스트, `vapply()`는 지정한 결과 타입·길이에 맞춰 반환합니다. `pmin()`은 원소별 최솟값이고 `min()`은 전체 최솟값입니다. [공식: lapply·vapply](https://stat.ethz.ch/R-manual/R-devel/library/base/html/lapply.html)

## 리스트 · 행렬 · 데이터 프레임

```r
person <- list(name = "민수", scores = c(80, 90))
print(person$name)
print(person[[2]])         # 벡터를 꺼냄
print(person[2])           # 리스트 형태 유지
m <- matrix(1:6, nrow = 2, byrow = TRUE)
print(m[1, 2])             # 2
print(m[, 1])              # 1 4
students <- data.frame(name = c("민수", "지수"), score = c(80, 95))
print(students$score)
print(students[students$score >= 90, , drop = FALSE])
```

| 구조 | 용도 |
|---|---|
| vector | 같은 타입의 값들 |
| list | 타입이 다른 값/객체 묶음 |
| matrix | 같은 타입의 행·열 데이터 |
| data.frame | 열마다 타입이 다른 표 |

행렬의 기본 채우기는 열 방향이며 위 예제는 `byrow=TRUE`로 행 방향을 지정했습니다. `drop=FALSE`는 선택 후 차원이 사라지는 것을 막습니다. [공식: 데이터 프레임](https://stat.ethz.ch/R-manual/R-devel/library/base/html/data.frame.html)

## 정렬 · 빈도 · 문자열

```r
x <- c(30, 10, 30, 20)
print(sort(x))          # 10 20 30 30
print(order(x))         # 2 4 1 3: 정렬될 위치
print(unique(x))        # 30 10 20
print(table(x))         # 값별 개수
print(paste("R", "공부"))   # "R 공부"
print(paste0("day", 1:3)) # "day1" "day2" "day3"
print(strsplit("a,b,c", ",", fixed = TRUE)[[1]])
```

`sort()`는 정렬된 값, `order()`는 정렬 순서의 인덱스를 반환합니다. 표를 정렬할 때는 `df[order(df$score), , drop=FALSE]`처럼 씁니다. [공식: 정렬](https://search.r-project.org/R/refmans/base/html/sort.html)

## CSV · 기초 통계 · 그래프

아래는 독립적으로 실행하는 예제입니다. 현재 작업 폴더에 CSV와 PNG를 생성합니다.

```r
df <- data.frame(name = c("민수", "지수", "현우"), score = c(70, 90, 80))
write.csv(df, "scores.csv", row.names = FALSE, fileEncoding = "UTF-8")
loaded <- read.csv("scores.csv", fileEncoding = "UTF-8")
print(summary(loaded$score))
print(median(loaded$score)) # 80
print(sd(loaded$score))     # 표본 표준편차: 10
png("scores.png", width = 800, height = 500)
barplot(loaded$score, names.arg = c("A", "B", "C"), ylab = "Score")
dev.off()
```

`getwd()`로 저장 위치를 확인합니다. `head(df)`, `str(df)`, `nrow(df)`, `names(df)`로 데이터 구조부터 살펴보세요. 그래프 장치를 열었다면 `dev.off()`로 닫아 저장을 완료합니다.

## 전체 실습 — 결측값을 제외한 성적 집계

아래 전체 코드는 [grade-summary.R](sample-files/grade-summary.R)로 제공됩니다. 파일을 저장한 폴더에서 `Rscript grade-summary.R`로 실행합니다.

```r
scores <- c(55, 80, NA, 95, 70)
valid <- scores[!is.na(scores)]
stopifnot(length(valid) > 0)
cat("인원:", length(valid), "\n")
cat("평균:", mean(valid), "\n")
cat("합격:", sum(valid >= 60), "\n")
cat("정렬:", sort(valid), "\n")
```

예상 결과는 인원 `4`, 평균 `75`, 합격 `3`, 정렬 `55 70 80 95`입니다. 점수를 모두 `NA`로 바꾸면 `stopifnot()`에서 중단합니다. 데이터가 없을 때 평균을 표시할지 별도 메시지를 낼지는 요구사항에 맞게 정합니다.

## 복습 체크 · 참고 자료

R 문법을 복습할 때는 다음 항목을 확인하세요.

- 1부터 시작하는 인덱스를 확인합니다.
- `integer` 오버플로를 피하려고 큰 합계는 `numeric`으로 처리합니다. double도 큰 정수 정밀도에 한계가 있습니다.
- 반복문에서 `c()`로 계속 늘리기보다 `numeric(n)` 등으로 공간을 미리 확보합니다.
- 객체 확인용 `print()`와 출력 형식을 지정하는 `cat()`을 구분합니다.

[공식 R 입문서](https://cran.r-project.org/doc/manuals/r-release/R-intro.html) · [공식 scan 입력](https://search.r-project.org/R/refmans/base/html/scan.html)
