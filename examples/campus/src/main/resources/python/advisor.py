"""학사 상담 엔진. 표준 입력 JSON → 표준 출력 JSON (Python 3.10+)."""
import json
import re
import sys

DAYS = '월화수목금'
SUGGESTIONS = ['졸업요건 알려줘', '수업 추천해줘', '내 시간표 알려줘']


def answer(topic, message, points=(), recommendations=(), sources=(), suggestions=SUGGESTIONS):
    return dict(topic=topic, message=message, points=list(points),
                recommendations=list(recommendations), sources=list(sources), suggestions=list(suggestions))


def reply(payload):
    state, profile = payload['state'], payload['profile']
    query = re.sub(r'\s+', '', payload['message'].lower())
    student = state['student']
    enrolled = [c for c in state['courses'] if c['id'] in state['enrolledIds']]
    credits = sum(c['credits'] for c in enrolled)
    has = lambda *words: any(word in query for word in words)

    def unavailable(course):
        if course['id'] in state['enrolledIds']:
            return '이미 신청한 강의예요.'
        if course['enrolled'] >= course['capacity']:
            return '현재 정원이 마감됐어요.'
        if credits + course['credits'] > student['maxCredits']:
            return '현재 남은 신청 학점을 초과해요.'
        if any(a['day'] == b['day'] and a['start'] < b['end'] and b['start'] < a['end']
               for c in enrolled for a in c['meetings'] for b in course['meetings']):
            return '이미 신청한 강의와 시간이 겹쳐요.'
        return None

    def meeting_text(course):
        def clock(minutes):
            return f'{minutes // 60:02d}:{minutes % 60:02d}'
        return ', '.join(f"{DAYS[m['day']]} {clock(m['start'])}–{clock(m['end'])}" for m in course['meetings'])

    def welcome():
        return answer('welcome', f"{profile['name']}님, 안녕하세요. {profile['department']} 학기 준비를 함께할게요.",
                      ['시간표·잔여 정원·학점을 확인해 수업을 추천해요.',
                       '졸업요건은 대학·학과·입학년도에 맞춰 등록된 공식 자료만 안내해요.',
                       '이수 성적표가 연결되지 않아 졸업 가능 여부나 남은 졸업 학점은 계산하지 않아요.'])

    def graduation():
        if profile.get('university') is None or profile.get('admissionYear') is None:
            return answer('graduation', '대학과 입학년도를 먼저 알려주세요. 상단의 ‘학적 정보’에서 저장할 수 있어요.',
                          [f"현재 학과: {profile['department']}", '학번 숫자만으로 입학년도를 추정하지 않아요.',
                           '본인에게 적용되는 대학·학과·입학년도가 모두 일치하는 자료만 안내해요.'])
        policy = payload.get('policy')
        if not policy:
            return answer('graduation', f"{profile['university']} · {profile['department']} · {profile['admissionYear']}학번의 공식 졸업요건이 아직 등록되지 않았어요.",
                          ['학과 홈페이지의 졸업요건·교육과정표를 운영자에게 전달하면 연결할 수 있어요.',
                           '총 이수학점, 전공필수, 교양 영역, 졸업논문·인증 여부를 공식 문서에서 확인하세요.',
                           '현재 신청 학점은 이수 완료 학점이 아니므로 졸업 잔여 학점으로 계산하지 않아요.'])
        return answer('graduation', f"{policy['university']} {policy['department']} {policy['admissionYear']}학번 기준으로 등록된 졸업요건이에요.",
                      policy['requirements'] + [f"공식 자료 확인일: {policy['verifiedOn']}. 이후 개정·개인별 예외 적용은 학과에 확인하세요.",
                                                '현재 앱에는 누적 이수 성적표가 없으므로 개인의 졸업 충족 여부는 판정하지 않아요.'],
                      sources=[dict(title=policy['title'], url=policy['sourceUrl'], checkedOn=policy['verifiedOn'])])

    def timetable():
        return answer('timetable', f'현재 {len(enrolled)}과목, {credits}학점을 신청했어요.',
                      [f"{c['name']} · {c['credits']}학점 · {meeting_text(c)}" for c in enrolled] +
                      [f"이번 학기 추가 신청 가능 학점: {student['maxCredits'] - credits}학점",
                       '이 수치는 현재 수강신청 기준이며 누적 이수학점이나 졸업 잔여 학점이 아니에요.'])

    def recommend(text):
        general = '교양' in text
        major = not general and '전공' in text
        interest = next((w for w in ['인공지능', '데이터', '웹', '네트워크', '디자인', '심리', '수학', '경영', '운영체제', '자료구조', '글쓰기', '프로젝트'] if w in text), '')
        excluded = [d for d in DAYS if re.search(d + r'(?:요일)?(?:은|는|에는)?(?:공강|빼|제외|피하|쉬)', text)]
        candidates = [c for c in state['courses'] if unavailable(c) is None
                      and (c['category'].startswith('교양') if general else
                           c['department'] == student['department'] or (not major and c['category'].startswith('교양')))
                      and (not interest or interest in c['name'] or interest in c['department'])
                      and not any(DAYS[m['day']] in excluded for m in c['meetings'])]
        candidates.sort(key=lambda c: (0 if c['department'] == student['department'] and c['category'] == '전공필수'
                                       else 1 if c['department'] == student['department'] else 2, c['code']))
        recommendations = [dict(course=c, reason=(f"내 학과 {c['category']}" if c['department'] == student['department'] else c['category']) +
                                f" · 현재 시간표와 겹치지 않음 · 잔여 {c['capacity'] - c['enrolled']}자리") for c in candidates[:3]]
        points = [f"기준: {student['department']} · 현재 {credits}/{student['maxCredits']}학점"]
        if excluded:
            points.append('공강 요청 반영: ' + ', '.join(excluded) + '요일 제외')
        if interest:
            points.append('관심 분야: ' + interest)
        points += ['각 강의는 현재 시간표 기준의 개별 후보예요. 후보끼리 시간이 겹치거나 함께 신청하면 학점이 초과될 수 있어요.',
                   '과거 이수·선수과목·실제 졸업 인정 여부는 확인되지 않았어요. 정원은 신청 시 다시 검사해요.']
        return answer('recommend', '현재 시간표에 맞는 강의를 최대 3개 골랐어요.' if recommendations else
                      '현재 조건에서 바로 신청할 수 있는 추천 강의를 찾지 못했어요.', points, recommendations,
                      [dict(title='현재 개설 강의·개인 신청 내역', url=None, checkedOn=None)],
                      ['전공 수업 추천해줘', '교양 수업 추천해줘', '금요일 공강으로 추천해줘'])

    if has('졸업', '이수요건', '졸논', '논문', '인증', '토익', '졸업학점'):
        return graduation()
    if has('취소', '철회', '삭제'):
        return answer('cancel', '수강 취소는 신청 내역에서 할 수 있어요.',
                      ['내 시간표 또는 신청 내역에서 취소 → 확인을 누르세요.', '취소된 강의는 시간표에서 삭제되고 정원이 반환돼요.',
                       '채팅에서는 신청·취소를 자동 실행하지 않아요.'], suggestions=['내 시간표 알려줘'])
    if has('장바구니', '찜'):
        return answer('cart', f"장바구니에 {len(state['cartIds'])}과목이 담겨 있어요.",
                      ['장바구니는 관심 강의 목록이며 자리를 예약하지 않아요.', '강의 목록의 가방 아이콘으로 담거나 뺄 수 있어요.',
                       '수강신청이 성공하면 해당 강의는 장바구니에서 빠져요.'], suggestions=['수업 추천해줘'])
    if has('추천', '들을만', '뭐들', '공강', '수업찾', '강의찾'):
        return recommend(query)
    for c in state['courses']:
        if c['code'].lower() in query or re.sub(r'\s+', '', c['name'].lower()) in query:
            return answer('course', f"{c['name']} ({c['code']}) 안내예요.",
                          [f"{c['professor']} 교수 · {c['department']} · {c['category']} · {c['credits']}학점",
                           f"{meeting_text(c)} · {c['room']}", f"신청 {c['enrolled']}/{c['capacity']}명",
                           unavailable(c) or '현재 시간표와 학점 기준으로 신청 가능한 후보예요. 선수과목·과거 이수는 별도 확인이 필요해요.'],
                          [dict(course=c, reason='강의 목록에서 자세히 확인할 수 있어요.')],
                          [dict(title='현재 개설 강의·개인 신청 내역', url=None, checkedOn=None)])
    if has('시간표', '내수업', '내강의', '신청내역', '몇학점', '남은학점', '현재학점'):
        return timetable()
    if has('충돌', '겹', '중복', '정원', '동시', '마감', '최대', '18학점', '신청방법', '수강신청', '학점제한'):
        return answer('rules', '이 사이트의 수강신청 기준을 알려드릴게요.',
                      [f"학기당 최대 {student['maxCredits']}학점까지 신청할 수 있어요.",
                       '같은 요일에 시간이 겹치는 수업과 이미 신청한 강의는 중복 신청할 수 없어요.',
                       '마감된 강의는 신청할 수 없어요. 여러 사람이 동시에 신청해도 서버가 정원을 다시 검사해요.',
                       '강의 행에 커서를 올리면 미리보기, 신청 버튼을 누르면 서버 확인 후 시간표에 반영돼요.'])
    if has('다시', '자세히', '더알려', '그거') and payload.get('previousTopic'):
        return {'graduation': graduation, 'recommend': lambda: recommend('추천'), 'timetable': timetable}.get(payload['previousTopic'], welcome)()
    if has('안녕', '도움', '뭘', '시작', '반가'):
        return welcome()
    return answer('help', '현재 확인할 수 있는 학사 데이터 안에서 답변해요. 이 질문은 아직 정확히 답할 자료가 없어요.',
                  ['졸업요건, 시간표, 수업 추천, 강의명·학수번호, 수강신청 방법을 물어보세요.',
                   '등록금·장학금·휴복학·학교별 학사 일정은 공식 공지나 학과 사무실의 확인이 필요해요.'])


if __name__ == '__main__':
    json.dump(reply(json.load(sys.stdin)), sys.stdout, ensure_ascii=False)
