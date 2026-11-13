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

### 클라우드 프로젝트

- [프로젝트 1 · 3-Tier 고가용성](https://p2terghks.github.io/study-notes/docs/quick-reference/cloud-ha-reference.html)
- [프로젝트 2 · Terraform 자동화](https://p2terghks.github.io/study-notes/docs/quick-reference/cloud-iac-reference.html)
- [프로젝트 3 · Docker · ECS CI/CD](https://p2terghks.github.io/study-notes/docs/quick-reference/cloud-cicd-reference.html)
- [프로젝트 4 · 서버리스 이미지 처리](https://p2terghks.github.io/study-notes/docs/quick-reference/cloud-serverless-reference.html)

### 컴퓨터 · 네트워크 기초

- [컴퓨팅 기본 개념 · 코어·스레드·프로세스](https://p2terghks.github.io/study-notes/docs/quick-reference/computing-basics-reference.html)
- [네트워크 기본 개념 · IP·DNS·TCP·HTTP](https://p2terghks.github.io/study-notes/docs/quick-reference/network-basics-reference.html)

### 졸업요건 AI 프로젝트 · cap_graduate v2

- [전체 19개 함수 관계 다이어그램](https://p2terghks.github.io/study-notes/cap_graduate_v2/docs/함수_관계_다이어그램.html)
- [함수별 코드 읽기 · 매개변수·변수·메서드·반복문·조건문](https://p2terghks.github.io/study-notes/cap_graduate_v2/docs/함수별_코드_읽기.html)

Tkinter 데스크톱 앱에서 사진을 선택하면 로컬 EasyOCR이 과목명을 읽습니다. 과목명과 공식 별칭을 자모 유사도로 비교한 뒤 교육과정의 학점·영역을 조회하고, 사용자가 검토한 내역을 중복 없이 합산해 2022학번 졸업요건 127학점과 비교합니다.

`load → worker → recognize → review_row → match → 검토표 → calculate → report` 순서로 처리합니다. 표의 과목명 열을 찾지 못하면 전체 OCR 결과를 좌표로 묶습니다.

현재 보정 기준은 최소 유사도 **0.80**, 1·2위 차이 **0.04**입니다. 2026-11-13 사진 한 장을 재시험한 결과 0.80에서는 9개 행 중 8개가 연결되고 `TLCs`는 확인 대상으로 남았습니다. 0.75 테스트에서는 9개가 연결되어 총 18학점을 계산했습니다. 0.75는 테스트에만 적용했으며, Windows 실제 실행은 아직 검증하지 않았습니다.

## 졸업현황2 — HTML 버전

- [코드·실행 안내](졸업현황2/README.md)
- [변경 요약](졸업현황2/PROJECT_SUMMARY.md)
- [브라우저로 상세 설명 보기](https://p2terghks.github.io/study-notes/%EC%A1%B8%EC%97%85%ED%98%84%ED%99%A92/CODE_GUIDE.html)

HTML·JavaScript 화면과 Flask/Python OCR 서버로 구성합니다. 설명 문서는 웹에서 열 수 있고, 실제 앱은 Python 서버를 실행해야 합니다.
