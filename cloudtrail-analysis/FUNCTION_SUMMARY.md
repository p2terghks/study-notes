# CloudTrail 함수·조건문·반복문 상세 요약본
현재 핵심 R 코드 3파일·135줄을 기준으로 작성했습니다. 원본 함수 7개와 실행 블록 2개를 구분하며, 테스트·문서는 줄 수에서 제외합니다.
## 먼저 보는 실행 흐름
파일 경로 → read_events → event_list → 이벤트 목록 → login_records → 네 열 표 → CSV 저장 / failure_counts → plot_login_failures → Plots 또는 PNG
함수 정의는 일을 준비하는 단계이고 호출은 실제 일을 시키는 단계입니다. source("failure_charts.R")만 실행하면 그래프는 아직 나오지 않습니다.

## text_value(x)
필드 하나를 문자열 하나 또는 NA로 맞추기
- 입력: 문자열·NULL·길이 0 벡터
- 출력: 문자열 1개 또는 NA_character_
- 예시: text_value(NULL) → NA / text_value("Failure") → "Failure"

```r
text_value <- function(x) {
  if (is.null(x) || length(x) == 0) NA_character_ else as.character(x[[1]])
}
```

### 한 줄씩 읽기
- **8행**: function(x)는 x라는 값을 받는 함수를 만듭니다. <-는 이 함수에 text_value라는 이름을 붙입니다. 정의할 때가 아니라 호출할 때 본문이 실행됩니다.
- **9행**: x가 NULL이거나 길이 0이면 NA_character_를 반환합니다. ||는 왼쪽이 TRUE일 때 오른쪽을 검사하지 않는 OR입니다. 값이 있으면 [[1]]로 첫 원소를 꺼내 문자열로 바꿉니다. 이 표현식이 마지막이므로 자동 반환됩니다.
- **10행**: 이 함수 또는 조건 블록을 닫습니다. 함수라면 마지막으로 계산한 값이 반환됩니다.

## event_list(x)
문서 포장을 통일해 이벤트 하나씩 처리할 준비
- 입력: 해석된 JSON list
- 출력: 이벤트들을 담은 list
- 예시: Records 문서 → Records 안의 목록 / 단일 이벤트 → list(이벤트)

```r
event_list <- function(x) {
  if (!is.list(x)) stop("JSON 객체 또는 배열이 필요합니다.")
  if (!is.null(x$Records)) return(x$Records)
  if (!is.null(x$eventName)) return(list(x))
  x
}
```

### 한 줄씩 읽기
- **13행**: event_list(x)는 해석된 JSON 객체를 받습니다. 같은 이름 x라도 text_value의 x와는 별도의 매개변수입니다.
- **14행**: is.list(x)는 목록인지 검사합니다. ! 때문에 목록이 아닌 경우 TRUE가 되어 stop()으로 중단합니다. 예: event_list(10)은 오류입니다.
- **15행**: Records가 NULL이 아니면 포장 안의 이벤트 목록만 return()으로 즉시 반환합니다. 그 아래 줄은 실행하지 않습니다.
- **16행**: Records는 없고 eventName이 있으면 단일 이벤트로 판단합니다. list(x)로 감싸 이벤트 한 개짜리 목록을 반환합니다.
- **17행**: 위 조건에서 반환되지 않은 경우 x를 그대로 반환합니다. 이미 이벤트 배열인 입력이 이 경로를 사용합니다. 완전한 스키마 검증은 하지 않습니다.
- **18행**: 이 함수 또는 조건 블록을 닫습니다. 함수라면 마지막으로 계산한 값이 반환됩니다.

## read_events(path)
전체 JSON을 먼저 읽고 실패하면 한 줄씩 읽기
- 입력: 입력 파일 경로 character 1개
- 출력: 이벤트 목록 list
- 예시: 빈 파일 → list() / 잘못된 NDJSON 줄 → 오류 중단

```r
read_events <- function(path) {
  lines <- readLines(path, warn = FALSE, encoding = "UTF-8")
  lines <- lines[nzchar(trimws(lines))]
  if (!length(lines)) return(list())
  # 우선 파일 전체를 JSON으로 읽고, 실패하면 NDJSON으로 읽습니다.
  parsed <- tryCatch(
    jsonlite::fromJSON(paste(lines, collapse = "\n"), simplifyVector = FALSE),
    error = function(e) NULL
  )
  if (!is.null(parsed)) return(event_list(parsed))
  result <- list()
  for (i in seq_along(lines)) {
    item <- tryCatch(
      jsonlite::fromJSON(lines[[i]], simplifyVector = FALSE),
      error = function(e) stop(sprintf("JSON 파싱 실패: 비어 있지 않은 %d번째 줄", i))
    )
    result <- c(result, event_list(item))
  }
  result
}
```

### 한 줄씩 읽기
- **20행**: path라는 파일 경로 문자열을 받는 함수입니다. 예: read_events("data/logs.json").
- **21행**: readLines()는 UTF-8 파일을 줄별 문자열 벡터로 읽습니다. 아직 JSON의 필드를 꺼낼 수 있는 상태가 아닙니다. warn=FALSE는 불완전한 마지막 줄 등에 대한 경고를 줄입니다.
- **22행**: trimws()로 공백을 뺀 검사값을 만들고 nzchar()로 남은 문자가 있는지 확인합니다. TRUE인 줄의 원문만 남깁니다. 원문 전체를 trim해서 저장하는 코드는 아닙니다.
- **23행**: length(lines)가 0이면 !0이 TRUE가 됩니다. 빈 파일은 list()를 즉시 반환해 아래 파싱·반복 작업을 생략합니다.
- **24행**: 주석입니다. 실행되지 않으며 다음 코드의 의도나 실행 방법을 알려 줍니다.
- **25행**: tryCatch()가 해석 작업의 오류를 받도록 시작합니다. 결과를 parsed에 저장합니다.
- **26행**: paste(..., collapse="\n")로 모든 줄을 하나의 문서로 합칩니다. jsonlite::는 패키지 안의 함수를 지정합니다. fromJSON()이 글자를 R 객체로 해석하고 simplifyVector=FALSE는 list 중심 구조를 유지합니다.
- **27행**: 전체 문서 해석에서 오류가 나면 error 함수가 오류 객체 e를 받아 NULL을 반환합니다. 여기서는 e를 읽지 않고, 다음 NDJSON 방식으로 넘어갈 신호만 만듭니다.
- **28행**: tryCatch() 호출을 닫습니다. 해석 성공 객체 또는 오류 처리 함수가 반환한 NULL이 parsed에 저장됩니다.
- **29행**: parsed가 NULL이 아니면 전체 JSON 해석 성공입니다. event_list()로 구조를 통일해 반환하고 함수 실행을 끝냅니다.
- **30행**: 전체 해석이 실패한 경로에서만 실행됩니다. 한 줄씩 해석한 이벤트를 누적할 빈 목록을 준비합니다.
- **31행**: seq_along(lines)는 1부터 줄 개수까지의 번호를 만듭니다. for는 i를 그 번호로 바꾸며 본문을 반복합니다. 줄이 3개면 i는 1, 2, 3입니다.
- **32행**: 이번 한 줄을 읽는 작업에도 tryCatch()를 적용합니다. 결과를 item에 저장합니다.
- **33행**: lines[[i]]는 i번째 줄 문자열 하나입니다. NDJSON은 한 줄에 완전한 JSON이 하나씩 있어야 이 해석이 성공합니다.
- **34행**: 이번 줄도 해석에 실패하면 sprintf()로 i를 포함한 오류 문구를 만들고 stop()으로 전체 처리를 중단합니다. %d는 정수, i는 빈 줄 제거 후의 번호입니다.
- **35행**: 이번 줄의 tryCatch()를 닫습니다. 성공한 JSON 객체가 item에 저장됩니다.
- **36행**: event_list(item)으로 이번 줄의 구조도 통일하고 c()로 result 끝에 붙입니다. 목록 전체를 문자로 바꾸거나 깊이 전부 펼치는 코드가 아닙니다.
- **37행**: for 본문의 끝입니다. 남은 줄이 있으면 i를 다음 번호로 바꿔 32행으로 돌아갑니다.
- **38행**: 누적된 이벤트 목록을 함수의 마지막 값으로 반환합니다.
- **39행**: 이 함수 또는 조건 블록을 닫습니다. 함수라면 마지막으로 계산한 값이 반환됩니다.

## login_records(events)
ConsoleLogin만 선택해 네 열의 표로 만들기
- 입력: 이벤트 목록 list
- 출력: time·user·ip·result data.frame
- 예시: API 이벤트 제외 / 이름 없으면 ARN / 로그인 없음 → 0행

```r
login_records <- function(events) {
  # ConsoleLogin만 남깁니다. 로그인 실패와 성공을 모두 포함합니다.
  selected <- Filter(function(e) is.list(e) &&
    identical(e$eventName, "ConsoleLogin"), events)
  rows <- lapply(selected, function(e) {
    user <- text_value(e$userIdentity$userName)
    if (is.na(user)) user <- text_value(e$userIdentity$arn)
    data.frame(
      time = text_value(e$eventTime),
      user = user,
      ip = text_value(e$sourceIPAddress),
      result = text_value(e$responseElements$ConsoleLogin),
      stringsAsFactors = FALSE
    )
  })
  if (!length(rows)) return(data.frame(
    time = character(), user = character(), ip = character(), result = character()
  ))
  output <- do.call(rbind, rows)
  # CloudTrail UTC ISO 형식의 원본 시각 문자열을 오름차순으로 정렬합니다.
  output[order(output$time, na.last = TRUE), , drop = FALSE]
}
```

### 한 줄씩 읽기
- **41행**: 이벤트 여러 개를 담은 목록 events를 받습니다. 입력 형식이 이미 event_list()로 통일됐다는 전제에서 반복합니다.
- **42행**: 주석입니다. 실행되지 않으며 다음 코드의 의도나 실행 방법을 알려 줍니다.
- **43행**: Filter()가 events의 원소를 하나씩 익명함수 function(e)에 전달합니다. is.list(e)가 FALSE이면 &&가 뒤의 필드 검사를 생략합니다.
- **44행**: e$eventName이 대소문자까지 ConsoleLogin과 정확히 같은지 검사합니다. 두 조건이 TRUE인 이벤트만 selected에 남습니다. 일반 API 이벤트는 제외됩니다.
- **45행**: lapply()는 selected의 각 로그인 이벤트 e를 처리한 뒤 결과들을 목록으로 모읍니다. 여기서는 한 행짜리 표들이 rows에 모입니다.
- **46행**: 중첩 필드 e$userIdentity$userName을 꺼내 text_value()에 전달합니다. 없으면 user는 NA가 됩니다.
- **47행**: user가 NA일 때만 ARN을 대신 읽습니다. 이름이 있으면 이 대입을 건너뜁니다. ARN도 없으면 NA가 유지됩니다. 빈 문자열은 NA가 아니므로 별도 대체하지 않습니다.
- **48행**: 한 로그인 이벤트를 data.frame 한 행으로 만들기 시작합니다.
- **49행**: eventTime을 문자열로 꺼내 time 열에 넣습니다. 이 단계에서는 시간 자료형으로 변환하지 않습니다.
- **50행**: 앞에서 선택한 사용자명 또는 ARN을 user 열에 넣습니다. 왼쪽 user는 열 이름이고 오른쪽 user는 지역변수 값입니다.
- **51행**: sourceIPAddress를 문자열로 읽어 ip 열에 넣습니다.
- **52행**: responseElements 안의 ConsoleLogin 값을 읽어 result 열에 넣습니다. 보통 Success 또는 Failure이며 누락이면 NA입니다.
- **53행**: 문자열을 범주형 factor로 자동 변환하지 않도록 지정합니다.
- **54행**: 현재 이벤트의 data.frame()을 완성합니다. 익명함수의 마지막 표현식이라 이 한 행이 반환됩니다.
- **55행**: 익명함수 본문과 lapply()를 닫습니다. 모든 한 행짜리 표가 rows 목록에 모입니다.
- **56행**: rows 길이가 0이면 로그인 이벤트가 없는 경우입니다. 열 형식이 정해진 빈 표를 즉시 반환합니다.
- **57행**: character()는 원소 0개인 문자열 벡터입니다. 네 열이 모두 길이 0이므로 0행 표가 됩니다. 빈 문자열 하나인 ""와 다릅니다.
- **58행**: 빈 data.frame 생성과 return()을 닫습니다.
- **59행**: do.call(rbind, rows)는 rows 안의 표들을 rbind()의 인자로 전달해 세로로 연결합니다.
- **60행**: 주석입니다. 실행되지 않으며 다음 코드의 의도나 실행 방법을 알려 줍니다.
- **61행**: order()가 시간 문자열 오름차순의 행 번호를 만듭니다. NA는 뒤로 보냅니다. [행, 열]의 빈 열 자리는 모든 열이며 drop=FALSE는 data.frame 형태를 유지합니다. 동일한 UTC ISO 표현을 전제로 한 문자열 정렬입니다.
- **62행**: 이 함수 또는 조건 블록을 닫습니다. 함수라면 마지막으로 계산한 값이 반환됩니다.

## failure_counts(records)
실패 행과 유효한 시각만 골라 빈도 계산
- 입력: 로그인 표 data.frame
- 출력: total·invalid_time·daily·hourly list
- 예시: 실패 3건 중 시각 오류 1건 → total=3, 막대 합계=2

```r
failure_counts <- function(records) {
  failed <- records[!is.na(records$result) & records$result == "Failure", , drop = FALSE]
  times <- as.POSIXct(failed$time, format = "%Y-%m-%dT%H:%M:%OSZ", tz = "UTC")
  valid <- times[!is.na(times)]
  daily <- table(format(valid, "%Y-%m-%d", tz = "UTC"))
  hourly <- table(factor(format(valid, "%H", tz = "UTC"), levels = sprintf("%02d", 0:23)))
  list(total = nrow(failed), invalid_time = sum(is.na(times)), daily = daily, hourly = hourly)
}
```

### 한 줄씩 읽기
- **2행**: 네 열을 가진 로그인 표 records를 받는 집계 함수를 정의합니다. 실제 사용하는 열은 time과 result입니다.
- **3행**: !is.na()와 result=="Failure"를 &로 행마다 결합해 실패 행만 남깁니다. Success와 누락된 결과는 제외합니다. drop=FALSE로 표를 유지합니다.
- **4행**: 문자열 시각을 POSIXct 시간 자료형으로 바꿉니다. %Y·%m·%d는 연·월·일, %H·%M·%OS는 시·분·초이며 %OS는 소수점 초도 받습니다. Z는 형식의 문자이고 UTC 시간대로 해석합니다.
- **5행**: is.na(times)가 FALSE인 시각만 선택합니다. 해석에 실패한 NA 시각은 valid에서 제외됩니다.
- **6행**: 유효한 시각을 UTC 연-월-일 문자열로 바꾸고 table()로 날짜마다 개수를 셉니다. 기록이 없는 날짜를 자동으로 추가하지 않습니다.
- **7행**: %H로 UTC 시각대 00~23을 뽑습니다. 0:23과 sprintf("%02d", ...)로 모든 시각대를 levels로 지정해 기록이 없는 시간도 0건으로 유지합니다. 모든 날짜를 합산합니다.
- **8행**: 실패 전체 수 total, 시각 누락·해석 실패 수 invalid_time, 날짜 빈도표 daily, 시각대 빈도표 hourly를 이름 붙은 list로 반환합니다. TRUE는 sum()에서 1로 계산됩니다.
- **9행**: 이 함수 또는 조건 블록을 닫습니다. 함수라면 마지막으로 계산한 값이 반환됩니다.

## plot_login_failures(records)
집계를 날짜별·시각대별 막대로 표시
- 입력: 로그인 표 data.frame
- 출력: 그래프 출력 + invisible(counts)
- 예시: 높이 5인치 미만 → 여백 축소 / 유효 실패 없음 → 안내 그림

```r
plot_login_failures <- function(records) {
  counts <- failure_counts(records)
  previous <- par(no.readonly = TRUE)
  on.exit(par(previous))
  par(mfrow = c(2, 1))
  # 작은 RStudio Plots 창에서도 여백이 그릴 영역을 넘지 않게 합니다.
  compact <- dev.size("in")[[2]] < 5
  par(mar = c(4, 4, 3, 1), oma = c(1, 0, 3, 0),
      mex = if (compact) 0.45 else 1, cex = if (compact) 0.7 else 1)
  if (length(counts$daily)) {
    positions <- barplot(counts$daily, col = "#d97745", border = NA,
      main = "Failed logins by date (UTC)", ylab = "Failure records",
      cex.names = 0.8, ylim = c(0, max(counts$daily) * 1.18))
    text(positions, counts$daily, labels = counts$daily, pos = 3, cex = 0.8)
  } else {
    plot.new()
    title("Failed logins by date (UTC)")
    text(0.5, 0.5, "No failed logins with a valid time")
  }
  barplot(counts$hourly, col = "#477fbb", border = NA,
    main = "Failed logins by hour of day (UTC, all dates)",
    xlab = "Hour (00-23 UTC)", ylab = "Failure records", cex.names = 0.8,
    ylim = c(0, max(1, counts$hourly) * 1.18))
  mtext(sprintf("Failed login records: %d | Missing/invalid time: %d", counts$total,
    counts$invalid_time), outer = TRUE, side = 3, line = 1, font = 2)
  mtext("Repeated source events are counted; missing/invalid times are omitted from bars.",
    outer = TRUE, side = 1, cex = 0.75)
  invisible(counts)
}
```

### 한 줄씩 읽기
- **12행**: 로그인 표를 받아 두 그래프를 그리는 함수를 정의합니다.
- **13행**: failure_counts(records)를 호출해 집계 목록을 counts에 받습니다. 이 함수 호출 전에는 그래프를 그리지 않습니다.
- **14행**: par()는 그래프 설정을 읽고 바꿉니다. no.readonly=TRUE는 나중에 복원 가능한 설정들만 previous에 보관하게 합니다.
- **15행**: 정상 종료 또는 오류로 함수가 끝날 때 par(previous)를 실행하도록 예약합니다. 여기서 즉시 복원하는 것은 아닙니다.
- **16행**: mfrow=c(2,1)은 2행 1열 배치입니다. 첫 그래프는 위, 두 번째는 아래에 그려집니다.
- **17행**: 주석입니다. 실행되지 않으며 다음 코드의 의도나 실행 방법을 알려 줍니다.
- **18행**: dev.size("in")은 장치의 가로·세로 크기를 인치로 반환합니다. [[2]]로 높이를 꺼내 5보다 작은지 비교한 TRUE/FALSE를 compact에 저장합니다.
- **19행**: mar는 각 그래프의 아래·왼쪽·위·오른쪽 여백, oma는 전체 그림의 바깥 여백을 지정합니다.
- **20행**: 작은 창이면 여백 계산 배율 mex를 0.45, 글자 배율 cex를 0.7로 줄입니다. 그 외는 1입니다. mfrow를 먼저 설정한 뒤 적용해 초기화 영향을 피합니다.
- **21행**: 날짜 빈도표 원소 수가 0이 아니면 TRUE가 됩니다. 유효한 실패 시각이 한 개 이상 있을 때 날짜별 막대를 그립니다.
- **22행**: 날짜 빈도표를 막대그래프로 그리고 막대 중심의 x좌표들을 positions에 저장합니다. border=NA는 테두리를 없앱니다.
- **23행**: main은 그림 제목, ylab은 세로축 이름입니다.
- **24행**: cex.names는 범주 이름 크기입니다. ylim은 세로축 범위이며 최대 건수보다 18% 높게 잡아 숫자를 쓸 공간을 둡니다.
- **25행**: 막대 중심 positions와 높이 counts$daily에 건수 labels를 씁니다. pos=3은 그 지점 위쪽을 뜻합니다.
- **26행**: 21행 조건이 FALSE이면 else 경로로 이동합니다. 날짜 막대를 그리는 위 코드는 실행하지 않습니다.
- **27행**: 유효한 실패 시각이 없는 경우 안내문을 담을 빈 그래프를 만듭니다.
- **28행**: 빈 그래프에도 날짜별 실패 그래프라는 제목을 붙입니다.
- **29행**: 빈 그래프의 중앙에 유효한 실패 시각이 없다는 문구를 씁니다.
- **30행**: 날짜 그래프의 if/else를 마칩니다. 그 다음 시간대 그래프는 두 경우 모두 실행합니다.
- **31행**: 24개 시각대의 빈도를 두 번째 막대그래프로 그립니다.
- **32행**: 시간대별 그래프 제목입니다. 모든 날짜의 같은 UTC 시각대를 더한 값임을 표시합니다.
- **33행**: 가로축은 UTC 시각, 세로축은 실패 기록 수입니다. cex.names는 시각대 라벨 크기입니다.
- **34행**: max(1, counts$hourly)는 모든 값이 0이어도 최대값을 적어도 1로 보장합니다. ylim=c(0,0)이 되는 상황을 막습니다.
- **35행**: sprintf()로 전체 실패 기록 수와 잘못된 시각 수를 제목 문구에 끼워 넣습니다.
- **36행**: outer=TRUE는 전체 그림의 바깥 여백에 씁니다. side=3은 위쪽, line=1은 위치, font=2는 굵은 글씨입니다.
- **37행**: 중복 기록은 세고 잘못된 시각은 막대에서 제외한다는 집계 기준 문구입니다.
- **38행**: side=1은 아래쪽 바깥 여백입니다. cex=0.75로 이 안내문 크기를 줄입니다.
- **39행**: invisible(counts)는 집계를 반환하지만 콘솔에 자동 출력하지 않습니다. x <- plot_login_failures(records)처럼 값은 받을 수 있습니다.
- **40행**: 이 함수 또는 조건 블록을 닫습니다. 함수라면 마지막으로 계산한 값이 반환됩니다.

## save_failure_chart(records, path)
같은 그래프를 PNG 파일로 기록
- 입력: 로그인 표 + 출력 경로 문자열
- 출력: PNG 파일 + invisible(path)
- 예시: path 생략 → output/login_failures.png

```r
save_failure_chart <- function(records, path = "output/login_failures.png") {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  png(path, width = 1400, height = 1000, res = 140, bg = "white")
  on.exit(dev.off())
  plot_login_failures(records)
  invisible(path)
}
```

### 한 줄씩 읽기
- **42행**: records와 출력 경로 path를 받는 저장 함수입니다. path를 생략하면 output/login_failures.png가 기본값입니다.
- **43행**: PNG 파일의 부모 폴더를 만들며 중간 폴더도 함께 생성합니다.
- **44행**: png()가 새 그래프 출력 장치를 엽니다. 이후 그림은 1400×1000 픽셀, 140dpi, 흰 배경의 파일로 들어갑니다. 화면의 Plots 표시와 파일 저장은 구분됩니다.
- **45행**: 함수 종료 때 dev.off()로 방금 연 PNG 장치를 닫아 파일 기록을 마무리합니다.
- **46행**: 같은 집계·그리기 함수를 호출합니다. 별도의 다른 집계 방법으로 파일을 만드는 것이 아닙니다.
- **47행**: 저장 경로를 조용히 반환합니다. 자동으로 그림 파일을 열지는 않습니다.
- **48행**: 이 함수 또는 조건 블록을 닫습니다. 함수라면 마지막으로 계산한 값이 반환됩니다.

## login_records.R 직접 실행 블록
터미널 인자를 받아 추출 CSV 저장
- 입력: Rscript 뒤의 문자열 인자들
- 출력: CSV 파일과 콘솔 안내
- 예시: source()로 불러오면 이 블록은 건너뜀

```r
if (sys.nframe() == 0) {
  args <- commandArgs(trailingOnly = TRUE)
  if (!length(args)) stop("사용법: Rscript login_records.R 로그.json [출력.csv]")
  destination <- if (length(args) >= 2) args[[2]] else "output/login_records.csv"
  records <- login_records(read_events(args[[1]]))
  dir.create(dirname(destination), recursive = TRUE, showWarnings = FALSE)
  write.csv(records, destination, row.names = FALSE, na = "", fileEncoding = "UTF-8")
  print(records, row.names = FALSE)
  cat(sprintf("로그인 기록 %d건 저장: %s\n", nrow(records), destination))
}
```

### 한 줄씩 읽기
- **64행**: sys.nframe()==0은 직접 실행된 경우인지 구분합니다. 일반적인 Rscript 직접 실행이면 저장 작업을 하고 source()로 불러오면 이 블록을 건너뜁니다.
- **65행**: 명령 뒤에 붙인 인자만 문자열 벡터로 받습니다. 예: c("data/logs.json", "output/logins.csv").
- **66행**: 인자가 하나도 없으면 사용법을 알려주고 중단합니다. 입력 경로 없는 args[[1]] 접근을 막습니다.
- **67행**: 인자가 2개 이상이면 두 번째를 저장 경로로 쓰고, 아니면 기본 경로를 씁니다. if 결과를 destination에 대입하는 표현식입니다.
- **68행**: 안쪽 read_events(args[[1]])가 먼저 실행됩니다. 반환된 이벤트 목록을 login_records()가 받아 표 records를 만듭니다.
- **69행**: dirname()이 출력 파일의 부모 폴더를 구합니다. recursive=TRUE는 중간 폴더도 만들고 showWarnings=FALSE는 이미 있는 폴더 등의 경고를 줄입니다.
- **70행**: CSV로 저장합니다. row.names=FALSE는 별도 행 번호 열을 빼고, na=""는 결측값을 빈칸으로 쓰며 UTF-8로 저장합니다. 같은 경로의 기존 결과는 덮어씁니다.
- **71행**: 로그인 표를 콘솔에 출력합니다. CSV 저장과 별개의 화면 출력입니다.
- **72행**: nrow(records)로 행 수를 구하고 sprintf()의 %d에 건수, %s에 경로를 넣습니다. cat()이 완성된 안내문과 줄바꿈을 출력합니다.
- **73행**: 이 함수 또는 조건 블록을 닫습니다. 함수라면 마지막으로 계산한 값이 반환됩니다.

## run_analysis.R 통합 실행
입력부터 CSV·PNG 저장까지 순서대로 연결
- 입력: 입력 파일 경로 + 선택적 출력 폴더
- 출력: login_records.csv와 login_failures.png
- 예시: Rscript run_analysis.R data/logs.json output

```r
# 프로젝트 폴더에서 실행: Rscript run_analysis.R 로그.json [출력폴더]
source("login_records.R")
source("failure_charts.R")
args <- commandArgs(trailingOnly = TRUE)
if (!length(args)) stop("사용법: Rscript run_analysis.R 로그.json [출력폴더]")
output_dir <- if (length(args) >= 2) args[[2]] else "output"
records <- login_records(read_events(args[[1]]))
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
write.csv(records, file.path(output_dir, "login_records.csv"), row.names = FALSE,
  na = "", fileEncoding = "UTF-8")
save_failure_chart(records, file.path(output_dir, "login_failures.png"))
print(records, row.names = FALSE)
cat(sprintf("로그인 %d건 / 실패 %d건 / 저장 위치: %s\n", nrow(records),
  sum(records$result == "Failure", na.rm = TRUE), output_dir))
```

### 한 줄씩 읽기
- **1행**: 주석입니다. 실행되지 않으며 다음 코드의 의도나 실행 방법을 알려 줍니다.
- **2행**: 추출 함수들이 들어 있는 파일을 실행해 현재 세션에서 사용할 수 있게 합니다. 상대 경로이므로 프로젝트 폴더에서 실행해야 합니다.
- **3행**: 집계·그래프·PNG 저장 함수를 불러옵니다.
- **4행**: 터미널 실행 인자들을 args에 저장합니다. 첫 번째는 입력 파일, 두 번째는 선택적인 출력 폴더입니다.
- **5행**: 입력 파일 인자가 없으면 사용법 오류로 중단합니다.
- **6행**: 인자가 2개 이상이면 두 번째를 출력 폴더로 쓰고, 없으면 output을 사용합니다.
- **7행**: 입력 경로 → 이벤트 목록 → 로그인 표 순서로 안쪽 함수부터 호출합니다.
- **8행**: 결과를 쓸 폴더를 만듭니다.
- **9행**: file.path()로 폴더와 파일명을 연결하고 로그인 전체 표를 CSV로 저장합니다. 행 번호는 넣지 않습니다.
- **10행**: CSV의 NA는 빈칸으로 기록하고 UTF-8로 저장합니다.
- **11행**: 출력 폴더에 실패 기록 집계 PNG를 저장합니다. 이 실행 파일은 Plots를 띄우는 대신 파일을 만드는 용도입니다.
- **12행**: 성공·실패를 포함한 로그인 표를 콘솔에 출력합니다.
- **13행**: nrow(records)로 전체 로그인 기록 수를 구하고 안내문을 만들기 시작합니다.
- **14행**: result=="Failure"로 실패 여부 벡터를 만들고 sum()으로 TRUE를 셉니다. na.rm=TRUE는 NA를 빼고 계산합니다. 마지막으로 cat()으로 저장 위치까지 출력합니다.

## 모든 주요 조건의 참·거짓 경로
| 위치 | 조건 | 참일 때 | 거짓일 때 | 필요한 이유 |
| --- | --- | --- | --- | --- |
| login_records.R:3 | !requireNamespace(...) | jsonlite가 없음 → 오류·설치 방법 안내 | 설치되어 있음 → 함수 정의 계속 | 패키지 없이 해석을 시작하지 않기 |
| login_records.R:9 | is.null(x) \|\| length(x)==0 | 값 없음 → NA_character_ | 첫 값을 문자열로 반환 | 빠진 필드도 표 한 칸을 유지 |
| login_records.R:14 | !is.list(x) | 목록 아님 → stop() | 다음 구조 검사 | 숫자·문자 자체를 이벤트 목록으로 받지 않기 |
| login_records.R:15 | !is.null(x$Records) | Records 안의 목록 즉시 반환 | 다음 조건으로 | 바깥 포장 벗기기 |
| login_records.R:16 | !is.null(x$eventName) | 단일 이벤트를 list()로 감싸 반환 | x 그대로 반환 | 한 이벤트도 목록 단위로 처리 |
| login_records.R:23 | !length(lines) | 빈 목록 반환·종료 | 전체 JSON 해석 시도 | 빈 파일 처리 |
| login_records.R:25–29 | 전체 fromJSON 성공 여부 | 성공 → parsed 객체 → 정규화 후 반환 | 오류 → NULL → NDJSON 반복 | 두 파일 형식 모두 지원 |
| login_records.R:32–35 | 한 줄 fromJSON 성공 여부 | 성공 → item 누적 | 오류 → 해당 줄 안내 후 중단 | 손상된 줄을 조용히 버리지 않기 |
| login_records.R:43–44 | is.list(e) && identical(...) | 목록이면서 ConsoleLogin → 선택 | 목록 아니거나 이름 불일치 → 제외 | 로그인 이벤트만 선택 |
| login_records.R:47 | is.na(user) | userName 대신 ARN 사용 | userName 유지 | 사용자명 누락 보완 |
| login_records.R:56 | !length(rows) | 네 열의 빈 표 반환 | rbind()로 행 합치기 | 로그인이 없어도 출력 열 유지 |
| login_records.R:64 | sys.nframe()==0 | 일반적인 Rscript 직접 실행 → 저장 블록 | source 호출 안 → 저장 블록 생략 | 함수 정의와 실행 분리 |
| login_records.R:66 / run_analysis.R:5 | !length(args) | 인자 없음 → 사용법 오류 | 입력 인자 사용 | 입력 파일 없이 실행 방지 |
| login_records.R:67 / run_analysis.R:6 | length(args)>=2 | 사용자가 지정한 출력 경로 사용 | 기본 경로 사용 | 출력 위치를 선택적으로 받기 |
| failure_charts.R:3 | !is.na(result) & result=="Failure" | 각 행을 실패 표에 포함 | Success·NA 행 제외 | 행별 실패 필터 |
| failure_charts.R:5 | !is.na(times) | 유효 시각을 valid에 포함 | 잘못된 시각 제외 | 빈도표의 시각을 신뢰할 수 있게 하기 |
| failure_charts.R:18–20 | 장치 높이 < 5 | 작은 창 → mex 0.45 / cex 0.7 | 일반 창 → 둘 다 1 | 그릴 공간보다 여백이 커지는 오류 완화 |
| failure_charts.R:21 | length(counts$daily) | 유효 실패 날짜 있음 → 막대·건수 | 없음 → 빈 그림과 안내문 | 빈 데이터에서 max() 등 문제 피하기 |
| failure_charts.R:34 | max(1, counts$hourly) | 별도 if가 아니라 최대값의 최솟값을 1로 보장 | 모두 0이어도 y축 상한 0을 피함 | 0건 그래프도 그리기 |

## R 기초 문법 사전
| 문법 | 뜻 | 프로젝트에서의 사용 |
| --- | --- | --- |
| function(x) | 입력 이름 x를 받는 함수를 정의 | text_value라는 함수 안에서 x는 받은 필드 값 |
| <- | 오른쪽 결과를 왼쪽 이름에 저장 | parsed <- ... |
| return(x) | 값을 반환하고 현재 함수 즉시 종료 | Records가 있으면 아래 조건 생략 |
| 마지막 표현식 | return 없이도 마지막 계산값 자동 반환 | event_list 마지막 x, read_events 마지막 result |
| if (...) ... else ... | 조건에 맞는 한 경로만 실행 | text_value에서는 값이 없으면 NA, 있으면 문자열 |
| for (i in ...) | i를 바꿔 같은 본문 반복 | NDJSON 각 줄 읽기 |
| Filter(function(e), events) | TRUE인 원소만 원래 모습으로 남김 | 이벤트 목록 → 로그인 이벤트 목록 |
| lapply(selected, function(e)) | 원소마다 작업하고 결과를 목록으로 모음 | 로그인 목록 → 한 행 표들의 목록 |
| tryCatch(..., error=function(e) ...) | 오류 발생 시 error 함수 실행 | 첫 해석 오류는 NULL로, 줄 해석 오류는 stop으로 |
| on.exit(...) | 현재 함수가 끝날 때 정리 작업 예약 | 그래프 설정 복원, PNG 장치 닫기 |
| NULL / NA / "" / character() | 값 없음 / 결측값 / 빈 문자열 하나 / 문자열 원소 0개 | 서로 구분해야 필드 누락과 빈 표를 다룰 수 있음 |
| $ / [[ ]] / [ ] | 이름으로 필드 / 원소 하나 / 부분 선택 | e$eventName / lines[[i]] / valid[조건] |
| [행, 열] | 표의 행과 열을 선택 | records[조건, , drop=FALSE]는 모든 열 유지 |
| ! / & / && / \|\| | 반전 / 원소별 AND / 단락 AND / 단락 OR | &는 여러 행 비교, &&는 원소 하나의 조건 연결 |
| == / identical() | 값 비교 / 객체의 정확한 일치 검사 | result=="Failure"는 행별, identical()은 이벤트 이름 하나 |
| length() / nrow() | 벡터·목록 원소 수 / 표의 행 수 | length(records)는 열 개수, nrow(records)는 로그인 기록 수 |
| list() / data.frame() / table() | 다양한 자료 묶음 / 같은 길이의 열로 된 표 / 값별 빈도표 | JSON 객체 / 로그인 4열 / 날짜별 실패 횟수 |
| sum(TRUE,FALSE,...) | 논리값 TRUE를 1, FALSE를 0으로 합산 | 실패 여부 벡터의 TRUE 개수 |
| drop=FALSE | 선택 후에도 표 차원을 유지 | 한 행·한 열이어도 data.frame 유지 |
| invisible(x) | 값을 반환하되 자동 출력하지 않음 | counts <- plot_login_failures(records)로 받을 수 있음 |
| source() / Rscript | 세션에서 파일 실행 / 터미널에서 독립 실행 | source로 함수 정의 후 직접 호출; runner는 터미널 인자 필요 |

## 변수와 매개변수 상세 표
| 이름 | 위치 | 자료형 | 예시 |
| --- | --- | --- | --- |
| x | text_value의 매개변수 | 필드 값·NULL | "Failure" 또는 NULL |
| x | event_list의 매개변수 | JSON list | Records 문서·이벤트 배열·단일 이벤트 |
| path | 입력 또는 출력 매개변수 | 문자열 하나 | "data/logs.json" 또는 "output/chart.png" |
| lines | read_events 내부 | 줄별 character 벡터 | c("{", "...", "}") |
| parsed | read_events 내부 | 전체 JSON 객체 또는 NULL | 해석 성공이면 list / 오류이면 NULL |
| item | for 내부 | 이번 한 줄의 JSON 객체 | NDJSON 이벤트 하나 또는 한 줄 문서 |
| i | for 반복변수 | 현재 줄 번호 정수 | 1 → 2 → 3 |
| e | Filter/lapply의 매개변수 | 이벤트 한 개 | e$eventName == "ConsoleLogin" |
| e | tryCatch error의 매개변수 | 오류 객체 | 해석 실패의 오류 정보. 이벤트 e와 다른 값 |
| result | read_events 내부 | 이벤트를 누적한 list | list(event1, event2) |
| result | 로그인 표의 열 | 성공/실패 문자열 | Success·Failure·NA |
| rows | login_records 내부 | 한 행짜리 표들의 list | list(한행표, 한행표) |
| records | 여러 함수의 매개변수 | 네 열의 data.frame | time/user/ip/result |
| counts | plot_login_failures 내부 | 집계 네 항목 list | total/invalid_time/daily/hourly |
| compact | plot_login_failures 내부 | 논리값 하나 | TRUE: 높이 5인치 미만 |

## 반복 처리 순서
for는 파일 전체 JSON 해석이 실패한 경우에만 각 줄을 읽습니다. i=1,2,3으로 바뀔 때마다 item을 해석하고 event_list(item)을 result 뒤에 붙입니다. 중간 줄이 잘못됐으면 stop()에서 중단합니다.
Filter는 이벤트를 선택하고, lapply는 선택한 이벤트 각각을 한 행 표로 변환합니다. do.call(rbind, rows)는 그 표들을 세로로 합칩니다.

## 정규화하지 않은 입력의 흐름
Records 문서 → 바깥 목록을 이벤트로 착각 → e$eventName은 NULL → 로그인 비교 FALSE → 표 0행. 단일 이벤트도 필드가 반복되어 일반적인 CloudTrail 구조에서는 0행이 됩니다. 이미 이벤트 배열인 경우에는 정규화 없이도 정상 처리될 수 있습니다.
fromJSON은 글자를 객체로 해석하고, event_list는 객체의 바깥 구조를 통일합니다. 두 단계는 다릅니다.

## 설명용 가상 이벤트 추적
입력: A(ConsoleLogin/Failure/정상 시각), B(ConsoleLogin/Success/정상 시각), C(ConsoleLogin/Failure/잘못된 시각), D(ListBuckets).
결과: 로그인 표 A·B·C 3행 → 실패 표 A·C 2행 → total=2, invalid_time=1 → daily와 hourly의 막대 합계는 각각 1.

## 발표할 때 기억할 것
함수 정의와 호출은 다릅니다. source한 뒤 데이터를 읽고 plot_login_failures(records)를 호출해야 합니다. 작은 창에서는 mfrow를 먼저 설정한 뒤 mex·cex를 줄입니다.
공개 테스트 로그는 중복 포함 90건 중 실패 82·성공 8건이었습니다. 별도 eventID 중복 제거 입력은 43건 중 실패 39·성공 4건입니다. 현재 코드는 자동 중복 제거·공격 여부 판정을 하지 않습니다.
시간 정렬은 같은 UTC ISO 문자열 형식을 전제로 하며 파일 전체를 메모리에 읽습니다. 원본 로그·개별 사용자와 IP가 있는 CSV는 공개 저장소에 포함하지 않습니다.

## 원본 출처

Splunk attack_data 공개 보안 테스트 로그입니다.

- [aws_mulitple_failed_console_login · 로그인 31건](https://github.com/splunk/attack_data/blob/master/datasets/attack_techniques/T1110.003/aws_mulitple_failed_console_login/aws_cloudtrail.json)
- [aws_multiple_login_fail_per_user · 로그인 28건](https://github.com/splunk/attack_data/blob/master/datasets/attack_techniques/T1110.003/aws_multiple_login_fail_per_user/cloudtrail.json)
- [aws_failed_mfa · 로그인 14건](https://github.com/splunk/attack_data/blob/master/datasets/attack_techniques/T1621/aws_failed_mfa/cloudtrail.json)
- [multiple-ips · 로그인 8건](https://github.com/splunk/attack_data/blob/master/datasets/attack_techniques/T1586.003/aws_console_login_multiple_ips/cloudtrail.json)
- [login-failure · 로그인 7건](https://github.com/splunk/attack_data/blob/master/datasets/attack_techniques/T1110.001/aws_login_failure/aws_cloudtrail_events.json)
- [login-sfa · 로그인 2건](https://github.com/splunk/attack_data/blob/master/datasets/attack_techniques/T1078.004/aws_login_sfa/cloudtrail.json)
