# 졸업현황2 — HTML 화면 + Python OCR

기존 `graduation-photo-ai`의 OCR·졸업요건 사전 점검 기능을 HTML 화면으로 옮긴 독립 프로젝트입니다. Streamlit은 사용하지 않습니다.

## 설명 문서

- [engine.py 동작 흐름만 보기 — 요구사항·해결 방법·계산 공식](https://p2terghks.github.io/study-notes/%EC%A1%B8%EC%97%85%ED%98%84%ED%99%A92/ENGINE_FLOW_GUIDE.html)

- [바뀐 코드와 데이터 흐름 요약](PROJECT_SUMMARY.md)
- [브라우저용 코드 상세 해설](CODE_GUIDE.html)
- [웹에서 설명 바로 보기](https://p2terghks.github.io/study-notes/%EC%A1%B8%EC%97%85%ED%98%84%ED%99%A92/CODE_GUIDE.html)

## 실행

Mac에서는 `run.command`를 실행하고 **http://127.0.0.1:8504** 를 여세요. 처음 실행 시 Python 3.11 이상과 인터넷이 필요합니다. 이 컴퓨터에서만 접속하도록 설정했습니다.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py --port 8504
```

HTML 파일을 더블클릭하면 OCR·학점 API가 연결되지 않습니다. 반드시 위 Python 서버를 실행하고 주소로 접속하세요. 현재 Mac에서 검증한 정확한 패키지 버전은 `requirements.lock.txt`에 기록합니다.

## 구성과 데이터 흐름

- `templates/index.html`: 화면의 제목, 입력칸, 검토 표, 결과 영역
- `static/style.css`: 반응형 레이아웃과 다크모드
- `static/app.js`: 버튼 처리, 표 편집, API 호출, 결과 표시, 다운로드
- `app.py`: Flask 서버. 사진·텍스트·CSV 요청과 검토 상태를 검증하고 엔진에 전달
- `graduation/ocr.py`: 사전학습 EasyOCR/PyTorch로 사진 인식
- `graduation/engine.py`: 과목 후보 해석 및 학점 계산. 기존 수정 버전과 동일
- `data/curriculum.json`: 2022~2025 × 3개 트랙의 교육과정
- `reference/`: 교육과정 원문 PDF
- `tests/`: 계산 엔진과 HTTP API 검사

브라우저의 `fetch` → Flask API → OCR 또는 계산 함수 → JSON 응답 → JavaScript의 표·결과 갱신 순서입니다. 사진은 FormData로 전송하며, Python은 바이트를 읽어 OCR에 전달합니다. 텍스트와 계산 요청은 JSON으로 보냅니다. 화면에 사용자 입력을 넣을 때는 `textContent`를 사용합니다.

## 주요 기능

1. 연도·트랙 선택, 기준과 원문 PDF 열람
2. 사진 최대 5장(장당 15MB), 텍스트, UTF-8 CSV(2MB) 입력
3. 미해석 행과 OCR 원문 확인, 과목 추가·편집·삭제, 행별 원문 확인
4. 필수로 확인받은 과목 지정, 전공심화 선택 검사
5. 부족학점·검토 사유·제외 내역·추가 확인 항목 표시
6. 검토 내역 CSV, 점검 결과 JSON 다운로드
7. 입력 변경 시 이전 결과 숨김, 기준 변경 시 내역 초기화

사진과 이수 내역은 영구 파일로 저장하지 않습니다. 업로드 파일은 크기 제한을 적용하여 메모리에서 처리하며, 브라우저도 내역을 영구 저장하지 않습니다. 다크모드 선택만 localStorage에 저장합니다. OCR 모델은 `.models/`에 저장합니다. 이 로컬 사본에는 기존에 준비된 모델을 복사했으며, 다른 환경에서는 처음 OCR 사용 시 모델 다운로드가 필요할 수 있습니다.

## 검증

```sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python tools/smoke_ocr.py
```

API 테스트의 사진 인식 테스트는 모델을 대체한 연결 검사입니다. 실제 모델 추론은 별도 `smoke_ocr.py`로 확인합니다. 실제 학생 성적표의 인식률을 검증했다는 뜻은 아닙니다.

## 적용 범위

공식 졸업 판정 도구가 아닙니다. 모든 후보를 원문과 대조해야 합니다. 입력한 전공 과목이 교육과정의 구분·학점과 다르면 합산하지 않습니다. 재수강·대체과목 대응, 교양 의무 과목, 졸업시험·논문·복수전공 등은 학과 확인이 필요합니다. 전공심화는 전공선택에 포함한다는 기존 가정을 유지합니다. 교육과정 추출 시 발견한 경고는 화면에서 확인할 수 있습니다.

로그인·공유 서비스 기능은 없으며 Flask 로컬 개발 서버로 실행합니다. 외부 서비스로 공개하려면 별도의 배포 구성이 필요합니다. 소스와 실행 자료는 study-notes의 `졸업현황2` 폴더에 정리합니다. GitHub Pages는 정적 설명 문서만 제공하며 Python 서버를 실행하지 않습니다.

## 2026-11-03 확인 결과

- 계산 엔진·API 테스트 33개 통과.
- `node tests/test_frontend.cjs`: 초기 로딩, 입력 가져오기, 검토, 결과 표시, 늦게 도착한 결과 무효화, 기준 변경 초기화, 탭·다크모드 검사 통과.
- 실제 브라우저: 텍스트 입력, 미해석 행 표시, 확인 후 3학점 계산, 학점 수정 시 결과 숨김, 30학점 오입력 제외를 확인했습니다.
- 실제 CPU OCR: 가상 사진의 4개 행이 후보 3개·미해석 1개로 보존되었습니다. 구조화된 후보의 정확한 과목명은 전체 4과목 중 1개였고, 사용자가 원문대로 수정한 예시에서는 F를 제외한 9학점으로 계산되었습니다. 이 표본은 일반적인 인식률을 뜻하지 않습니다.
- `preview.png`: 실제 브라우저에서 확인한 시작 화면.
