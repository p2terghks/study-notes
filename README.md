# p2terghks GitHub

---

## 요약 파일들

개발하면서 배운 개념과 코드 사용법을 정리합니다. 제목을 누르면 요약 자료가 열립니다.

[전체 요약 검색하기](https://p2terghks.github.io/study-notes/?v=20261008-campus-archive) · [학습 자료 저장소](https://github.com/p2terghks/study-notes)

### Spring · 백엔드

- [Spring · JPA 입문 가이드](https://p2terghks.github.io/study-notes/docs/spring-web-guide.html)
- [Spring 기능 · 사용법](https://p2terghks.github.io/study-notes/docs/quick-reference/spring-reference.html)

### React

- [React 입문 가이드](https://p2terghks.github.io/study-notes/docs/react-web-guide.html)
- [React 함수 · Hook](https://p2terghks.github.io/study-notes/docs/quick-reference/react-reference.html)

### 프로그래밍 언어

- [Python 문법 가이드](https://p2terghks.github.io/study-notes/docs/python-syntax-guide.html)
- [C 문법 가이드](https://p2terghks.github.io/study-notes/docs/c-syntax-guide.html)
- [C++ 문법 가이드](https://p2terghks.github.io/study-notes/docs/cpp-syntax-guide.html)
- [R 언어 · 문법과 데이터 처리](https://p2terghks.github.io/study-notes/docs/quick-reference/r-reference.html)

### AWS · 클라우드

- [쿠버네티스 · 테라폼 강의 노트 · 기초부터 실습까지](https://p2terghks.github.io/study-notes/docs/quick-reference/kubernetes-terraform-guide.html) · [예제 ZIP](https://p2terghks.github.io/study-notes/docs/quick-reference/kubernetes-terraform-examples.zip)

- [Boto3 · Python AWS SDK 사용법](https://p2terghks.github.io/study-notes/docs/quick-reference/boto3-reference.html)
- [CI/CD 통합 개발환경 · 클라우드 개발 실무](https://p2terghks.github.io/study-notes/docs/quick-reference/devops-handbook-reference.html)
- [AWS 컴퓨팅 서비스](https://p2terghks.github.io/study-notes/docs/quick-reference/aws-reference.html)
- [AWS CLI · 인증·프로파일·명령어](https://p2terghks.github.io/study-notes/docs/quick-reference/aws-cli-reference.html)
- [Terraform · 문법·명령어·상태 관리](https://p2terghks.github.io/study-notes/docs/quick-reference/terraform-reference.html)

### GitHub · Docker

- [GitHub · Git · 학습 기록 작성법](https://p2terghks.github.io/study-notes/docs/quick-reference/github-reference.html)
- [Docker 사용법](https://p2terghks.github.io/study-notes/docs/quick-reference/docker-reference.html)

### 코딩 테스트

- [코딩 테스트 · 언어별 풀이](https://p2terghks.github.io/study-notes/docs/quick-reference/coding-test-reference.html)

### 클라우드 프로젝트

- [프로젝트 1 · 3-Tier 고가용성](https://p2terghks.github.io/study-notes/docs/quick-reference/cloud-ha-reference.html)
- [프로젝트 2 · Terraform 자동화](https://p2terghks.github.io/study-notes/docs/quick-reference/cloud-iac-reference.html)
- [프로젝트 3 · Docker · ECS CI/CD](https://p2terghks.github.io/study-notes/docs/quick-reference/cloud-cicd-reference.html)
- [프로젝트 4 · 서버리스 이미지 처리](https://p2terghks.github.io/study-notes/docs/quick-reference/cloud-serverless-reference.html)

### 컴퓨터 · 네트워크 기초

- [컴퓨팅 기본 개념 · 코어·스레드·프로세스](https://p2terghks.github.io/study-notes/docs/quick-reference/computing-basics-reference.html)
- [네트워크 기본 개념 · IP·DNS·TCP·HTTP](https://p2terghks.github.io/study-notes/docs/quick-reference/network-basics-reference.html)

### cap_graduate v2 · 성적표 과목명 자동 보정과 졸업요건 검사

정보 전공 학생의 사진에서 OCR이 `모바일프로그래망`을 읽으면, 프로그램은 이를 `모바일프로그래밍`으로 보정하고 교육과정표에서 학부공통 3학점을 조회한다.

| 필요한 기능 | 구현 | 입력과 결과 |
|---|---|---|
| 사진 읽기 | `ocr.recognize(image_bytes)` | 사진 바이트에서 과목명 열을 읽는다. 표를 구분하기 어려우면 글자 위치로 행을 묶는다. |
| 과목명 추출 | `app.review_row(line, track)` | OCR 행 사전에서 과목명을 꺼낸다. 전체 줄만 있으면 제목 행을 제외하고 과목번호·학점·성적 표기를 정리한다. |
| 오독 보정 | `matcher.match(name, track)` | OCR 이름과 선택 전공을 받아 교육과정 목록의 표준 과목명을 찾는다. 판단이 모호하면 검토할 수 있도록 원문을 남긴다. |
| 학점·영역 분류 | `CREDITS`, `rules.catalog(track)` | 보정한 이름으로 학점과 전공별 이수 영역을 조회해 검토표를 채운다. |
| 졸업요건 검사 | `calculate()`, `rules.report(rows, track)` | 검토된 과목을 중복 없이 합산한다. 전공필수 24학점 초과분을 전공선택에 먼저 반영하고 각 영역의 초과분을 자율선택으로 보낸다. 2022학년도 기준 127학점과 영역별 부족분을 표시한다. |
| 과목 추천 | `rules.report(rows, track)` | 부족한 영역에서 이미 이수한 과목을 제외하고 남은 교육과정 과목을 후보로 표시한다. |

**모델이 예측하는 값**은 OCR 이름과 후보 이름이 같은 과목일 점수다. 정확한 이름·별칭과 기존 규칙으로 해결되지 않으면 `features(a, b)`가 글자 유사도, 한글 자모 유사도, 길이 비율, 첫 두 글자 일치, 끝 두 글자 일치, 단계 표기 일치를 계산한다. 학습한 가중치로 후보별 점수를 구해 1위가 0.90 이상이고 2위가 있으면 점수 차이가 0.12 이상일 때 채택한다. 기준에 못 미치면 네 글자 한글 보정 규칙을 확인한다.

### 졸업요건 AI 프로젝트

- [과목명 AI 분류 시스템 · 요구사항과 단계별 코드 설명](https://p2terghks.github.io/study-notes/docs/ai-classification-guide.html)

- [졸업요건 AI · 클릭형 함수 흐름과 문법 설명](https://p2terghks.github.io/study-notes/graduation-photo-ai/FUNCTION_DIAGRAM.html)
- [졸업요건 AI · 전체 코드·함수·Streamlit 상세 해설](https://p2terghks.github.io/study-notes/graduation-photo-ai/DETAILED_CODE_GUIDE.html)
- [졸업요건 AI · 핵심 코드와 발표 가이드](https://p2terghks.github.io/study-notes/graduation-photo-ai/CODE_GUIDE.html)

PyTorch 기반 성적표 OCR과 졸업요건 사전 점검 프로젝트입니다. [전체 소스와 실행 안내](graduation-photo-ai/README.md)를 함께 제공합니다. 클릭형 다이어그램에서는 19개 단계의 코드·기능과 `st`, `st.checkbox()`, `with` 등 46개 기초 설명을 볼 수 있습니다.

### CloudTrail 로그인 기록 추출

- [CloudTrail · 함수·조건문·반복문 상세 요약본](https://p2terghks.github.io/study-notes/cloudtrail-analysis/cloudtrail-function-summary.html)


- [전체 소스와 실행 안내](cloudtrail-analysis/README.md)

ConsoleLogin 이벤트만 찾아 시간·사용자·IP·성공/실패를 출력하고 CSV로 저장합니다. 핵심 R 코드 3개 파일, 총 135줄로 구성되며 실패 기록의 UTC 날짜별·시간대별 시각화를 제공합니다. 새 요약본에서는 함수별 입력·출력과 조건문의 참·거짓 경로를 읽고 코드 줄을 눌러 설명을 확인할 수 있습니다.

## 졸업현황2 — HTML 버전

- [코드·실행 안내](졸업현황2/README.md)
- [변경 요약](졸업현황2/PROJECT_SUMMARY.md)
- [브라우저로 상세 설명 보기](https://p2terghks.github.io/study-notes/%EC%A1%B8%EC%97%85%ED%98%84%ED%99%A92/CODE_GUIDE.html)

HTML·JavaScript 화면과 Flask/Python OCR 서버로 구성합니다. 설명 문서는 웹에서 열 수 있고, 실제 앱은 Python 서버를 실행해야 합니다.
