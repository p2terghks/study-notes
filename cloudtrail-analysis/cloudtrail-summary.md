# CloudTrail 로그인 분석 — 핵심 요약
4개 시나리오의 ConsoleLogin 이벤트를 3개 규칙으로 분석합니다. R 코드 407줄이며 전체 실행 재검증 전입니다.

## rule_login_failure_burst
로그인 events → 그룹별 실패 집중 탐지
- ConsoleLogin·Failure 조건과 유효한 시각을 만족하는 행만 고릅니다.
- group_by(id,technique,principal)는 같은 시나리오·라벨·주체끼리 계산하도록 묶습니다.
- n_total=n()은 전체 실패 수입니다. vapply()는 각 실패 시각 t에서 [t,t+60분] 범위의 실패 수를 하나씩 계산하고 숫자 하나라는 반환 형태를 지정합니다.
- event_time>=t &amp; event_time<=t+window_min*60은 논리 벡터입니다. sum()은 TRUE를 1로 세고, max()는 그중 최댓값을 선택합니다.
- summarise()는 대표 시각을 그룹 최초 시각, IP를 중복 제거 후 쉼표로 합친 값으로 기록합니다. .groups="drop"으로 그룹을 해제합니다.
- 최댓값 n이 threshold 이상일 때만 남깁니다. n>=5이면 high, 그 외 medium입니다. sprintf()는 숫자를 설명 문자열에 끼워 넣습니다.
집중 구간을 정확히 찾았어도 출력 event_time과 source_ip는 그룹 전체 요약입니다. 임계값 threshold를 바꿔도 high 기준 5는 별도로 고정되어 있습니다.

## rule_multi_ip
로그인 events → IP가 바뀐 현재 이벤트
- Root/IAMUser·IPv4 모양·ConsoleLogin·유효한 시각을 먼저 선택합니다.
- arrange()로 시간순을 만든 후 시나리오·주체별로 그룹을 나눕니다.
- lag(source_ip)는 직전 행 IP, lag(event_time)은 직전 시각을 가져옵니다. 그룹 첫 행은 이전 값이 없어 NA입니다.
- difftime(...,units="mins")는 시간 차이이고 as.numeric()이 분 단위 숫자로 바꿉니다.
- ungroup()으로 그룹을 풀고, 이전 IP가 존재하고 IP가 다르며 0~window_min분일 때만 남깁니다.
- Root는 high, IAMUser는 medium입니다. detail에는 이전 IP와 현재 IP, 시간 간격을 넣습니다.
성공 로그인에 한정하지 않습니다. IPv6는 제외하고 IPv4 정규식은 0~255 범위를 검사하지 않습니다. IP 변경을 세션 탈취로 확정하지 않습니다.

## rule_login_without_mfa
로그인 events → MFA 없는 성공 로그인
- ConsoleLogin, Success, MFAUsed="No", Root/IAMUser 조건을 모두 만족해야 합니다. filter() 안의 쉼표는 조건들의 AND입니다.
- MFA 값이 NA이면 해당 조건이 TRUE가 아니므로 filter()에서 제외됩니다.
- Root는 high, IAMUser는 medium으로 구분하고 finalize()로 공통 형식을 반환합니다.
AssumedRole은 대상에 없습니다. MFA 미사용과 공격 성공은 같은 의미가 아닙니다. R03에는 시각 결측값을 제외하는 별도 조건이 없습니다.

## 전체 실행 순서
설정 → 다운로드 → JSON 파싱 → ConsoleLogin 선택 → 시간 변환 → 세 규칙 독립 실행 → 결과 통합 → 라벨 평가 → 그림·보고서

## 결과 상태
문법 검사는 통과했지만 필수 R 패키지가 없어 전체 파이프라인은 재실행하지 않았습니다. 예전 24/24·151건 수치는 새 버전 결과가 아닙니다.
