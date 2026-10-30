# 프로젝트 설정: 데이터셋 목록(manifest)과 경로
# 데이터 출처: Splunk attack_data (https://github.com/splunk/attack_data)
# 각 시나리오는 MITRE ATT&CK 기법 ID로 라벨링되어 있어 "탐지 규칙이 정답을 맞혔는지" 검증할 수 있다.

suppressPackageStartupMessages({
  library(tidyverse)
  library(jsonlite)
  library(lubridate)
})

# 파일은 Git LFS로 저장되어 있어 raw.githubusercontent.com이 아니라 media.githubusercontent.com에서 받는다.
BASE_URL <- "https://media.githubusercontent.com/media/splunk/attack_data/master/datasets/attack_techniques"

DIR_RAW     <- "data/raw"
DIR_PROC    <- "data/processed"
DIR_OUT     <- "output"
DIR_FIG     <- file.path(DIR_OUT, "figures")

# technique: 시나리오에 붙은 MITRE ATT&CK 기법 ID (정답 라벨)
# scenario : 저장소 내 디렉터리 이름, file: 그 안의 로그 파일 이름
manifest <- tribble(
  ~technique,  ~scenario,                                   ~file,
  "T1110.001", "aws_login_failure",                         "aws_cloudtrail_events.json",
  "T1586.003", "aws_console_login_multiple_ips",            "cloudtrail.json",
  "T1078.004", "aws_login_sfa",                             "cloudtrail.json",
  "T1621",     "aws_mfa_disabled",                          "cloudtrail.json",
  "T1556.006", "aws_new_mfa_method_registered_for_user",    "cloudtrail.json",
  "T1185",     "aws_concurrent_sessions_from_different_ips","cloudtrail.json",
  "T1562.008", "stop_delete_cloudtrail",                    "aws_cloudtrail_events.json",
  "T1562.008", "update_cloudtrail",                         "aws_cloudtrail_events.json",
  "T1562.008", "delete_cloudwatch_log_group",               "aws_cloudtrail_events.json",
  "T1562.008", "aws_delete_security_services",              "aws_cloudtrail_events.json",
  "T1562.008", "put_bucketlifecycle",                       "aws_cloudtrail_events.json",
  "T1078",     "aws_create_policy_version",                 "aws_cloudtrail_events.json",
  "T1078",     "aws_setdefaultpolicyversion",               "aws_cloudtrail_events.json",
  "T1078",     "aws_createaccesskey",                       "aws_cloudtrail_events.json",
  "T1078",     "aws_createloginprofile",                    "aws_cloudtrail_events.json",
  "T1078",     "aws_updateloginprofile",                    "aws_cloudtrail_events.json",
  "T1537",     "aws_ami_shared_public",                     "aws_cloudtrail_events.json",
  "T1537",     "aws_snapshot_exfil",                        "aws_cloudtrail_events.json",
  "T1119",     "aws_exfil_datasync",                        "cloudtrail.json",
  "T1486",     "s3_file_encryption",                        "aws_cloudtrail_events.json",
  "T1490",     "aws_bucket_version",                        "cloudtrail.json",
  "T1201",     "aws_password_policy",                       "cloudtrail.json",
  "T1204",     "aws_updatelambdafunctioncode",              "aws_cloudtrail_events.json",
  "T1110.002", "aws_rds_password_reset",                    "aws_cloudtrail_events.json"
) |>
  mutate(
    id       = paste(technique, scenario, sep = "__"),
    url      = file.path(BASE_URL, technique, scenario, file),
    raw_path = file.path(DIR_RAW, id, file)
  )

# base R 4.3에는 %||% 가 없다 (4.4부터 포함). NULL이거나 길이 0이면 기본값을 쓴다.
`%||%` <- function(a, b) if (is.null(a) || length(a) == 0) b else a

# 한글 문자열이 깨지지 않도록 UTF-8 로케일을 시도한다 (환경마다 이름이 달라 순서대로 시도)
for (loc in c("C.UTF-8", "en_US.UTF-8", "ko_KR.UTF-8")) {
  if (nzchar(suppressWarnings(Sys.setlocale("LC_CTYPE", loc)))) break
}

for (d in c(DIR_RAW, DIR_PROC, DIR_FIG)) dir.create(d, recursive = TRUE, showWarnings = FALSE)
