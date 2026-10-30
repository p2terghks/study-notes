# R을 활용한 AWS CloudTrail 로그인 이상 징후 분석

공개 로그인 시나리오 4개에서 ConsoleLogin 이벤트만 추출하고 3개 규칙으로 분석합니다.

| 규칙 | 조건 | 기본값 |
|---|---|---|
| R01 | 같은 주체의 로그인 실패 집중 | 60분 내 3회 이상 |
| R02 | 콘솔 로그인의 직전 IP와 변경 | Root/IAMUser, IPv4, 10분 이내 |
| R03 | MFA 없는 콘솔 로그인 성공 | Root/IAMUser, Success, MFAUsed=No |

R02는 성공·실패를 모두 비교합니다. 로그인 외 API 이벤트는 제외합니다.

## 실행

R >= 4.1 및 tidyverse, jsonlite, lubridate, rmarkdown과 Pandoc이 필요합니다.
프로젝트 루트에서 `Rscript run_pipeline.R`을 실행합니다.
코드 규모: R 407줄(주석·빈 줄 포함). Dockerfile은 실행 검증하지 않았습니다.

## 구조

- R/00_config.R: 시나리오 목록과 경로
- R/01_download.R: 원본 다운로드
- R/02_parse.R: JSON 정규화와 ConsoleLogin 선택
- R/03_detect.R: R01·R02·R03, 결과 통합과 라벨 비교
- R/04_visualize.R: 로그인 타임라인과 탐지 매트릭스
- run_pipeline.R: 전체 순서 관리
- report.Rmd: 현재 실행에서 계산한 결과를 담는 보고서

## 자료

- [핵심 요약](https://p2terghks.github.io/study-notes/cloudtrail-analysis/cloudtrail-summary.html)
- [클릭형 흐름도](https://p2terghks.github.io/study-notes/cloudtrail-analysis/cloudtrail-interactive-diagram.html)
- [코드 해설](https://p2terghks.github.io/study-notes/cloudtrail-analysis/cloudtrail-code-guide.html)

## 검증과 한계

R 파일 문법 검사 통과. 현재 환경의 필요한 R 패키지 부재로 전체 파이프라인을 재실행하지 않았습니다.
새 범위의 탐지 건수·커버리지는 아직 제시하지 않습니다. 이전 전체 분석의 24/24·151건 수치는 이 버전 결과가 아닙니다.
정상 로그·독립 데이터가 없어 정확도와 오탐률을 주장할 수 없습니다.
R01 결과 시간은 그룹 전체 최초 실패이며, R02는 탈취 확정이 아닌 IP 변경 정황입니다.
시나리오 기준 집계와 표시용 principal은 운영 환경에 맞게 보강해야 합니다.
원본 로그·이벤트별 결과는 공개 저장소에서 제외하며 실행 시 다운로드·생성합니다.
데이터 출처: [Splunk attack_data](https://github.com/splunk/attack_data). 사용 조건은 원본 저장소를 확인하세요.
