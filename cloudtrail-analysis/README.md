# CloudTrail 콘솔 로그인 기록 추출

CloudTrail JSON에서 ConsoleLogin 이벤트만 골라 시간·사용자·IP·성공/실패를 출력하고 CSV로 저장합니다.

## 실행

R과 jsonlite가 필요합니다.

```sh
Rscript -e 'install.packages("jsonlite")'
Rscript login_records.R 로그.json
Rscript login_records.R 로그.json 결과.csv
```

출력 경로 기본값은 output/login_records.csv입니다. ConsoleLogin이 없으면 헤더만 저장합니다.
사용자 이름이 없으면 ARN을 사용하고, 누락된 필드는 CSV 빈칸으로 저장합니다.
Records 문서·이벤트 배열·단일 이벤트·NDJSON을 지원합니다. UTF-8 입력을 읽습니다.
입력과 출력은 서로 다른 경로를 지정하세요. 출력 경로에 기존 파일이 있으면 덮어씁니다.

## 코드 규모

실행 코드 login_records.R 하나, 주석·빈 줄 포함 73줄입니다. 테스트와 설명 문서는 별도입니다.
이전 반복 실패·IP 변경·MFA 탐지 규칙, 자동 다운로드, 기법 라벨 평가와 차트는 제거했습니다.
이전 버전은 Git 커밋 기록에서 확인할 수 있습니다.

## 설명 자료

- [전체 코드 설명](https://p2terghks.github.io/study-notes/cloudtrail-analysis/cloudtrail-code-guide.html)
- [클릭형 요약본](https://p2terghks.github.io/study-notes/cloudtrail-analysis/cloudtrail-interactive-diagram.html)

## 검증

가상 이벤트로 실제 R 실행과 CSV 저장을 확인했습니다.
Records·배열·단일 이벤트·NDJSON·빈 파일·로그인 없는 파일·잘못된 JSON,
성공/실패 유지·시간 정렬·ARN 대체·누락값 검사를 통과했습니다.

```sh
Rscript tests/test_login_records.R
```

실제 로그인·공격 데이터로 성능을 평가한 결과는 아닙니다. 입력 로그와 CSV 결과는 공개 저장소에 포함하지 않습니다.
시각 정렬은 CloudTrail의 일반적인 UTC ISO 시각 문자열을 전제로 합니다. 중복 이벤트는 제거하지 않습니다.
파일 전체를 메모리에 읽습니다. 이 도구가 AWS에서 직접 로그를 수집하지는 않습니다.

## R 입문자 설명

기본 요약본은 클릭형 처리 순서 페이지입니다. 각 상자를 누르면 관련 코드의 줄별 설명을 확인할 수 있습니다. 전체 코드 해설과 클릭형 처리 순서에는 각 실행 줄의 문법과 역할을 설명합니다. 함수는 정의한 뒤 호출할 때 실행되며, 마지막 표현식을 자동 반환한다는 R의 동작도 예시로 설명합니다.
