# CloudTrail에서 콘솔 로그인 기록만 추출합니다.
# 실행: Rscript login_records.R 로그.json [출력.csv]
if (!requireNamespace("jsonlite", quietly = TRUE)) {
  stop('jsonlite가 필요합니다: install.packages("jsonlite")')
}

# 필드가 없으면 NA, 있으면 문자열 하나로 반환합니다.
text_value <- function(x) {
  if (is.null(x) || length(x) == 0) NA_character_ else as.character(x[[1]])
}

# Records 포장, 단일 이벤트, 이벤트 배열을 목록으로 맞춥니다.
event_list <- function(x) {
  if (!is.list(x)) stop("JSON 객체 또는 배열이 필요합니다.")
  if (!is.null(x$Records)) return(x$Records)
  if (!is.null(x$eventName)) return(list(x))
  x
}

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
