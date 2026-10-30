# 탐지 규칙 + 정답 라벨 대비 커버리지 평가
#
# 설계 원칙
#  - 규칙은 이벤트 필드(event_name, request_params 등)만 본다. 시나리오의 MITRE 라벨(technique)은
#    규칙 판단에 쓰지 않고, 아래 evaluate_coverage()에서 "채점"에만 사용한다.
#  - 규칙은 샘플 데이터를 보고 작성했으므로 커버리지가 높게 나오는 것은 당연하다.
#    이 수치는 실환경 정확도가 아니다 (정상 트래픽 baseline이 없어 오탐률은 측정 불가).
source("R/00_config.R")

SEVERITY_LEVELS <- c("low", "medium", "high", "critical")

empty_findings <- function() {
  tibble(id = character(), label_technique = character(),
         event_time = as.POSIXct(character(), tz = "UTC"),
         principal = character(), source_ip = character(), event_name = character(),
         severity = character(), detail = character())
}

# 규칙 함수가 돌려준 data.frame을 공통 컬럼으로 정리
finalize <- function(df) {
  if (nrow(df) == 0) return(empty_findings())
  df |> transmute(id, label_technique = technique, event_time, principal, source_ip,
                  event_name, severity, detail)
}

fail_tag <- function(error_code) ifelse(is.na(error_code), "", paste0(" [실패: ", error_code, "]"))
IPV4 <- "^\\d{1,3}(\\.\\d{1,3}){3}$"

# ---- R01: 콘솔 로그인 실패 반복 (무차별 대입) -------------------------------------------------
# 같은 주체가 window_min 분 안에 threshold회 이상 실패해야 발동한다. (시간 창이 없으면 몇 달에 걸친
# 실패도 "burst"로 잡히므로 의미가 없다.) 몇 시간~며칠에 걸친 low-and-slow 공격은 이 규칙으로 못 잡는다.
rule_login_failure_burst <- function(ev, threshold = 3, window_min = 60) {
  ev |>
    filter(event_name == "ConsoleLogin", login_result == "Failure") |>
    group_by(id, technique, principal) |>
    summarise(
      n_total = n(),
      # 각 실패 시각 t에서 [t, t + window] 안에 들어오는 실패 수의 최댓값
      n       = max(vapply(event_time, \(t) sum(event_time >= t & event_time <= t + window_min * 60), numeric(1))),
      event_time = min(event_time),
      source_ip  = paste(unique(source_ip), collapse = ","),
      event_name = "ConsoleLogin", .groups = "drop") |>
    filter(n >= threshold) |>
    mutate(severity = if_else(n >= 5, "high", "medium"),
           detail = sprintf("%d분 안에 콘솔 로그인 실패 %d회 (전체 실패 %d회)", window_min, n, n_total)) |>
    finalize()
}

# ---- R02: 같은 주체가 짧은 간격으로 서로 다른 IP 사용 (세션 탈취/자격증명 도용 의심) ------------
# 대상: Root/IAMUser + IPv4 출발지만 (AWS 내부 서비스 호출 등 노이즈 제외)
rule_multi_ip <- function(ev, window_min = 10) {
  ev |>
    filter(user_type %in% c("Root", "IAMUser"), str_detect(source_ip, IPV4)) |>
    arrange(id, principal, event_time) |>
    group_by(id, technique, principal) |>
    mutate(prev_ip = lag(source_ip),
           gap = as.numeric(difftime(event_time, lag(event_time), units = "mins"))) |>
    ungroup() |>
    filter(!is.na(prev_ip), prev_ip != source_ip, gap <= window_min) |>
    mutate(severity = if_else(user_type == "Root", "high", "medium"),
           detail = sprintf("%.1f분 간격으로 IP 변경 (%s -> %s)", gap, prev_ip, source_ip)) |>
    finalize()
}

# ---- R03: MFA 없는 콘솔 로그인 성공 (Root/IAMUser) --------------------------------------------
# AssumedRole(SSO/페더레이션) 로그인은 CloudTrail이 MFA 여부를 신뢰성 있게 남기지 않아 제외
rule_login_without_mfa <- function(ev) {
  ev |>
    filter(event_name == "ConsoleLogin", login_result == "Success", mfa_used == "No",
           user_type %in% c("Root", "IAMUser")) |>
    mutate(severity = if_else(user_type == "Root", "high", "medium"),
           detail = sprintf("MFA 없이 %s 콘솔 로그인 성공", user_type)) |>
    finalize()
}

# ---- R04: 루트 계정 활동 (이벤트 종류별 집계) --------------------------------------------------
rule_root_activity <- function(ev) {
  ev |>
    filter(user_type == "Root") |>
    group_by(id, technique, principal, event_name) |>
    summarise(n = n(), event_time = min(event_time),
              source_ip = paste(unique(source_ip), collapse = ","), .groups = "drop") |>
    mutate(severity = "high", detail = sprintf("루트 계정이 %s 실행 (%d건)", event_name, n)) |>
    finalize()
}

# ---- R05: 로깅·모니터링·보안 서비스 무력화 -----------------------------------------------------
LOG_TAMPER <- c("StopLogging", "DeleteTrail", "UpdateTrail", "PutEventSelectors",
                "DeleteLogGroup", "DeleteLogStream", "DeleteFlowLogs", "DeleteDetector",
                "DeleteIPSet", "DeleteWebACL", "DeleteRule", "DisableSecurityHub",
                "StopConfigurationRecorder", "DeleteConfigurationRecorder", "DeleteDeliveryChannel")
rule_logging_tamper <- function(ev) {
  ev |>
    filter(event_name %in% LOG_TAMPER) |>
    mutate(severity = if_else(is.na(error_code), "high", "medium"),
           detail = paste0("로깅/탐지 서비스 변경: ", event_name, fail_tag(error_code))) |>
    finalize()
}

# ---- R06: 로그 저장 버킷 수명주기 변경 (증거 자동 삭제) ----------------------------------------
rule_log_bucket_lifecycle <- function(ev) {
  ev |>
    filter(str_starts(event_name, "PutBucketLifecycle"),
           str_detect(request_params, regex("\"bucketName\":\"[^\"]*(cloudtrail|log)", ignore_case = TRUE))) |>
    mutate(severity = "high", detail = "로그 버킷 수명주기 규칙 변경") |>
    finalize()
}

# ---- R07: IAM 권한 상승 / 지속성 확보 -----------------------------------------------------------
IAM_PRIVESC <- c("CreatePolicyVersion", "SetDefaultPolicyVersion", "AttachUserPolicy", "AttachRolePolicy",
                 "AttachGroupPolicy", "PutUserPolicy", "PutRolePolicy", "PutGroupPolicy",
                 "AddUserToGroup", "UpdateAssumeRolePolicy")
IAM_PERSIST <- c("CreateAccessKey", "CreateLoginProfile", "UpdateLoginProfile", "CreateUser")
rule_iam_changes <- function(ev) {
  ev |>
    filter(event_name %in% c(IAM_PRIVESC, IAM_PERSIST)) |>
    mutate(severity = case_when(!is.na(error_code)         ~ "low",     # 실패한 시도
                                event_name %in% IAM_PRIVESC ~ "high",
                                TRUE                        ~ "medium"),
           detail = paste0("IAM 변경: ", event_name, fail_tag(error_code))) |>
    finalize()
}

# ---- R08: MFA 장치 변경 -------------------------------------------------------------------------
MFA_EVENTS <- c("CreateVirtualMFADevice", "EnableMFADevice", "DeactivateMFADevice",
                "DeleteVirtualMFADevice", "ResyncMFADevice")
rule_mfa_tamper <- function(ev) {
  ev |>
    filter(event_name %in% MFA_EVENTS) |>
    mutate(severity = if_else(event_name %in% c("DeactivateMFADevice", "DeleteVirtualMFADevice"), "high", "medium"),
           detail = paste0("MFA 장치 변경: ", event_name, " (주체: ", user_type, ")")) |>
    finalize()
}

# ---- R09: AMI/스냅샷 외부 공유 ------------------------------------------------------------------
SHARE_EVENTS <- c("ModifyImageAttribute", "ModifySnapshotAttribute",
                  "ModifyDBSnapshotAttribute", "ModifyDBClusterSnapshotAttribute")
# "추가(add)"만 위협으로 본다. 공유 해제(remove)나 내용이 빈 add는 제외한다.
#  - EC2(AMI/스냅샷): {"add":{"items":[{"group":"all"}]}} 또는 {"add":{"items":[{"userId":"..."}]}}
#  - RDS 스냅샷:      {"valuesToAdd":["all"]} 또는 계정 ID 목록
rule_resource_sharing <- function(ev) {
  ec2_add <- "\"add\":\\{\"items\":\\[[^]]*"
  public_pat  <- paste0(ec2_add, "\"group\":\"all\"|\"valuesToAdd\":\\[[^]]*\"all\"")
  account_pat <- paste0(ec2_add, "\"userId\"|\"valuesToAdd\":\\[[^]]*\"\\d{12}\"")
  ev |>
    filter(event_name %in% SHARE_EVENTS) |>
    mutate(share_type = case_when(str_detect(request_params, public_pat)  ~ "public",
                                  str_detect(request_params, account_pat) ~ "account",
                                  TRUE                                    ~ NA_character_)) |>
    filter(!is.na(share_type)) |>
    mutate(severity = if_else(share_type == "public", "critical", "medium"),
           detail   = paste0(event_name, if_else(share_type == "public", ": 전체 공개로 공유", ": 다른 계정에 공유"))) |>
    finalize()
}

# ---- R10: 대량 데이터 이동 설정 (DataSync 작업 / S3 복제) ---------------------------------------
rule_bulk_data_movement <- function(ev) {
  ev |>
    filter((event_name == "CreateTask" & str_detect(event_source, "datasync")) |
             event_name == "PutBucketReplication") |>
    mutate(severity = "medium", detail = paste0("데이터 이동 설정 생성: ", event_name)) |>
    finalize()
}

# ---- R11: S3 영향(Impact) 징후 - 버전관리 중지, KMS 재암호화 -----------------------------------
rule_s3_impact <- function(ev) {
  bind_rows(
    ev |> filter(event_name == "PutBucketVersioning", str_detect(request_params, "\"Status\":\"Suspended\"")) |>
      mutate(severity = "high", detail = "S3 버전 관리 중지 (복구 수단 제거)"),
    ev |> filter(event_name %in% c("CopyObject", "PutObject"),
                 str_detect(request_params, "server-side-encryption-aws-kms-key-id")) |>
      mutate(severity = "medium", detail = paste0("KMS 키 지정 객체 쓰기: ", event_name, fail_tag(error_code)))
  ) |> finalize()
}

# ---- R12: 비밀번호 정책 조회/약화 ---------------------------------------------------------------
rule_password_policy <- function(ev) {
  ev |>
    filter(event_name %in% c("GetAccountPasswordPolicy", "UpdateAccountPasswordPolicy", "DeleteAccountPasswordPolicy")) |>
    mutate(severity = if_else(event_name == "GetAccountPasswordPolicy", "low", "medium"),
           detail = paste0("계정 비밀번호 정책: ", event_name)) |>
    finalize()
}

# ---- R13: Lambda 코드 변경 -----------------------------------------------------------------------
rule_lambda_code_update <- function(ev) {
  ev |>
    filter(str_starts(event_name, "UpdateFunctionCode")) |>
    mutate(severity = "medium", detail = paste0("Lambda 함수 코드 변경: ", event_name)) |>
    finalize()
}

# ---- R14: RDS 마스터 비밀번호 변경 ---------------------------------------------------------------
rule_rds_password_reset <- function(ev) {
  ev |>
    filter(event_name == "ModifyDBInstance", str_detect(request_params, "masterUserPassword")) |>
    mutate(severity = "high", detail = "RDS 마스터 비밀번호 변경") |>
    finalize()
}

# ---- R15: 접근 거부 반복 (범용 규칙, MITRE 매핑 없음) --------------------------------------------
rule_access_denied_burst <- function(ev, threshold = 3) {
  ev |>
    filter(str_detect(error_code, regex("AccessDenied|Unauthorized", ignore_case = TRUE))) |>
    group_by(id, technique, principal) |>
    summarise(n = n(), event_time = min(event_time),
              source_ip = paste(unique(source_ip), collapse = ","),
              event_name = paste(unique(event_name), collapse = ","), .groups = "drop") |>
    filter(n >= threshold) |>
    mutate(severity = "medium", detail = sprintf("접근 거부 %d회 반복", n)) |>
    finalize()
}

# 규칙 목록: mitre에 적힌 기법은 "이 규칙이 잡으려는 대상". 범용 규칙은 NA.
rules <- tribble(
  ~rule_id, ~rule_name,                        ~mitre,                       ~fn,
  "R01", "콘솔 로그인 실패 반복",              list(c("T1110.001")),               rule_login_failure_burst,
  "R02", "짧은 간격 다중 IP 사용",             list(c("T1586.003", "T1185")),      rule_multi_ip,
  "R03", "MFA 없는 콘솔 로그인",               list(c("T1078.004")),               rule_login_without_mfa,
  "R04", "루트 계정 활동",                     list(c("T1078.004")),               rule_root_activity,
  "R05", "로깅/보안 서비스 무력화",            list(c("T1562.008")),               rule_logging_tamper,
  "R06", "로그 버킷 수명주기 변경",            list(c("T1562.008")),               rule_log_bucket_lifecycle,
  "R07", "IAM 권한 상승/지속성",               list(c("T1078")),                   rule_iam_changes,
  "R08", "MFA 장치 변경",                      list(c("T1556.006", "T1621")),      rule_mfa_tamper,
  "R09", "AMI/스냅샷 외부 공유",               list(c("T1537")),                   rule_resource_sharing,
  "R10", "대량 데이터 이동 설정",              list(c("T1119", "T1537")),          rule_bulk_data_movement,
  "R11", "S3 영향 징후",                       list(c("T1486", "T1490")),          rule_s3_impact,
  "R12", "비밀번호 정책 조회/약화",            list(c("T1201")),                   rule_password_policy,
  "R13", "Lambda 코드 변경",                   list(c("T1204")),                   rule_lambda_code_update,
  "R14", "RDS 마스터 비밀번호 변경",           list(c("T1110.002")),               rule_rds_password_reset,
  "R15", "접근 거부 반복",                     list(NA_character_),          rule_access_denied_burst
) |>
  mutate(mitre = map(mitre, unlist))  # tribble이 리스트 셀을 한 겹 더 감싸므로 풀어준다

run_detections <- function(events, rules) {
  rules |>
    mutate(findings = map(fn, \(f) f(events))) |>
    select(rule_id, rule_name, findings) |>
    unnest(findings) |>
    mutate(severity = factor(severity, levels = SEVERITY_LEVELS, ordered = TRUE)) |>
    arrange(id, event_time, rule_id)
}

# 규칙의 기법(r)이 시나리오 라벨(s)과 같거나 상·하위 관계일 때만 "일치"로 본다. (T1110.001 vs T1110.002 같은 형제는 불일치)
technique_match <- function(s, r) {
  !is.na(r) & (s == r | startsWith(s, paste0(r, ".")) | startsWith(r, paste0(s, ".")))
}

# 규칙-기법 대응표 (rule_id, mitre) 1행 1기법
rule_techniques <- function(rules) {
  rules |> select(rule_id, mitre) |> unnest(mitre) |> rename(rule_technique = mitre)
}

# 시나리오별: 라벨과 일치하는 규칙이 하나라도 발동했는가?
evaluate_coverage <- function(findings, events, rules) {
  rt <- rule_techniques(rules)
  scenarios <- events |> distinct(id, technique, scenario)

  matched <- findings |>
    inner_join(rt, by = "rule_id", relationship = "many-to-many") |>
    filter(technique_match(label_technique, rule_technique)) |>
    distinct(id, rule_id, event_time, event_name, detail)

  scenarios |>
    left_join(
      matched |> group_by(id) |>
        summarise(matched_rules = paste(sort(unique(rule_id)), collapse = ", "), .groups = "drop"),
      by = "id") |>
    left_join(
      findings |> group_by(id) |>
        summarise(n_findings = n(), max_severity = as.character(max(severity)), .groups = "drop"),
      by = "id") |>
    mutate(detected = !is.na(matched_rules),
           n_findings = replace_na(n_findings, 0L)) |>
    arrange(technique, scenario)
}

# 시나리오 라벨과 일치하지 않는데 발동한 규칙 (오탐일 수도, 라벨에 없는 실제 추가 행위일 수도 있음 -> 사람이 검토)
unmatched_hits <- function(findings, rules) {
  rt <- rule_techniques(rules)
  hit_ok <- findings |>
    inner_join(rt, by = "rule_id", relationship = "many-to-many") |>
    filter(technique_match(label_technique, rule_technique)) |>
    distinct(id, rule_id)
  findings |>
    anti_join(hit_ok, by = c("id", "rule_id"))
}

if (sys.nframe() == 0) {
  events   <- readRDS(file.path(DIR_PROC, "events.rds"))
  findings <- run_detections(events, rules)
  coverage <- evaluate_coverage(findings, events, rules)
  saveRDS(findings, file.path(DIR_PROC, "findings.rds"))
  write_csv(findings, file.path(DIR_OUT, "findings.csv"))
  write_csv(coverage, file.path(DIR_OUT, "coverage.csv"))
  cat(sprintf("탐지 결과 %d건 / 라벨 일치 탐지 %d of %d 시나리오\n",
              nrow(findings), sum(coverage$detected), nrow(coverage)))
}
