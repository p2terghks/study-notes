# 졸업현황2 — HTML 화면 전환 요약

2026-11-03 기준. 사진 속 성적표를 읽고 사용자가 검토한 이수 내역을 교육과정과 비교하는 **졸업 사전 점검 시스템**입니다. 화면은 HTML·CSS·JavaScript, 서버는 Flask/Python, 문자 인식은 EasyOCR/PyTorch로 구성합니다.

## 이전 버전에서 달라진 점

| 구분 | 기존 Streamlit | 졸업현황2 |
|---|---|---|
| 화면 | `st.*` 함수가 화면 생성 | `templates/index.html` + `static/style.css` |
| 입력 이벤트 | 위젯 조작으로 Python 재실행 | JavaScript 이벤트 → 필요한 API만 요청 |
| 사진 전송 | `photo.getvalue()` | 브라우저 File → FormData → 서버 `photo.read()` |
| 표 편집 | `st.data_editor`, pandas DataFrame | JavaScript 객체 배열 → HTML 표와 input/select |
| 상태 보관 | `st.session_state` | 브라우저 변수 `rows`, `result`, `epoch` 등 |
| 이전 결과 무효화 | 입력 SHA-256 지문 비교 | `invalidate()`가 결과 숨김, `epoch`로 늦은 응답 차단 |
| 검토 절차 | 화면의 체크박스 | 화면 체크와 서버의 검토 토큰·입력 검증 |
| 결과 표시 | `st.dataframe`, `st.metric` | JSON 응답 → `renderResult()`가 DOM 갱신 |
| 저장 | Streamlit 다운로드 버튼 | `Blob` + 임시 URL + 다운로드 링크 |
| 실행 주소 | localhost:8503 | localhost:8504 |

OCR·계산 핵심 함수와 교육과정 데이터는 기존 수정 버전을 그대로 사용합니다. Flask로 바꿨다고 OCR 정확도가 높아지는 것은 아닙니다.

## 화면과 코드가 연결되는 순서

1. 브라우저가 `/`를 요청하면 `index()`가 HTML을 반환합니다. CSS와 JavaScript를 따로 불러옵니다.
2. JavaScript가 `GET /api/config`를 호출하여 12개 교육과정과 이수구분 목록을 받습니다.
3. 사진은 `POST /api/ocr`, 텍스트는 `/api/parse`, CSV는 `/api/csv`로 전송합니다.
4. 서버는 과목 후보 `rows`, 미해석 행 `rejected`, 원문 `raw`, 검토 토큰 `review_token`을 JSON으로 반환합니다.
5. `setRows()`가 브라우저 상태를 바꾸고 `renderRows()`가 편집 표를 만듭니다.
6. 사용자가 표를 수정하면 해당 행의 확인을 해제하고 이전 결과를 숨깁니다.
7. 점검 버튼은 `/api/audit`로 검토 내역과 선택 기준을 보냅니다.
8. `check()`가 입력 형식과 검토 절차를 확인한 뒤 `audit()`에 넘깁니다.
9. `audit()`의 계산 결과를 `renderResult()`가 부족학점 표와 안내로 표시합니다.

## 자료형은 왜, 어디서 바뀌나요?

### 사진: File → FormData → bytes

```javascript
const form = new FormData();
form.append('profile', profile.id);
files.forEach(f => form.append('photos', f));
setRows(await api('/api/ocr', form));
```

브라우저의 `File`은 사용자가 선택한 파일을 나타냅니다. `FormData`는 사진과 교육과정 ID를 HTTP 요청에 함께 넣기 위한 전송 형식입니다. JavaScript가 사진을 딕셔너리로 형변환하는 것이 아닙니다. `api()`는 FormData일 때 Content-Type을 직접 지정하지 않고 브라우저가 multipart 경계값을 포함해 정하도록 둡니다.

```python
photos = request.files.getlist('photos')
content = photo.read(15 * 1024 * 1024 + 1)
lines, _ = recognize(content)
```

서버의 업로드 파일 객체에서 `read()`로 bytes를 읽습니다. JPEG/PNG는 이미 파일 바이트로 인코딩되어 있으므로 `bytes(photo)`로 새로 형변환하지 않습니다. 최대 허용량보다 1바이트 더 읽어 초과를 검사합니다. 업로드는 크기 제한 아래 메모리에서 처리합니다.

### bytes → 이미지 객체 → NumPy 배열

```python
source = Image.open(io.BytesIO(image_bytes))
image = ImageOps.exif_transpose(source).convert('RGB')
image.thumbnail((2600, 2600))
detections = get_reader().readtext(np.array(image), detail=1, paragraph=False)
```

`BytesIO`는 bytes를 파일처럼 읽을 수 있게 감쌉니다. `Image.open`은 파일 형식을 해석하고, 실제 코드에서는 화소 수를 먼저 검사한 뒤 방향·색상을 정리합니다. `np.array(image)`는 픽셀을 `(높이, 너비, 3)` 형태의 RGB 숫자 배열로 만듭니다. 이후 EasyOCR 내부에서 모델용 전처리·텐서 변환이 이뤄집니다. 이 프로젝트가 직접 `torch.tensor()`를 호출하지는 않습니다.

### OCR 결과 → 딕셔너리 목록

```python
boxes.append({'x': float(min(xs)), 'y': float(sum(ys) / 4),
              'height': float(max(ys) - min(ys)),
              'text': text, 'confidence': float(confidence)})
```

한 문자 영역은 위치·문자·신뢰도를 가진 딕셔너리입니다. `boxes`는 여러 영역을 담은 리스트입니다. `append({...})`는 딕셔너리 하나를 만들어 리스트 끝에 붙이는 코드입니다. 이후 위치별로 묶고 문자열을 이어 붙여 `lines`를 만듭니다.

### 문자열 학점 → float / 과목 정보 → rows

```python
name, credits, grade = match.groups()
```

정규표현식의 추출값은 문자열입니다. 후보 딕셔너리를 만들 때 `float(credits)`로 `'3'`을 `3.0`으로 바꿔 합산할 수 있게 합니다. `rows.append({...})`로 한 과목을 리스트에 추가합니다. 정확히 일치하는 과목만 자동 분류하며, 확인은 False로 시작합니다. 해석에 실패한 줄은 원문과 이유를 `rejected`에 남깁니다.

### Python 자료구조 → JSON → JavaScript 객체

`jsonify()`는 Python 딕셔너리·리스트를 JSON HTTP 응답으로 직렬화합니다. 브라우저의 `await response.json()`은 JSON을 JavaScript 객체·배열로 해석합니다. Python dict와 JavaScript object는 같은 메모리 객체가 아니며, 네트워크에서 JSON을 통해 정보를 주고받습니다.

### JavaScript 객체 배열 → HTML 표

`rows.forEach()`로 과목을 순회하고 `document.createElement()`로 tr·td·input·select를 만듭니다. 화면 텍스트는 `textContent`, 편집값은 `input.value`로 넣습니다. 입력 이벤트에서 `row[key] = input.value`로 메모리 데이터를 바꿉니다. HTML 표 자체를 서버로 보내는 것이 아니라 이 객체 배열을 JSON으로 보냅니다. 숫자 입력칸의 value도 문자열일 수 있어 서버 계산 단계에서 다시 숫자로 검사합니다. 새 버전은 pandas DataFrame을 사용하지 않습니다.

### 점검 요청 → 결과 → 다운로드

`JSON.stringify()`로 요청 객체를 문자열로 직렬화하고 Flask의 `request.get_json()`으로 다시 읽습니다. 서버는 확인·학점·성적·교육과정·중복을 검사하고 인정 가능한 행만 합산합니다. 결과를 다운로드할 때는 `JSON.stringify(result, null, 2)`와 `new Blob()`을 사용합니다. 이는 브라우저 다운로드를 준비하는 코드이며 서버 디스크에 성적표를 저장하지 않습니다.

## 상태와 검토 토큰

- `invalidate()`: epoch를 1 올리고 결과를 숨깁니다. 입력이나 기준을 바꿨을 때 이전 결과를 무효화합니다.
- `epoch`: 요청을 보낸 시점의 값과 응답 시점의 값이 다르면 늦게 도착한 결과를 버립니다.
- `busy` / `task()`: 중복 요청을 줄이고 실패 메시지를 표시한 뒤 버튼 상태를 복구합니다.
- `review_token`: 서버가 교육과정 ID와 미해석 행 개수에 서명한 값입니다. 위조 여부·기준 일치 여부를 확인하고, 미해석 행이 있었다면 추가 확인을 요구합니다.
- 토큰은 성적표 진위나 사용자가 실제로 원문을 읽었다는 증거가 아닙니다. 사진 내용의 암호화도 아닙니다. 서버를 재시작하면 기존 토큰은 무효가 되어 입력을 다시 불러와야 합니다.
- `rows` 등은 브라우저 메모리에 있으며 새로고침하면 사라집니다. localStorage에는 다크모드 선택만 저장합니다.

## 검증과 한계

계산·API 테스트 33개, JavaScript 상태 전환 검사, 실제 브라우저 입력·검토·결과 표시를 확인했습니다. 실제 OCR 가상 사진은 4행 중 후보 3개·미해석 1개로 보존됐고, 원문대로 수정한 예시는 F를 제외한 9학점으로 계산됐습니다. 정확한 과목명은 전체 4과목 중 1개로 나타나 원문 검토가 필요합니다. 작은 가상 표본의 결과를 일반적인 정확도로 해석하지 않습니다.

공식 재수강·대체과목, 졸업시험·논문·교양 의무 과목·복수전공 등은 학과 확인이 필요합니다. 전공심화를 전공선택에 포함하는 기존 가정을 유지합니다. 모델 파일과 가상환경은 GitHub에 포함하지 않으며, 최초 실행 시 패키지·모델 다운로드가 필요할 수 있습니다.

**GitHub Pages에서는 설명 HTML만 볼 수 있습니다. 실제 앱의 OCR·계산 기능은 Python 서버를 실행해야 동작합니다.**
