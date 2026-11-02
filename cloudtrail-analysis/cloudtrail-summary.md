# 처음 배우는 R — 로그인 기록 코드 설명

입력 JSON → 이벤트 리스트 → ConsoleLogin 선택 → 시간·사용자·IP·결과 표 → CSV 저장.

실행: `Rscript login_records.R logs.json`

## 1행

```r
# CloudTrail에서 콘솔 로그인 기록만 추출합니다.
```

주석입니다. # 뒤는 실행되지 않습니다. CloudTrail에서 콘솔 로그인 기록만 추출합니다.

## 2행

```r
# 실행: Rscript login_records.R 로그.json [출력.csv]
```

주석입니다. # 뒤는 실행되지 않습니다. 실행: Rscript login_records.R 로그.json [출력.csv]

## 3행

```r
if (!requireNamespace("jsonlite", quietly = TRUE)) {
```

requireNamespace()는 jsonlite 패키지가 설치되어 사용할 수 있는지 확인해 TRUE 또는 FALSE를 반환합니다. !는 반대입니다. 패키지가 없으면 중괄호 안을 실행합니다. quietly=TRUE는 확인 메시지를 줄입니다.

## 4행

```r
  stop('jsonlite가 필요합니다: install.packages("jsonlite")')
```

stop()은 오류를 표시하고 실행을 중단합니다. 따옴표 속 install.packages(...)는 안내 문장입니다. 이 줄이 패키지를 자동 설치하지는 않습니다.

## 5행

```r
}
```

앞에서 시작한 함수·조건·반복의 중괄호 블록을 닫습니다.

## 7행

```r
# 필드가 없으면 NA, 있으면 문자열 하나로 반환합니다.
```

주석입니다. # 뒤는 실행되지 않습니다. 필드가 없으면 NA, 있으면 문자열 하나로 반환합니다.

## 8행

```r
text_value <- function(x) {
```

text_value라는 이름에 함수를 저장합니다. function(x)의 x는 함수를 부를 때 전달받는 값입니다. {부터 함수의 동작이 시작됩니다.

## 9행

```r
  if (is.null(x) || length(x) == 0) NA_character_ else as.character(x[[1]])
```

x가 NULL이거나 길이가 0이면 NA_character_를 반환합니다. ||는 두 조건 중 하나가 참이면 된다는 뜻입니다. 값이 있으면 x[[1]]로 첫 원소를 꺼내 as.character()로 문자열로 맞춥니다.

## 10행

```r
}
```

앞에서 시작한 함수·조건·반복의 중괄호 블록을 닫습니다.

## 12행

```r
# Records 포장, 단일 이벤트, 이벤트 배열을 목록으로 맞춥니다.
```

주석입니다. # 뒤는 실행되지 않습니다. Records 포장, 단일 이벤트, 이벤트 배열을 목록으로 맞춥니다.

## 13행

```r
event_list <- function(x) {
```

event_list()를 정의합니다. 파일 포장이 달라도 결과를 “이벤트 목록” 하나의 형태로 맞추는 함수입니다.

## 14행

```r
  if (!is.list(x)) stop("JSON 객체 또는 배열이 필요합니다.")
```

is.list(x)가 FALSE이면 stop()으로 중단합니다. JSON 숫자나 문자열 하나는 이벤트 목록으로 다룰 수 없기 때문입니다.

## 15행

```r
  if (!is.null(x$Records)) return(x$Records)
```

x$Records는 이름이 Records인 원소입니다. 그 원소가 NULL이 아니면 return()으로 내부 이벤트 목록을 즉시 반환하고 함수를 끝냅니다.

## 16행

```r
  if (!is.null(x$eventName)) return(list(x))
```

x$eventName이 있으면 단일 이벤트로 봅니다. list(x)는 그 이벤트 전체를 원소 하나인 목록 안에 넣습니다. 이벤트의 필드를 따로 펼치는 것이 아닙니다.

## 17행

```r
  x
```

앞 조건에 걸리지 않은 x를 그대로 둡니다. R 함수는 마지막으로 계산한 값을 자동 반환하므로 return(x)를 쓰지 않아도 됩니다.

## 18행

```r
}
```

앞에서 시작한 함수·조건·반복의 중괄호 블록을 닫습니다.

## 20행

```r
read_events <- function(path) {
```

read_events()는 path라는 파일 경로를 받아 이벤트 목록을 반환합니다. 아직 이 단계에서 로그인 여부를 걸러내지 않습니다.

## 21행

```r
  lines <- readLines(path, warn = FALSE, encoding = "UTF-8")
```

readLines()는 파일을 줄마다 문자열로 읽습니다. lines는 문자열 벡터가 됩니다. encoding은 UTF-8로 해석하도록 지정합니다. warn=FALSE는 일부 읽기 경고를 숨깁니다.

## 22행

```r
  lines <- lines[nzchar(trimws(lines))]
```

trimws(lines)는 앞뒤 공백을 제거한 임시 값을 만들고 nzchar()가 글자 존재 여부를 TRUE/FALSE로 만듭니다. lines[...]는 TRUE 위치의 원래 줄만 고릅니다. 원래 줄 안의 공백을 전부 지우지는 않습니다.

## 23행

```r
  if (!length(lines)) return(list())
```

빈 줄 제거 뒤 길이가 0이면 빈 리스트를 즉시 반환합니다. !length(lines)는 0을 FALSE로 해석한 뒤 뒤집는 표현입니다. 초보자는 length(lines)==0으로 생각하면 쉽습니다.

## 24행

```r
  # 우선 파일 전체를 JSON으로 읽고, 실패하면 NDJSON으로 읽습니다.
```

주석입니다. # 뒤는 실행되지 않습니다. 우선 파일 전체를 JSON으로 읽고, 실패하면 NDJSON으로 읽습니다.

## 25행

```r
  parsed <- tryCatch(
```

tryCatch()는 안쪽 작업에 오류가 생겼을 때 실행할 대체 동작을 지정합니다. 결과를 parsed 변수에 저장합니다.

## 26행

```r
    jsonlite::fromJSON(paste(lines, collapse = "\n"), simplifyVector = FALSE),
```

paste(...,collapse="\n")는 줄들을 줄바꿈으로 이어 문서 하나로 만듭니다. jsonlite::fromJSON()의 ::는 jsonlite 패키지에 있는 함수를 직접 부르는 문법입니다. simplifyVector=FALSE는 JSON을 중첩 리스트 중심으로 유지합니다.

## 27행

```r
    error = function(e) NULL
```

error=function(e) NULL은 오류가 생기면 NULL을 반환하라는 뜻입니다. e는 발생한 오류 객체지만 여기서는 내용을 쓰지 않습니다.

## 28행

```r
  )
```

앞에서 시작한 함수 호출의 괄호를 닫습니다.

## 29행

```r
  if (!is.null(parsed)) return(event_list(parsed))
```

전체 문서 해석이 성공해 parsed가 NULL이 아니면 event_list()로 포장을 맞추고 즉시 반환합니다. 성공했다는 것은 JSON 문법 해석 성공이며 모든 필드의 정확성 보장은 아닙니다.

## 30행

```r
  result <- list()
```

result <- list()는 빈 목록을 만듭니다. 이후 줄별 이벤트를 이 목록에 이어 붙일 준비입니다.

## 31행

```r
  for (i in seq_along(lines)) {
```

seq_along(lines)는 줄 개수에 맞는 번호를 만듭니다. 3줄이면 1,2,3입니다. for는 i에 각 번호를 차례로 넣고 안쪽 코드를 반복합니다.

## 32행

```r
    item <- tryCatch(
```

이번 줄의 JSON 해석도 tryCatch()로 감쌉니다. 성공한 객체를 item에 저장합니다.

## 33행

```r
      jsonlite::fromJSON(lines[[i]], simplifyVector = FALSE),
```

lines[[i]]는 i번째 문자열 하나입니다. 첫 시도에서는 문서 전체를 읽었지만 여기서는 각 줄을 하나의 JSON 문서로 읽습니다. 이 형식이 NDJSON입니다.

## 34행

```r
      error = function(e) stop(sprintf("JSON 파싱 실패: 비어 있지 않은 %d번째 줄", i))
```

줄 해석에 실패하면 sprintf()로 오류 위치를 문장에 넣고 stop()합니다. %d 자리에 줄 번호가 들어갑니다. 번호는 빈 줄 제거 이후 기준입니다.

## 35행

```r
    )
```

앞에서 시작한 함수 호출의 괄호를 닫습니다.

## 36행

```r
    result <- c(result, event_list(item))
```

event_list(item)으로 이번 객체를 이벤트 목록으로 맞춥니다. c(result,...)가 기존 목록 뒤에 그 목록을 이어 붙여 result에 다시 저장합니다.

## 37행

```r
  }
```

앞에서 시작한 함수·조건·반복의 중괄호 블록을 닫습니다.

## 38행

```r
  result
```

반복이 끝난 result가 함수의 최종 반환값입니다. 보통 이벤트 하나하나가 원소로 들어 있는 리스트입니다.

## 39행

```r
}
```

앞에서 시작한 함수·조건·반복의 중괄호 블록을 닫습니다.

## 41행

```r
login_records <- function(events) {
```

login_records()는 이벤트 목록을 받아 네 열의 표를 만드는 함수입니다. JSON 파일을 읽는 역할은 앞의 read_events()가 담당합니다.

## 42행

```r
  # ConsoleLogin만 남깁니다. 로그인 실패와 성공을 모두 포함합니다.
```

주석입니다. # 뒤는 실행되지 않습니다. ConsoleLogin만 남깁니다. 로그인 실패와 성공을 모두 포함합니다.

## 43행

```r
  selected <- Filter(function(e) is.list(e) &&
```

Filter()는 조건 함수가 TRUE를 반환한 이벤트만 남깁니다. function(e)는 이벤트 하나를 받는 이름 없는 함수입니다. is.list(e)가 FALSE이면 &&의 오른쪽은 검사하지 않습니다.

## 44행

```r
    identical(e$eventName, "ConsoleLogin"), events)
```

identical()은 eventName이 문자열 ConsoleLogin과 같은지 확인합니다. 성공·실패 조건은 없으므로 로그인 시도 기록 둘 다 남깁니다. events는 Filter()가 순회할 입력 목록입니다.

## 45행

```r
  rows <- lapply(selected, function(e) {
```

lapply()는 selected의 각 이벤트에 함수를 적용합니다. 각 호출에서 한 행의 표를 반환하고 rows에는 그 표들이 리스트로 모입니다. 최종 표 자체가 바로 rows에 들어가는 것은 아닙니다.

## 46행

```r
    user <- text_value(e$userIdentity$userName)
```

e$userIdentity$userName은 이벤트 → 사용자 정보 → 이름 순으로 안쪽 값을 읽습니다. text_value()는 그 값을 문자열 하나 또는 NA로 정리합니다.

## 47행

```r
    if (is.na(user)) user <- text_value(e$userIdentity$arn)
```

사용자 이름이 NA이면 ARN을 대신 읽습니다. is.na()는 값이 빠졌는지 검사합니다. ARN도 없으면 사용자 열은 NA로 남습니다. 여기서는 별도 사용자명을 추정하지 않습니다.

## 48행

```r
    data.frame(
```

data.frame()은 행과 열이 있는 표를 만듭니다. 아래에서는 이벤트 한 건의 값을 네 개 열로 지정합니다.

## 49행

```r
      time = text_value(e$eventTime),
```

time 열에 이벤트 발생 시각을 넣습니다. 아직 날짜·시간 자료형으로 바꾸지 않고 원본 문자열을 사용합니다.

## 50행

```r
      user = user,
```

user=user에서 왼쪽 user는 새 표의 열 이름이고 오른쪽 user는 46~47행에서 계산한 변수입니다. 같은 이름이지만 역할이 다릅니다.

## 51행

```r
      ip = text_value(e$sourceIPAddress),
```

ip 열은 호출 출발지 sourceIPAddress입니다. 값이 없으면 text_value()가 NA를 반환합니다.

## 52행

```r
      result = text_value(e$responseElements$ConsoleLogin),
```

result 열은 responseElements 안의 ConsoleLogin 값입니다. 보통 Success 또는 Failure 문자열이며 값이 없으면 NA입니다.

## 53행

```r
      stringsAsFactors = FALSE
```

stringsAsFactors=FALSE는 문자열을 범주형 factor로 자동 변환하지 않도록 합니다. 최신 R 기본값도 FALSE지만 의도를 명시했습니다.

## 54행

```r
    )
```

앞에서 시작한 함수 호출의 괄호를 닫습니다.

## 55행

```r
  })
```

이름 없는 함수의 중괄호와 바깥 함수 호출 괄호를 닫습니다.

## 56행

```r
  if (!length(rows)) return(data.frame(
```

rows가 비어 있으면, 즉 로그인 이벤트가 한 건도 없으면 바로 빈 표를 반환합니다.

## 57행

```r
    time = character(), user = character(), ip = character(), result = character()
```

character()는 길이 0인 문자열 벡터입니다. 네 열 모두 길이 0이므로 표는 헤더만 있고 0행입니다. character()와 빈 문자열 한 개 ""는 다릅니다.

## 58행

```r
  ))
```

빈 data.frame() 생성과 return() 호출의 괄호를 차례로 닫습니다.

## 59행

```r
  output <- do.call(rbind, rows)
```

do.call(rbind,rows)는 목록에 들어 있는 표들을 rbind()의 인자로 전달하여 위아래로 합칩니다. 이벤트가 2개면 보통 1행 표 두 개가 2행 표 하나가 됩니다.

## 60행

```r
  # CloudTrail UTC ISO 형식의 원본 시각 문자열을 오름차순으로 정렬합니다.
```

주석입니다. # 뒤는 실행되지 않습니다. CloudTrail UTC ISO 형식의 원본 시각 문자열을 오름차순으로 정렬합니다.

## 61행

```r
  output[order(output$time, na.last = TRUE), , drop = FALSE]
```

order(output$time)는 시각 문자열을 정렬할 행 번호를 구합니다. output[행번호, ,drop=FALSE]는 그 순서의 행과 모든 열을 선택합니다. 쉼표 뒤 빈칸은 모든 열이고, drop=FALSE는 1행이어도 표 형태를 유지하게 합니다. 이 표현이 함수의 반환값입니다.

## 62행

```r
}
```

앞에서 시작한 함수·조건·반복의 중괄호 블록을 닫습니다.

## 64행

```r
if (sys.nframe() == 0) {
```

직접 Rscript로 실행할 때 이 실행부를 동작시키는 조건입니다. 다른 R 코드에서 source()로 불러올 때는 일반적으로 함수 정의만 재사용하고 실행부는 건너뜁니다.

## 65행

```r
  args <- commandArgs(trailingOnly = TRUE)
```

commandArgs(trailingOnly=TRUE)는 명령줄에서 스크립트 이름 뒤에 넣은 인자만 문자열 벡터로 받습니다. args라는 이름의 변수에 저장합니다.

## 66행

```r
  if (!length(args)) stop("사용법: Rscript login_records.R 로그.json [출력.csv]")
```

입력 경로 인자가 없으면 사용법을 안내하고 중단합니다. 대괄호 [출력.csv]는 사용법에서 선택 사항을 뜻하는 표기이며 실제 명령에 대괄호를 쓰지 않습니다.

## 67행

```r
  destination <- if (length(args) >= 2) args[[2]] else "output/login_records.csv"
```

인자가 2개 이상이면 두 번째 값을 출력 경로로 쓰고, 그렇지 않으면 기본 경로를 씁니다. if (...) 값 else 값도 R에서는 결과를 돌려주는 표현식이므로 destination에 저장할 수 있습니다.

## 68행

```r
  records <- login_records(read_events(args[[1]]))
```

안쪽 read_events(args[[1]])가 먼저 실행됩니다. 첫 인자인 입력 파일을 목록으로 읽고, 그 결과를 바깥 login_records()에 넣어 최종 표 records를 만듭니다.

## 69행

```r
  dir.create(dirname(destination), recursive = TRUE, showWarnings = FALSE)
```

dirname(destination)은 출력 파일의 부모 폴더입니다. dir.create(recursive=TRUE)는 필요한 중간 폴더까지 만듭니다. showWarnings=FALSE는 폴더가 이미 있을 때 등의 경고를 줄입니다.

## 70행

```r
  write.csv(records, destination, row.names = FALSE, na = "", fileEncoding = "UTF-8")
```

write.csv()가 records를 CSV 파일로 기록합니다. row.names=FALSE는 별도 행 번호 열을 빼고, na=""는 누락값을 빈칸으로, fileEncoding="UTF-8"는 저장 인코딩을 지정합니다.

## 71행

```r
  print(records, row.names = FALSE)
```

print()는 표를 R 콘솔이나 터미널 화면에 출력합니다. row.names=FALSE는 표시용 행 번호를 숨깁니다. 이 함수는 CSV를 저장하는 역할이 아닙니다.

## 72행

```r
  cat(sprintf("로그인 기록 %d건 저장: %s\n", nrow(records), destination))
```

nrow(records)는 행 수입니다. sprintf()가 %d에 행 수, %s에 저장 경로를 넣고 \n으로 줄바꿈을 붙입니다. cat()이 완성된 문장을 화면에 출력합니다.

## 73행

```r
}
```

앞에서 시작한 함수·조건·반복의 중괄호 블록을 닫습니다.
