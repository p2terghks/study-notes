"""Deterministic credit audit; OCR never decides graduation eligibility."""
import math
import re
import unicodedata
from difflib import get_close_matches

CATEGORIES = ['전공필수','전공선택','전공심화','기초교양','나사렛교양','핵심교양','소양교양','자율선택','미분류']
PASS_GRADES = {'A+','A0','A','A-','B+','B0','B','B-','C+','C0','C','C-','D+','D0','D','D-','P','PASS','S','이수','이수완료'}
FAIL_GRADES = {'F','NP','N','U','FAIL','W','철회','미이수','수강중'}

def normalize(value):
    return re.sub(r'\s+','',unicodedata.normalize('NFKC',str(value or ''))).casefold()

def catalog_index(profile):
    return {normalize(c['name']):c for c in profile['courses']}

def suggest(name, profile):
    catalog=catalog_index(profile); key=normalize(name)
    if key in catalog: return catalog[key], True
    near=get_close_matches(key,list(catalog),n=1,cutoff=.65)
    return (catalog[near[0]],False) if near else (None,False)

def parse_lines_with_review(lines, profile):
    """Return candidates and every nonempty unparsed line for manual review."""
    rows, rejected = [], []
    grades = sorted(PASS_GRADES | FAIL_GRADES, key=len, reverse=True)
    grade_pattern = "(?:" + "|".join(re.escape(g) for g in grades) + ")"
    pattern = re.compile(
        rf"^\s*(.+?)\s+(\d+(?:\.\d+)?)\s*(?:학점\s*)?"
        rf"({grade_pattern})(?:\s+(?:[0-4](?:\.\d+)?|5(?:\.0+)?))?\s*$", re.I)
    for line in lines:
        text = line['text'] if isinstance(line, dict) else line
        confidence = line.get('confidence', 1.0) if isinstance(line, dict) else 1.0
        text = text.strip()
        if not text:
            continue
        if re.match(r'^(총학점|합계|취득학점|평균|신청학점)(?:\s|$)', text):
            continue
        match = pattern.fullmatch(text)
        if match:
            name, credits, grade = match.groups()
            # A prior grade/credit pair indicates merged columns or two courses.
            if re.search(rf"\s\d+(?:\.\d+)?\s+{grade_pattern}(?=\s|$)", name, re.I):
                rejected.append({'text': text, 'reason': '한 줄에 여러 과목이 있어 분리해야 합니다.'})
                continue
        else:
            missing_grade = re.fullmatch(r'(.+?)\s+(\d+(?:\.\d+)?)\s*', text)
            if not missing_grade or not suggest(missing_grade[1], profile)[1]:
                rejected.append({'text': text, 'reason': '과목명·학점·성적 열을 확인하세요.'})
                continue
            name, credits = missing_grade.groups()
            grade = ''
        course, exact = suggest(name, profile)
        rows.append({'과목명': course['name'] if exact else name, '학점': float(credits),
                     '이수구분': course['category'] if exact else '미분류', '성적': grade.upper(),
                     '확인': False, '인식신뢰도': round(float(confidence), 3),
                     '메모': '' if exact else f'과목 후보: {course["name"]}' if course else '교육과정 목록에 없음'})
    return rows, rejected


def parse_lines(lines, profile):
    """Compatibility helper; interactive imports use parse_lines_with_review."""
    return parse_lines_with_review(lines, profile)[0]

def audit(rows, profile, mandatory=(), advanced=False):
    catalog=catalog_index(profile)
    totals={c:0.0 for c in CATEGORIES}
    accepted={}; issues=[]; excluded=[]
    for i,row in enumerate(rows,1):
        name=str(row.get('과목명','') or '').strip()
        if not name: continue
        if row.get('확인') is not True:
            issues.append(f'{i}행 {name}: 원문 확인이 필요합니다.'); continue
        category=row.get('이수구분','미분류')
        if category not in CATEGORIES or category=='미분류':
            issues.append(f'{i}행 {name}: 이수구분을 지정하세요.'); continue
        try: credits=float(row.get('학점'))
        except (ValueError,TypeError): credits=float('nan')
        if not math.isfinite(credits) or credits<=0 or credits>30:
            issues.append(f'{i}행 {name}: 유효한 학점(0 초과 30 이하)을 입력하세요.'); continue
        grade=str(row.get('성적','')).strip().upper()
        if grade in FAIL_GRADES:
            excluded.append(f'{name}: {grade} (취득학점 제외)'); continue
        if grade not in PASS_GRADES:
            issues.append(f'{i}행 {name}: 성적을 확인하세요.'); continue
        key=normalize(name)
        course = catalog.get(key)
        if course and (credits != float(course['credits']) or category != course['category']):
            issues.append(f'{i}행 {name}: 교육과정은 {course["category"]} {course["credits"]}학점입니다. 입력을 수정하거나 학과에서 인정 기준을 확인하세요.')
            continue
        if not course and category.startswith('전공'):
            issues.append(f'{i}행 {name}: 교육과정에 없는 전공 과목입니다. 과목명·대체 인정 여부를 확인하세요.')
            continue
        # Conflicting repeated records require a user decision, never a silent sum.
        if key in accepted:
            old=accepted[key]
            if old['학점']!=credits or old['이수구분']!=category:
                issues.append(f'{name}: 중복 내역의 학점 또는 구분이 다릅니다. 한 행만 남기세요.')
            else: excluded.append(f'{name}: 중복 취득은 1회만 계산')
            continue
        accepted[key]={'과목명':name,'학점':credits,'이수구분':category,'성적':grade}
        totals[category]+=credits
    totals['총학점']=sum(totals.values())
    totals['교양합계']=sum(totals[c] for c in ['기초교양','나사렛교양','핵심교양','소양교양'])
    totals['전공합계']=sum(totals[c] for c in ['전공필수','전공선택','전공심화'])
    # Advanced courses contribute to elective minima; no double counting in total.
    totals['전공선택']+=totals['전공심화']
    checks=[{'항목':key,'필요학점':value,'인정학점':totals[key],
             '부족학점':max(0,value-totals[key])} for key,value in profile['minimums'].items()]
    if advanced:
        if profile['optional_advanced'] is None:
            issues.append('이 연도의 전공심화 최소학점이 제공되지 않아 확인이 필요합니다.')
        else:
            value=profile['optional_advanced']
            checks.append({'항목':'선택한 전공심화','필요학점':value,'인정학점':totals['전공심화'],
                           '부족학점':max(0,value-totals['전공심화'])})
    missing=[name for name in mandatory if normalize(name) not in accepted]
    uncompleted=[c for key,c in catalog.items() if c['category']=='전공필수' and key not in accepted]
    status='입력 검토 필요' if issues else '입력 기준 미충족' if missing or any(c['부족학점'] for c in checks) else '입력한 학점·지정 과목 기준 충족 (공식 요건 확인 대기)'
    return {'status':status,'checks':checks,'missing_mandatory':missing,'uncompleted_catalog_required':uncompleted,
            'issues':issues,'excluded':excluded,'accepted':list(accepted.values()),'total':totals['총학점'],
            'pending':['과목코드·수강학기·대체과목의 공식 대응표가 없어 재수강 인정은 별도 확인 필요',
                       '학과의 의무 이수 과목 및 대체과목 인정 확인','복수전공·부전공·교직 등 개인별 적용 기준 확인',
                       '졸업시험·논문·인증·교양 필수과목 등 교육과정표 외 졸업요건 확인'],
            'assumptions':['전공심화 이수학점을 전공선택 최소학점에 포함합니다. 학과의 인정 방식이 다르면 이수구분을 수정하세요.'],
            'profile':{'year':profile['year'],'track':profile['track'],'page':profile['page']}}
