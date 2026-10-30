# CloudTrail 로그 파싱 -> 정규화된 tibble
# 지원 형식: (1) 한 줄에 이벤트 하나인 NDJSON, (2) {"Records": [...]} 형태, (3) 이벤트 배열
source("R/00_config.R")

# 이벤트(list) 하나를 한 행으로 변환. 스키마가 이벤트마다 달라서 필요한 필드만 안전하게 꺼낸다.
parse_event <- function(x) {
  ui <- x$userIdentity %||% list()
  issuer <- ui$sessionContext$sessionIssuer %||% list()

  # 행위 주체: IAM 사용자명 > 역할(세션 발급자) > ARN 마지막 토큰 > 유형
  principal <- ui$userName %||% issuer$userName %||%
    (if (!is.null(ui$arn)) sub(".*[/:]", "", ui$arn) else NULL) %||%
    ui$type %||% NA_character_

  params <- x$requestParameters
  tibble(
    event_time    = x$eventTime %||% NA_character_,
    event_source  = x$eventSource %||% NA_character_,
    event_name    = x$eventName %||% NA_character_,
    aws_region    = x$awsRegion %||% NA_character_,
    source_ip     = x$sourceIPAddress %||% NA_character_,
    user_agent    = x$userAgent %||% NA_character_,
    user_type     = ui$type %||% NA_character_,
    principal     = principal,
    account_id    = ui$accountId %||% x$recipientAccountId %||% NA_character_,
    error_code    = x$errorCode %||% NA_character_,
    error_message = x$errorMessage %||% NA_character_,
    read_only     = as.logical(x$readOnly %||% NA),
    login_result  = x$responseElements$ConsoleLogin %||% NA_character_,
    mfa_used      = x$additionalEventData$MFAUsed %||% NA_character_,
    # 규칙에서 문자열 검색을 쉽게 하려고 요청 파라미터는 JSON 문자열로 보관
    request_params = if (is.null(params)) NA_character_ else
      as.character(toJSON(params, auto_unbox = TRUE, null = "null"))
  )
}

# 파일 하나 읽기: NDJSON 우선, 실패하면 통째로 JSON 파싱
read_cloudtrail_file <- function(path) {
  lines <- readLines(path, warn = FALSE, encoding = "UTF-8")
  lines <- lines[nzchar(trimws(lines))]

  as_events <- function(obj) {
    if (is.list(obj) && !is.null(obj$Records)) obj$Records
    else if (is.list(obj) && !is.null(obj$eventName)) list(obj)
    else obj
  }

  parsed <- lapply(lines, function(l) tryCatch(fromJSON(l, simplifyVector = FALSE), error = function(e) NULL))
  if (length(parsed) > 0 && all(!vapply(parsed, is.null, logical(1)))) {
    events <- unlist(lapply(parsed, as_events), recursive = FALSE)
  } else {
    events <- as_events(fromJSON(paste(lines, collapse = "\n"), simplifyVector = FALSE))
  }
  events <- Filter(function(e) is.list(e) && !is.null(e$eventName), events)
  if (!length(events)) return(tibble())
  map_dfr(events, parse_event)
}

load_all_events <- function(manifest) {
  manifest |>
    filter(file.exists(raw_path)) |>
    mutate(events = map(raw_path, read_cloudtrail_file)) |>
    select(id, technique, scenario, events) |>
    unnest(events) |>
    filter(event_name == "ConsoleLogin") |>
    mutate(
      event_time = ymd_hms(event_time, quiet = TRUE),
      hour       = floor_date(event_time, "hour")
    ) |>
    arrange(id, event_time)
}

if (sys.nframe() == 0) {
  events <- load_all_events(manifest)
  saveRDS(events, file.path(DIR_PROC, "events.rds"))
  write_csv(events, file.path(DIR_PROC, "events.csv"))
  cat(sprintf("이벤트 %d건, 시나리오 %d개 저장 완료\n", nrow(events), n_distinct(events$id)))
}
