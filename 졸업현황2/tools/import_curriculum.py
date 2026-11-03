"""Rebuild auditable profiles from the supplied PDF. 2022 is manually transcribed."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import pdfplumber

ROOT = Path(__file__).resolve().parents[1]
TRACKS = ['인공지능빅데이터', '정보통신보안', '스마트미디어']

def build(source):
    source = Path(source)
    dest = ROOT / 'reference' / 'curriculum-2011-2025.pdf'
    if source.resolve() != dest.resolve():
        shutil.copyfile(source, dest)
    profiles = []
    pages = []
    with pdfplumber.open(source) as pdf:
        for i, page in enumerate(pdf.pages):
            pages.append({'page': i+1, 'text': page.extract_text() or '', 'image_only': not bool(page.chars)})
        # 2023-2025 have the same explicit table schema, but separate catalogs.
        for i in range(20, 29):
            page = pdf.pages[i]
            text = page.extract_text()
            year = 2023 + (i-20)//3
            track = TRACKS[(i-20)%3]
            table = next(t for t in page.extract_tables() if len(t)>10 and len(t[0])==10)
            courses, warnings = [], []
            category, level = None, None
            for row in table[3:]:
                if row[0] == '계': break
                if row[0]: level = int(row[0])
                if row[1]: category = row[1].replace('\n','').replace(' ','')
                for semester, offset in [(1,2),(2,6)]:
                    name = (row[offset] or '').replace('\n','').strip()
                    credit = (row[offset+1] or '').strip()
                    if name and credit.isdigit():
                        courses.append({'name':name, 'credits':int(credit), 'category':category,
                                        'level':level, 'semester':semester, 'page':i+1})
                    elif credit.isdigit():
                        warnings.append(f'{i+1}쪽: 과목명이 비어 있는 {credit}학점 셀이 있어 자동 목록에서 제외했습니다.')
            warnings.append('상단 전공필수 최소 12학점과 하단 전공필수 목록 총학점이 다릅니다. 의무 이수 과목은 학과 확인 후 지정하세요.')
            profiles.append({'id':f'{year}-{track}', 'year':year, 'track':track, 'page':i+1,
                'extraction':'PDF 표 추출', 'minimums':{'총학점':127,'기초교양':12 if year==2023 else 10,
                '나사렛교양':6,'핵심교양':15,'소양교양':3,'교양합계':36 if year==2023 else 34,
                '전공필수':12,'전공선택':24,'전공합계':36},'optional_advanced':21,
                'courses':courses,'warnings':warnings})
        # Image-only PDF page 20: transcribed after visual inspection, not copied from 2021.
        common = {
            (1,1,'전공필수'):['파이썬프로그래밍','컴퓨터프로그래밍1','컴퓨터그래픽기초'],
            (1,2,'전공필수'):['컴퓨터프로그래밍2','웹프로그래밍기초'],
            (2,1,'전공필수'):['JAVA'], (2,2,'전공필수'):['DB이론및실습'],
            (3,1,'전공필수'):['모바일프로그래밍'],
            (4,1,'전공필수'):['프로젝트실무1(종합설계)'],
            (4,2,'전공필수'):['프로젝트실무2(종합설계)'],
            (1,1,'전공선택'):['IT개론','대학수학','Lab1(기초설계)'],
            (1,2,'전공선택'):['Lab2(기초설계)'],
            (2,1,'전공선택'):['촬영실무','2D융합디자인','Lab3(기초설계)'],
            (2,2,'전공선택'):['JAVA실무','서버구축실무','콘텐츠기획론','Lab4(기초설계)'],
            (3,1,'전공선택'):['시스코네트워크','고급웹프로그래밍','게임프로그래밍기초','그래픽프로그래밍','데이터분석론','3D영상제작','Lab5(종합설계Startup)'],
            (3,2,'전공선택'):['JAVA프레임워크','모바일프로그래밍응용','고급게임프로그래밍','고급AI프로그래밍','임베디드시스템','전산통계학','Lab6(종합설계Startup)'],
            (4,1,'전공선택'):['증강및가상현실','디지털포렌식','정보통신특론','데이터마이닝','현장실습1','Lab7(종합설계Startup)'],
            (4,2,'전공선택'):['IT실무특강','현장실습2','Lab8(종합설계Startup)']}
        special = {
            '인공지능빅데이터':{(1,2):['이산구조','객체지향프로그래밍'],(2,1):['UNIX','자료구조','컴퓨터네트워크','컴퓨터구조'],(2,2):['JSP/Servlet','운영체제','알고리즘','윈도우즈프로그래밍'],(3,1):['시스템프로그래밍','인공지능이론및실습'],(3,2):['소프트웨어공학','네트워크프로그래밍','빅데이터실무']},
            '정보통신보안':{(1,2):['이산구조','객체지향프로그래밍'],(2,1):['UNIX','자료구조','컴퓨터네트워크','컴퓨터구조'],(2,2):['JSP/Servlet','운영체제','컴퓨터네트워크응용','정보보호개론'],(3,1):['시스템프로그래밍','시스템보안실무'],(3,2):['소프트웨어공학','네트워크프로그래밍','네트워크보안실무']},
            '스마트미디어':{(1,2):['일러스트레이션','웹디자인'],(2,1):['멀티미디어이론및실습','영상편집실무1','3D그래픽'],(2,2):['영상편집실무2','3D그래픽응용','디지털애니메이션'],(3,1):['멀티미디어신호처리','메트페인팅'],(3,2):['UI/UX디자인','컴퓨터비전및응용','VFX']}}
        for track in TRACKS:
            groups = {k:list(v) for k,v in common.items()}
            for (a,b),names in special[track].items():
                groups.setdefault((a,b,'전공필수'),[]).extend(names)
            courses = [{'name':n,'credits':1 if n.startswith('Lab') else 12 if n.startswith('현장실습') else 3,
                        'category':c,'level':a,'semester':b,'page':20}
                       for (a,b,c),names in groups.items() for n in names]
            profiles.append({'id':f'2022-{track}','year':2022,'track':track,'page':20,
                'extraction':'이미지 원문 육안 확인 및 수기 전사 (원문 표기: 멀콘 / 정보 / 인공)',
                'minimums':{'총학점':127,'기초교양':12,'나사렛교양':6,'핵심교양':15,'소양교양':3,
                            '교양합계':36,'전공필수':54,'전공선택':21,'전공합계':75},
                'optional_advanced':None,'courses':courses,'warnings':[
                    '2022 원문은 트랙을 멀콘·정보·인공으로 표시합니다. 화면에서는 대응하는 현재 명칭을 사용합니다.',
                    '2022 상단의 학부공통+전공필수(30+24) 54학점과 하단 목록의 과목 총학점이 다릅니다. 의무 과목 및 이수 인정 범위를 학과에 확인하세요.',
                    '전공심화는 2022 표에 최소학점 수치가 없어 자동 판정하지 않습니다.']})
    data = {'source':dest.name,'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'profiles':sorted(profiles,key=lambda p:(p['year'],TRACKS.index(p['track']))),'pages':pages}
    (ROOT/'data'/'curriculum.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'{len(profiles)} profiles, {sum(len(p["courses"]) for p in profiles)} catalog rows imported')

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('pdf'); build(parser.parse_args().pdf)
