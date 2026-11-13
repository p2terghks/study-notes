from pathlib import Path
from functools import lru_cache

# 이 파일이 있는 폴더: OCR 모델을 저장할 .models 경로의 기준
ROOT = Path(__file__).resolve().parent


# 한국어·영어 OCR 판독기를 준비하고 재사용
# 최초 호출의 Reader를 기억하므로 사진마다 무거운 모델을 다시 만들지 않음
@lru_cache(maxsize=1)
def get_reader():
    import os
    import certifi

    # 인증서 경로가 설정되어 있지 않으면 certifi의 인증서 파일을 사용
    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
    import easyocr
    import torch

    # CUDA GPU가 있으면 사용하고, 없으면 CPU로 인식
    return easyocr.Reader(
        ["ko", "en"],
        gpu=torch.cuda.is_available(),
        model_storage_directory=str(ROOT / ".models"),
        user_network_directory=str(ROOT / ".models" / "user_network"),
        verbose=False,
    )


# 사진의 방향과 크기를 정리한 뒤 OCR로 읽은 행과 위치 정보를 반환
def recognize(image_bytes):
    import io
    import numpy as np
    from PIL import Image, ImageOps

    # 입력은 이미 app.worker에서 read_bytes()로 읽은 사진 파일의 bytes
    # BytesIO: 바이트를 메모리 안의 파일처럼 감쌈 → Image.open: 이미지로 해석
    source = Image.open(io.BytesIO(image_bytes))
    # 사진이 2,400만 픽셀을 넘으면 메모리 사용을 제한하기 위해 처리 중단
    if source.width * source.height > 24_000_000:
        raise ValueError("이미지는 2,400만 화소 이하로 줄여주세요.")
    # 사진의 EXIF 방향 정보를 반영한 뒤 빨강·초록·파랑 3채널 형식으로 통일
    image = ImageOps.exif_transpose(source).convert("RGB")
    # 가로·세로 2600픽셀 안에 들어가도록 비율을 유지해 축소
    image.thumbnail((2600, 2600))
    # PIL 이미지 → (높이, 너비, RGB 3채널) 형태의 NumPy 숫자 배열
    pixels = np.array(image)
    # 먼저 표의 칸을 구분해 과목명만 읽는 방식을 시도
    table_lines = recognize_grid_table(pixels)

    # 표 구조를 읽었으면 그 결과를 반환하고 전체 이미지 OCR은 생략
    if table_lines is not None:
        return table_lines, []
    # 표 인식 결과가 None이면 전체 이미지에서 글자 영역을 검출하고 읽음
    # detections: [(네 꼭짓점 좌표, 인식 문자열, 신뢰도), ...]
    detections = get_reader().readtext(
        pixels, detail=1, paragraph=False, min_size=5, mag_ratio=2, canvas_size=3200
    )
    # boxes: 글자 영역 하나마다 위치·크기·문자열·신뢰도를 담는 딕셔너리 리스트
    boxes = []

    # box는 [[x1, y1], ..., [x4, y4]] 형태의 네 꼭짓점
    for box, text, confidence in detections:
        # x좌표만, y좌표만 따로 꺼내 왼쪽 위치·중심 높이·영역 높이를 계산
        xs = [p[0] for p in box]
        ys = [p[1] for p in box]
        boxes.append(
            {
                "x": float(min(xs)),
                "y": float(sum(ys) / 4),
                "height": float(max(ys) - min(ys)),
                "text": text,
                "confidence": float(confidence),
            }
        )
    # groups: 같은 줄에 속하는 글자 영역들을 묶은 리스트 안의 리스트
    # 예: [[자료구조 영역, 3 영역, A+ 영역], [다음 행의 영역들]]
    groups = []
    # y좌표가 작은 위쪽 글자부터 처리
    for item in sorted(boxes, key=lambda b: b["y"]):
        # 기존 행의 첫 영역과 높이가 가까운 첫 그룹을 찾고, 없으면 None
        # 허용 거리: 최소 7픽셀 또는 두 영역 중 작은 높이의 절반
        target = next(
            (
                g
                for g in groups
                if abs(g[0]["y"] - item["y"])
                <= max(7, min(g[0]["height"], item["height"]) * 0.5)
            ),
            None,
        )
        # 같은 행으로 묶을 그룹이 없으면 새 행 그룹 생성
        if target is None:
            groups.append([item])
        else:
            target.append(item)
    # 각 행 안에서는 x좌표 순으로 정렬해 왼쪽부터 문자열을 연결
    # 행 신뢰도는 해당 행의 글자 영역 신뢰도 중 가장 낮은 값
    lines = [
        {
            "text": " ".join(b["text"] for b in sorted(g, key=lambda b: b["x"])),
            "confidence": min(b["confidence"] for b in g),
        }
        for g in groups
    ]
    # 반환은 튜플: (행 딕셔너리 리스트, 글자 영역 딕셔너리 리스트)
    # 예: lines = [{"text": "자료구조 3 A+", "confidence": 0.95}]
    # app.worker는 lines만 사용하며 boxes는 _로 받아 사용하지 않음
    return lines, boxes


# 이미지에서 표의 가로선과 세로선 위치를 검출
def grid_boundaries(pixels):
    """Find a fully ruled transcript table; fall back for other layouts."""
    import cv2
    import numpy as np

    # RGB 색상 이미지를 회색조 밝기 이미지로 변환
    gray = cv2.cvtColor(pixels, cv2.COLOR_RGB2GRAY)
    # 밝기 225를 기준으로 글자·선을 강조하는 이진 이미지 생성
    ink = cv2.threshold(gray, 225, 255, cv2.THRESH_BINARY_INV)[1]
    # 2차원 배열의 크기: h는 높이(행 수), w는 너비(열 수)
    h, w = gray.shape

    # 지정한 방향의 긴 선을 찾아 각 선의 중심 좌표를 반환
    def positions(vertical):
        # vertical=True면 세로로 긴 검사 도구, False면 가로로 긴 검사 도구
        kernel = (1, max(30, h // 2)) if vertical else (max(30, w // 2), 1)
        # 가로나 세로로 긴 구조를 남겨 표 선을 검출
        mask = cv2.morphologyEx(
            ink, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, kernel)
        )
        # 각 행 또는 열에서 검출된 선 픽셀 개수를 셈
        counts = np.count_nonzero(mask, axis=0 if vertical else 1)
        # 선 길이 조건을 만족하는 위치의 좌표를 구함
        indices = np.flatnonzero(counts > (h if vertical else w) * 0.65)
        groups = []
        for value in indices:
            # 첫 좌표이거나 이전 좌표와 떨어졌으면 새로운 표 선 그룹 생성
            if not groups or value > groups[-1][-1] + 1:
                groups.append([int(value)])
            else:
                groups[-1].append(int(value))
        return [round(sum(g) / len(g)) for g in groups]

    # 반환: 회색조 이미지, 세로선 x좌표 리스트, 가로선 y좌표 리스트
    return gray, positions(True), positions(False)


# 표의 과목명 열을 찾아 각 셀에서 과목명을 추출
def recognize_grid_table(pixels):
    """Read explicit cells only for the seven-column transcript layout.

    No catalog-based correction: uncertain names remain review candidates.
    """
    import cv2
    import numpy as np

    # xs의 이웃 좌표 두 개가 한 열, ys의 이웃 좌표 두 개가 한 행의 경계
    gray, xs, ys = grid_boundaries(pixels)
    # 검출한 표 경계가 부족하면 전체 이미지 인식으로 넘김
    if len(xs) < 4 or len(ys) < 3:
        return None
    reader = get_reader()

    # 지정한 행과 열의 셀을 확대해 문자열과 인식 점수를 반환
    def cell(col, row, allowed=None):
        # 배열은 [세로 범위, 가로 범위]로 자름; 테두리 선을 피하려고 3픽셀씩 안쪽 사용
        crop = gray[ys[row] + 3 : ys[row + 1] - 3, xs[col] + 3 : xs[col + 1] - 3]
        # 잘라낸 셀에 픽셀이 없으면 빈 문자열과 0점 반환
        if not crop.size:
            return "", 0.0
        # 작은 셀의 글자를 가로·세로 두 배로 확대
        crop = cv2.resize(crop, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        # 셀 가장자리에 흰색 여백 12픽셀을 추가
        crop = np.pad(crop, 12, constant_values=255)
        h, w = crop.shape
        # 셀 전체를 하나의 글자 영역으로 지정해 OCR 문자열·점수를 받음
        found = reader.recognize(
            crop,
            horizontal_list=[[0, w, 0, h]],
            free_list=[],
            detail=1,
            allowlist=allowed,
            paragraph=False,
        )
        # found의 각 결과에서 v[1]은 문자열, v[2]는 신뢰도
        # 반환: (셀의 문자열, 최저 신뢰도); 결과가 없으면 신뢰도는 0
        return (
            " ".join(v[1] for v in found).strip(),
            min((float(v[2]) for v in found), default=0.0),
        )

    # 왼쪽 외곽선이 누락된 경우 이미지 왼쪽 끝을 경계로 추가
    if xs[0] > 10:
        # 세로 경계 좌표 목록의 맨 앞에 0을 추가
        xs.insert(0, 0)
    # headers: 표준 열 이름 → 열 번호. 예: {"과목명": 4, "학점": 5}
    # 열 번호는 0부터 시작하므로 4는 다섯 번째 열
    headers = {}

    # 경계가 N개이면 그 사이의 열은 N-1개; 0번 행을 제목 행으로 읽음
    for col in range(len(xs) - 1):
        text, _ = cell(col, 0)
        field = header_field(text)
        # 열 제목을 표준 이름으로 해석했을 때만 열 번호를 기록
        if field:
            headers[field] = col
    # 과목명 칸 너비와 학점 열 위치로 예시 표의 구조인지 확인
    # 경계 개수·학점 열 위치·과목명 칸 너비가 예시 표 구조에 맞으면 열 번호 보완
    if (
        len(xs) in (8, 9)
        and headers.get("학점") == 5
        and xs[5] - xs[4] > 3 * (xs[6] - xs[5])
    ):
        # 확인한 표 구조에 맞는 열 이름과 번호를 사전에 반영
        headers.update({"과목명": 4, "학점": 5, "성적": 6, "과목번호": 3})
        # 8개 열을 가진 표이면 마지막 열을 교양영역으로 기록
        if len(xs) == 9:
            headers["교양영역"] = 7

    # 과목명 열을 찾지 못했으면 표 셀 인식을 중단하고 다른 방식으로 읽기
    if "과목명" not in headers:
        return None
    # 각 행 안에서는 x좌표 순으로 정렬해 왼쪽부터 문자열을 연결
    # 행 신뢰도는 해당 행의 글자 영역 신뢰도 중 가장 낮은 값
    lines = []

    # 0번 제목 행을 제외하고 과목명 셀만 읽음: 학점·성적 셀은 여기서 읽지 않음
    # lines: [{"과목명": "자료구조", "confidence": 0.95}, ...]
    for row in range(1, len(ys) - 1):
        name, score = cell(headers["과목명"], row)
        lines.append({"과목명": name or "이름 확인 필요", "confidence": score})
    return lines


# OCR로 읽은 열 제목을 정리해 프로그램에서 사용하는 이름으로 변환
def header_field(text):
    import re

    # 한글 이외의 문자·공백을 제거해 열 제목을 비교하기 쉽게 정리
    # 이 key는 문자열 변수이며 rules.py의 key() 함수와는 별개
    key = re.sub(r"[^가-힣]", "", text)
    # 대응표에 없는 제목이면 get()은 None 반환
    return {
        "과목명": "과목명",
        "교양영역": "교양영역",
        "과목영": "과목명",
        "교과목명": "과목명",
        "학점": "학점",
        "취득학점": "학점",
        "성적": "성적",
        "등급": "성적",
        "과목번호": "과목번호",
        "과목코드": "과목번호",
        "이수구분": "원문이수구분",
        "년도학기": "수강학기",
        "연도학기": "수강학기",
        "년되학기": "수강학기",
    }.get(key)
