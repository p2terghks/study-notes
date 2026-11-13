"""사용자가 제공한 2022학번 교육과정."""

GROUPS = {
    "학부공통": "파이썬프로그래밍1 컴퓨터프로그래밍1 컴퓨터그래픽기초 JAVA 모바일프로그래밍 프로젝트실무1(종합설계) 컴퓨터프로그래밍2 웹프로그래밍기초 DB이론및실습 프로젝트실무2(종합설계)",
    "멀콘": "멀티미디어이론및실습 영상편집실무1 3D그래픽 멀티미디어신호처리 메트페인팅 일러스트레이션 웹디자인 영상편집실무2 3D그래픽응용 디지털애니메이션 UI/UX디자인 컴퓨터비전및응용 VFX",
    "정보": "UNIX 자료구조 컴퓨터네트워크 컴퓨터구조 시스템프로그래밍 시스템보안실무 이산구조 객체지향프로그래밍 JSP/Servlet 운영체제 컴퓨터네트워크응용 정보보호개론 소프트웨어공학 네트워크프로그래밍 네트워크보안실무",
    "인공": "UNIX 자료구조 컴퓨터네트워크 컴퓨터구조 시스템프로그래밍 인공지능이론및실습 이산구조 객체지향프로그래밍 JSP/Servlet 운영체제 알고리즘 윈도우즈프로그래밍 소프트웨어공학 네트워크프로그래밍 빅데이터실무",
    "전공선택": "IT개론 대학수학 Lab1(기초설계) 촬영실무 2D융합디자인 Lab3(기초설계) 시스코네트워크 고급웹프로그래밍 게임프로그래밍기초 그래픽프로그래밍 데이터분석론 3D영상제작 Lab5(종합설계Startup) 증강가상현실 디지털포렌식 정보통신특론 데이터마이닝 현장실습1 Lab7(종합설계Startup) Lab2(기초설계) JAVA실무 서버구축실무 콘텐츠기획론 Lab4(기초설계) JAVA프레임워크 모바일프로그래밍응용 고급게임프로그래밍 고급AI프로그래밍 임베디드시스템 전산통계학 Lab6(종합설계Startup) IT실무특강 현장실습2 Lab8(종합설계Startup)",
}
GROUPS = {k: v.split() for k, v in GROUPS.items()}

GENERAL = {
    "생애설계": [
        "생애설계와직업진로1=생애설계와직업진로=생애설계와직업진로탐색",
        "생애설계와직업진로2(기업가정신)=생애설계와직업진로2",
    ],
    "영어": [
        "Practical English I=College English I=Practical English Reading",
        "Practical English II=College English II=Practical English Speaking",
    ],
    "국어(필수)": ["발표와토론=독서와구술"],
    "국어(택1)": [
        "논리적사고와글쓰기=읽기와쓰기=쓰기와윤리=독서와논술",
        "논리와비판적사고",
    ],
    "전산": [
        "정보사회와컴퓨터=ICT이해와활용=컴퓨터활용1",
        "컴퓨터코딩이해하기=컴퓨터활용2",
    ],
    "기독교": [
        "성서와인간=성서이해=성서이해하기",
        "하나님과세상",
        "기독교와사회=기독교이해=기독교이해하기",
        "역사와선교",
        "인물로보는기독교",
        "기독교역사",
    ],
    "사회봉사": ["나눔리더십=사회봉사", "나눔실천"],
    "장애인이해": ["장애인의이해=장애인의이해와수화"],
    "소양교양": ["미술의이해와감상"],
}

TARGET = dict(
    zip(
        [
            "생애설계",
            "영어",
            "국어(필수)",
            "국어(택1)",
            "전산",
            "기독교",
            "사회봉사",
            "장애인이해",
            "핵심교양",
            "소양교양",
            "학부공통",
            "전공필수",
            "전공선택",
            "자율선택",
        ],
        [2, 4, 2, 2, 2, 2, 2, 2, 15, 3, 30, 24, 21, 16],
    )
)
GRADES = "F D- D0 D+ C- C0 C+ B- B0 B+ A- A0 A+".split()


# 과목명의 공백과 영문 대소문자 차이를 정리
def key(s):
    return "".join(s.split()).casefold()


CREDITS = {key(n): 3 for courses in GROUPS.values() for n in courses}
for n in GROUPS["전공선택"]:
    # Lab으로 시작하는 과목은 기본 3학점 대신 1학점으로 등록
    if n.startswith("Lab"):
        CREDITS[key(n)] = 1
    # 현장실습1·2는 12학점으로 등록
    elif n in ("현장실습1", "현장실습2"):
        CREDITS[key(n)] = 12

for area, entries in GENERAL.items():
    credits = {"생애설계": 1, "사회봉사": 1, "소양교양": 3}.get(area, 2)
    for entry in entries:
        for alias in entry.split("="):
            CREDITS[key(alias)] = credits
# 채플5와 TLC5의 학점을 0으로 등록
CREDITS.update({key("채플5"): 0, key("TLC5"): 0})


# 학생의 전공을 기준으로 과목명·별칭을 표준 과목명과 이수 영역에 연결
def catalog(track):
    result = {}
    for group in ["멀콘", "정보", "인공", "전공선택", track, "학부공통"]:
        category = (
            "전공필수"
            if group == track
            else "학부공통" if group == "학부공통" else "전공선택"
        )
        for name in GROUPS[group]:
            result[key(name)] = (name, category)
    for category, entries in GENERAL.items():
        for entry in entries:
            names = entry.split("=")
            for alias in names:
                result[key(alias)] = (names[0], category)
    return result


# 중복 이수를 제거하고 졸업요건별 학점과 미이수 추천 과목을 계산
def report(rows, track):
    lookup = catalog(track)
    passed = {}
    for number, (name, credit, category) in enumerate(rows, 1):
        # 과목명이 비었거나 학점이 정수 문자열이 아니면 입력 확인 요청
        if not name.strip() or not credit.isdecimal():
            raise ValueError(f"{number}행의 과목명·학점을 확인하세요.")
        name, category = lookup.get(key(name), (name.strip(), category.strip()))
        # 0학점이 아닌 과목의 영역이 졸업요건에 없으면 분류 확인 요청
        if int(credit) and category not in TARGET:
            raise ValueError(f"{number}행 {name}의 영역을 확인하세요.")
        record = int(credit), category
        # 동일 과목의 중복 기록에서 학점 또는 영역이 다르면 충돌을 알림
        if key(name) in passed and passed[key(name)] != record:
            raise ValueError(f"{name}의 중복 행에서 학점 또는 영역이 다릅니다.")
        passed[key(name)] = record
    # 키가 중복되지 않는 사전을 생성
    totals = dict.fromkeys(TARGET, 0)

    for credit, category in passed.values():
        # 0학점 과목은 영역 합산에서 건너뛰고 양수 학점만 누적
        if credit:
            totals[category] += credit
    totals["전공선택"] += max(0, totals["전공필수"] - 24)
    totals["전공필수"] = min(24, totals["전공필수"])

    for category, minimum in TARGET.items():
        # 다른 영역의 초과 학점만 자율선택으로 이동
        if category != "자율선택":
            totals["자율선택"] += max(0, totals[category] - minimum)
            totals[category] = min(minimum, totals[category])

    lines = [f"총 취득 {sum(totals.values())}학점 / 졸업 기준 127학점"]

    for category, minimum in TARGET.items():
        missing = max(0, minimum - totals[category])
        lines.append(
            f"\n{category}  {totals[category]} / {minimum}학점  ·  "
            + (f"{missing}학점 부족" if missing else "충족")
        )
        # 부족 학점이 있을 때만 해당 영역의 미이수 후보를 검색
        if missing:
            # 키가 중복되지 않는 사전을 생성
            names = dict.fromkeys(
                n for n, c in lookup.values() if c == category and key(n) not in passed
            )
            # 추천할 미이수 후보가 한 과목 이상 있을 때만 후보 문장을 추가
            if names:
                lines.append("이수 후보: " + ", ".join(names))
    return "\n".join(lines)
