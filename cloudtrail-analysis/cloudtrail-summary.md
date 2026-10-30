# CloudTrail 분석 — 핵심 요약
공개 CloudTrail 로그를 R로 정규화하고 15개 규칙으로 의심 행위를 찾은 뒤 시나리오 라벨과 비교하는 프로젝트입니다. AI 모델 학습·추론 코드는 없습니다.

## 1. 분석할 파일 목록 만들기
**자료형:** 수동 입력 값 → tibble
24개 파일을 같은 절차로 처리하려면 출처와 저장 위치를 표로 관리해야 합니다.
```r
manifest <- tribble(
  ~technique, ~scenario, ~file,
  ...
) |> mutate(id = paste(technique, scenario, sep = "__"))
```
- tribble()은 행 중심으로 표를 만듭니다. ~는 여기서 열 이름을 선언합니다.
- mutate()는 id 열을 추가합니다. paste()는 두 문자열을 __로 연결합니다.
- 이 표를 download_all()과 load_all_events()에 넘깁니다.

예시: T1078 + aws_createaccesskey → T1078__aws_createaccesskey

주의: 코드의 ...는 시나리오 목록과 다른 열 계산을 생략한 설명용 표기입니다.

## 2. 다운로드한 파일을 문자열로 읽기
**자료형:** 디스크 JSON 파일 → character 벡터
파일을 분석하려면 파일 이름이 아니라 안에 기록된 내용을 읽어야 합니다.
```r
lines <- readLines(path, warn = FALSE, encoding = "UTF-8")
lines <- lines[nzchar(trimws(lines))]
```
- readLines()는 각 줄을 문자열 하나로 읽습니다. 아직 JSON의 필드에 접근할 수는 없습니다.
- trimws()는 빈 줄 판별을 위해 앞뒤 공백을 제거합니다.
- nzchar()는 글자가 있는지 TRUE/FALSE를 반환하고, lines[...]는 해당 줄만 선택합니다. 원래 줄의 공백을 모두 지우는 코드는 아닙니다.

예시: 파일의 3줄 → 문자열 원소 3개; 빈 줄이 1개면 2개만 유지

주의: 사진을 바이트로 변환하는 과정과 다릅니다. 여기서는 이미 텍스트인 로그를 문자열로 읽습니다.

## 3. JSON 문자열을 R 리스트로 해석하기
**자료형:** character → 중첩 list
문자열에서 eventName이나 userIdentity 같은 이름으로 값을 꺼내려면 JSON 구조를 해석해야 합니다.
```r
parsed <- lapply(lines, function(l)
  tryCatch(fromJSON(l, simplifyVector = FALSE),
           error = function(e) NULL))
```
- lapply()는 줄마다 함수를 실행하고 반환값을 리스트에 모읍니다.
- fromJSON()은 JSON 객체와 배열을 R 자료구조로 해석합니다. simplifyVector=FALSE는 리스트 구조를 유지하도록 합니다.
- 실패한 줄은 tryCatch()가 NULL로 바꿉니다. 이후 원본 코드에서 모든 줄 성공 여부를 확인합니다.

예시: {"eventName":"ConsoleLogin"} → x$eventName으로 "ConsoleLogin" 읽기

주의: R list는 이름 있는 서로 다른 자료형의 값을 담을 수 있습니다. Python dict와 역할이 비슷할 수 있지만 같은 자료형은 아닙니다.

## 4. 이벤트 하나를 표의 한 행으로 만들기
**자료형:** 중첩 list → 한 행의 tibble
규칙들이 같은 열 이름으로 접근하도록 서로 다른 로그 구조를 통일합니다.
```r
tibble(
  event_name = x$eventName %||% NA_character_,
  source_ip = x$sourceIPAddress %||% NA_character_,
  principal = principal
)
```
- $는 이름으로 리스트 원소를 읽습니다.
- %||%는 이 프로젝트에서 정의한 함수이며 NULL·길이 0일 때 오른쪽 기본값을 사용합니다.
- NA_character_는 문자열 자료형의 결측값입니다.
- tibble()은 지정한 열을 가진 표를 만듭니다. 위 코드는 parse_event()의 일부 열만 보인 발췌입니다.

예시: 중첩된 JSON → event_name / source_ip / principal 열을 가진 한 행

주의: %||%는 이미 들어 있는 NA와 빈 문자열까지 대체하지 않습니다. principal을 정하는 코드는 tibble() 전에 실행됩니다.

## 5. 요청 파라미터를 검색 가능한 문자열로 보관하기
**자료형:** requestParameters list → JSON character
규칙에서 공유 대상·버전 관리 상태 같은 요청 내용을 문자열 패턴으로 찾기 위해 변환합니다.
```r
request_params = if (is.null(params)) NA_character_ else
  as.character(toJSON(params, auto_unbox = TRUE, null = "null"))
```
- toJSON()은 R 객체를 JSON 표현으로 직렬화합니다.
- auto_unbox=TRUE는 길이 1인 원자 값을 불필요한 배열로 감싸지 않도록 합니다.
- as.character()는 JSON 표현을 문자열로 맞춥니다.
- params가 없으면 결측값을 저장합니다.

예시: list(bucketName="audit-log") → {"bucketName":"audit-log"}

주의: 전체 이벤트를 다시 문자열로 되돌리는 것이 아니라 요청 파라미터 열만 문자열로 보관합니다. 구조적 JSON 검사보다 정규식이 표현 형식에 민감합니다.

## 6. 이벤트 표들을 합치고 시간을 변환하기
**자료형:** 파일별 표를 담은 list-column → 통합 tibble; 문자 시간 → POSIXct
모든 파일에 같은 규칙을 적용하고 시간 차이를 계산하려면 하나의 표와 시간 자료형이 필요합니다.
```r
mutate(events = map(raw_path, read_cloudtrail_file)) |>
select(id, technique, scenario, events) |>
unnest(events) |>
mutate(event_time = ymd_hms(event_time, quiet = TRUE),
       hour = floor_date(event_time, "hour"))
```
- map()은 경로마다 파일 파싱 함수를 호출합니다.
- events 열의 각 셀에 파일 하나의 이벤트 표가 들어갑니다. 이를 list-column이라고 합니다.
- unnest()는 안쪽 표를 바깥 행으로 펼칩니다. 시나리오 정보도 각 행에 반복해서 붙습니다.
- ymd_hms()는 문자열을 시간값으로 해석합니다. floor_date()는 시각을 시간 단위로 내립니다.

예시: 파일 A 2행 + 파일 B 3행 → events 5행; 10:12:30 → hour 10:00:00

주의: 코드는 load_all_events() 파이프라인 중간 발췌입니다. 파싱 불가능한 시간은 결측값이 될 수 있습니다.

## 7. 조건에 맞는 이벤트를 선택하고 집계하기
**자료형:** events tibble → 필터된 표 → 집계 표
탐지는 단순 이벤트 선택과 여러 이벤트의 패턴 집계로 나뉩니다.
```r
filter(event_name == "ConsoleLogin", login_result == "Failure") |>
group_by(id, technique, principal)
```
- filter()의 쉼표 조건은 둘 다 만족해야 합니다. 로그인 실패만 남깁니다.
- group_by()는 데이터를 바로 합치지 않고 이후 계산의 그룹 기준을 지정합니다.
- R01은 각 실패 시각부터 60분 내 횟수를 계산한 뒤 최댓값을 사용합니다.
- summarise()가 여러 이벤트를 그룹별 결과 한 행으로 요약합니다.

예시: 가상 실패 시각 10:00, 10:02, 10:04, 16:00 → 전체 4회 / 최대 60분 내 3회 → medium 탐지 1건

주의: 이것은 실행 실측이 아닌 설명용 예시입니다. R01은 시나리오·주체별로 집계하며 출력 시각은 그룹 전체 최초 시각입니다.

## 8. 규칙별 탐지를 통일하고 합치기
**자료형:** 규칙별 tibble → list-column → findings tibble
규칙마다 중간 계산 열이 달라도 공통 형태로 모아야 CSV와 차트를 만들 수 있습니다.
```r
mutate(findings = map(fn, \(f) f(events))) |>
select(rule_id, rule_name, findings) |>
unnest(findings)
```
- fn 열에는 규칙 함수 객체가 들어 있습니다.
- \(f)는 익명 함수이며 f(events)는 해당 규칙에 이벤트 표를 전달합니다.
- 각 규칙 내부의 finalize()가 공통 열만 남깁니다.
- unnest()가 규칙별 결과를 펼치면서 규칙 번호와 이름을 붙입니다.

예시: 같은 로그인 이벤트가 R03과 R04에 걸릴 수 있음 → 이벤트 수와 탐지 수는 다름

주의: 여러 실패 이벤트를 하나로 요약하는 규칙도 있어 202개 이벤트와 151개 탐지는 단순 비율로 비교할 수 없습니다.

## 9. 심각도를 순서가 있는 범주로 바꾸기
**자료형:** character → ordered factor
문자 정렬 대신 low < medium < high < critical 순서로 최고 심각도를 계산하기 위해서입니다.
```r
severity = factor(severity,
  levels = SEVERITY_LEVELS, ordered = TRUE)
```
- SEVERITY_LEVELS는 c("low", "medium", "high", "critical")입니다.
- factor()는 값을 정해진 범주에 대응시킵니다.
- ordered=TRUE는 범주 간 순서가 있음을 나타냅니다.
- 이후 max(severity)는 의도한 심각도 순서를 사용합니다.

예시: medium, critical, high → 최고 심각도 critical

주의: 원본에서 선언한 levels 순서에 의존합니다. 임의의 숫자 위험 점수를 학습한 결과가 아닙니다.

## 10. 라벨과 비교해 시나리오 커버리지 만들기
**자료형:** findings + 규칙–기법 표 → coverage
탐지가 발생했다는 사실과 시나리오에 대응하는 규칙이 발동했다는 사실을 구분합니다.
```r
inner_join(rt, by = "rule_id", relationship = "many-to-many") |>
filter(technique_match(label_technique, rule_technique))
```
- inner_join()은 rule_id가 같은 행을 연결합니다.
- technique_match()는 동일 ID 또는 상·하위 기법 관계를 일치로 판단합니다.
- 일치 규칙을 시나리오별로 모은 뒤 matched_rules가 있으면 detected=TRUE가 됩니다.
- 불일치 탐지는 unmatched_hits()에서 검토 목록으로 분리합니다.

예시: T1078 ↔ T1078.004: 일치; T1110.001 ↔ T1110.002: 불일치

주의: 시나리오 하나에서 대응 규칙이 한 번만 발동해도 탐지로 계산합니다. 오탐률이나 이벤트 단위 정확도가 아닙니다.

## 11. 중간 객체와 결과를 파일로 저장하기
**자료형:** 메모리의 R 객체 → RDS / CSV / PNG / HTML
다음 단계에서 다시 읽거나 사람이 결과를 확인할 수 있도록 저장합니다.
```r
saveRDS(events, file.path(DIR_PROC, "events.rds"))
write_csv(findings, file.path(DIR_OUT, "findings.csv"))
save_all_figures(events, findings, coverage)
rmarkdown::render("report.Rmd", output_dir = DIR_OUT, quiet = TRUE)
```
- saveRDS()는 R 객체의 자료형을 보존해 저장합니다. readRDS()로 다시 읽습니다.
- write_csv()는 표를 교환하기 쉬운 텍스트 파일로 기록합니다.
- save_all_figures()는 ggplot 차트를 PNG로 저장합니다.
- render()는 설명문과 R 계산 결과를 결합해 HTML 보고서를 만듭니다.

예시: events.rds: 분석 재사용 / findings.csv: 탐지 표 / figures: 그림 / report.html: 보고서

주의: 위 호출들은 실행 파일에서 각각 다른 단계에 위치합니다. CSV만으로 R의 순서형 factor 설정까지 그대로 보존되지는 않습니다.

## 결과와 한계
동봉 보고서: 이벤트 202건, 시나리오 24/24에서 라벨 일치 탐지, 탐지 결과 151건, 라벨 불일치 15건. 실환경 정확도·오탐률을 뜻하지 않습니다. 원본 코드를 재실행하지 않은 정적 분석입니다.
