# Python 심화 실습 — CSV 성적 분석기

[상세 강의로 돌아가기](../../python-advanced-reference.html#item-21)

Python 3.11 이상과 표준 라이브러리만 사용합니다. 다음 세 파일을 같은 폴더에 저장하세요.

- [analyzer.py](analyzer.py): 입력 검증·분석·JSON 저장
- [test_analyzer.py](test_analyzer.py): 정상·빈 입력·경계값·잘못된 행·실패 시 출력 보존 테스트
- [students.csv](students.csv): 실행용 입력

터미널에서 이 폴더로 이동한 뒤 실행합니다.

```bash
python analyzer.py students.csv --output report.json
python -m unittest -v
```

macOS/Linux에서 `python` 명령이 없다면 `python3`를 사용하세요. Windows에서는 `py -3`도 사용할 수 있습니다.

결과: 인원 3명, 평균 73.33, A·B·F 각 1명, 팀 A 2명·B 1명, 합격자 Kim·Lee. 같은 내용이 터미널과 `report.json`에 출력됩니다. 정상 실행 시 기존 출력 파일은 덮어씁니다.

CSV 헤더는 `name,team,score` 순서입니다. 이름·팀은 비어 있으면 안 되며 점수는 0~100 정수입니다. 잘못된 입력은 오류 종료 코드 2와 줄 번호를 표시합니다. 입력 분석 실패 시 기존 출력 파일을 유지합니다. 빈 데이터는 평균을 JSON `null`로 저장합니다.

학습 과제: 팀별 평균 추가, 합격 기준 설정, 오류 행 수집 정책, 모델·서비스·CLI 모듈 분리. 각 변경 전에 기대 결과를 테스트에 추가해 보세요.
