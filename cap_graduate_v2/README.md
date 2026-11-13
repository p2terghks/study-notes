# cap_graduate v2 · 프로젝트 정리 및 실험 결과

성적표 사진에서 이수 내역을 읽고, 입학년도와 전공에 맞춰 부족한 학점과 수강 후보를 보여주는 파이썬 데스크톱 프로그램이다. 현재 기준은 사용자가 제공한 2022학번 교육과정이며 정보·인공·멀콘을 지원한다.

## 사용 흐름
입학년도와 전공 선택 → 사진에서 과목명 추출 → 표준 과목명 분류 → 교육과정에서 학점·영역 조회 → 이수 내역 검토 → 졸업요건 비교 및 미이수 과목 추천. 검토표는 과목명 | 학점 | 영역 세 열이다.

## v1에서 구현한 졸업요건
- 교양 36학점. 기초 12(생애설계 2, 영어 4, 국어 4, 전산 2), 나사렛 6(기독교·사회봉사·장애인이해 각 2), 핵심 15, 소양 3. 국어는 발표와토론 2학점과 논리 과목 택1을 별도로 확인한다.
- 전공 75학점. 학부공통 30, 본인 전공필수 24, 전공선택 21. 다른 전공 과목과 전공필수 초과분은 전공선택부터 채운다. 남는 학점은 자율선택 16학점에 반영한다. 전체 기준은 127학점이다.
- 성적은 입력받지 않는다. 검토표에는 이수 완료한 과목만 남기며 F·수강 중 과목은 사용자가 제외한다. 같은 과목은 한 번만 합산한다.

## 과목명 유사도 비교
EasyOCR이 읽은 이름을 matcher.match()가 교육과정 목록과 비교한다. 공백과 대소문자를 정리한 뒤 등록된 이름이나 별칭과 같으면 바로 반환한다. 나머지는 자모로 분해해 SequenceMatcher로 비교한다. 최고 유사도가 0.80 이상이고 차순위와 0.04 이상 차이가 나면 채택한다. 모호하면 원문을 검토표에 남긴다. 과목명 보정에는 별도 학습이 필요 없다.

## 실행 및 재현
현재 Mac에서는 이 폴더의 터미널에서 다음 명령을 실행한다.

    ../cap_graduate/.venv/bin/python app.py

다른 컴퓨터에서는 Tk를 포함한 Python 환경에서 다음을 실행한다. 로컬 OCR 모델은 첫 실행 시 이 폴더의 .models에 내려받는다.

    python -m pip install -r requirements.txt
    python app.py

## Windows 실행

Python 3.12 64비트를 설치하고 이 폴더에서 아래 명령을 실행합니다.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

GitHub 배포본은 최초 OCR 실행 시 모델 다운로드를 위한 인터넷 연결이 필요합니다. 다운로드한 모델은 .models에 저장됩니다. Windows 실제 실행은 미검증입니다.
