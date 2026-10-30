import hashlib
import io
import json
from pathlib import Path
import pandas as pd
import streamlit as st
from graduation.engine import CATEGORIES, audit, parse_lines, parse_lines_with_review
from graduation.ocr import recognize

ROOT=Path(__file__).resolve().parent
DATA=json.loads((ROOT/'data/curriculum.json').read_text(encoding='utf-8'))
COLUMNS=['과목명','학점','이수구분','성적','확인','인식신뢰도','메모']
st.set_page_config(page_title='졸업 체크 · 사진으로 확인하는 이수 현황',page_icon='🎓',layout='wide')
st.markdown('''<style>.block-container{max-width:1200px;padding-top:2rem}h1{letter-spacing:-1.5px}
[data-testid="stMetric"]{background:white;border:1px solid #e2e8f0;border-radius:14px;padding:18px}
.stButton>button{border-radius:10px}footer{visibility:hidden}</style>''',unsafe_allow_html=True)
st.caption('GRADUATION CHECK / PYTORCH OCR')
st.title('사진 한 장으로, 졸업까지 남은 길')
st.write('성적표를 읽고 · 이수 내역을 검토하고 · 나에게 적용되는 학점 기준과 비교하세요.')
with st.sidebar:
    st.subheader('나의 교육과정')
    year=st.selectbox('입학연도',[2022,2023,2024,2025],index=3)
    track=st.selectbox('전공 트랙',['인공지능빅데이터','정보통신보안','스마트미디어'])
    profile=next(p for p in DATA['profiles'] if p['year']==year and p['track']==track)
    st.caption(f'근거: 첨부 교육과정표 {profile["page"]}쪽 · {profile["extraction"]}')
    advanced=st.checkbox('전공심화 21학점도 별도로 확인',disabled=year==2022)
    st.info('결과는 졸업 상담을 위한 사전 점검입니다. 학과의 최종 졸업 사정이 필요합니다.')
    st.caption('사진과 성적표는 서버 파일에 저장하지 않습니다. 앱은 이 컴퓨터에서만 접속하도록 설정했습니다.')
    st.download_button('교육과정 원문 PDF',(ROOT/'reference'/DATA['source']).read_bytes(),file_name=DATA['source'])
context=profile['id']
if st.session_state.get('context')!=context:
    st.session_state['context']=context
    st.session_state['rows']=[]
    st.session_state['version']=st.session_state.get('version',0)+1
    st.session_state.pop('result',None)
    st.session_state['unparsed']=[]
    st.session_state.pop('ocr_lines',None)

def replace(rows, unparsed=None):
    st.session_state['rows']=rows
    st.session_state['unparsed']=unparsed or []
    st.session_state.pop('ocr_lines',None)
    st.session_state['version']+=1
    st.session_state.pop('result',None)

input_tab, rules_tab=st.tabs(['성적표 분석','교육과정과 판정 기준'])
with rules_tab:
    st.subheader(f'{year}학년도 {track}')
    st.dataframe(pd.DataFrame([{'항목':k,'최소학점':v} for k,v in profile['minimums'].items()]),hide_index=True,width='stretch')
    for warning in profile['warnings']: st.warning(warning)
    st.write('전공심화는 전공선택에 포함해 계산하며, 총학점에는 한 번만 더합니다. 실제 인정 방식은 학과 확인이 필요합니다.')
    st.dataframe(pd.DataFrame(profile['courses']).rename(columns={'name':'과목명','credits':'학점','category':'이수구분','level':'학년','semester':'학기','page':'원문쪽'}),hide_index=True,width='stretch')
    st.caption('2022는 이미지 원문을 전사했습니다. 2023~2025는 PDF 표를 추출했습니다. 원문의 빈 과목명은 자동 목록에서 제외했습니다. 과목명이 비슷한 경우 자동으로 대체 인정하지 않습니다.')
with input_tab:
    st.subheader('01  성적표 불러오기')
    mode=st.radio('입력 방식',['사진 업로드','텍스트 입력','CSV 가져오기'],horizontal=True)
    if mode=='사진 업로드':
        photos=st.file_uploader('성적표 사진 (JPG · PNG · WEBP, 파일당 최대 15MB)',type=['jpg','jpeg','png','webp'],accept_multiple_files=True)
        if photos:
            st.image(photos[0],width=400)
            if st.button('사진에서 이수 내역 읽기',type='primary'):
                rows=[]; raw=[]; unparsed=[]
                try:
                    with st.spinner('한국어 문자 인식 중입니다. 최초 실행은 모델을 내려받아 시간이 걸릴 수 있습니다.'):
                        for photo in photos:
                            lines,_=recognize(photo.getvalue())
                            raw.extend(lines)
                            candidates, rejected = parse_lines_with_review(lines,profile)
                            rows.extend(candidates); unparsed.extend(rejected)
                    replace(rows, unparsed); st.session_state['ocr_lines']=raw
                    st.success(f'{len(rows)}개 과목 후보를 찾았습니다. 아래 표를 원문과 비교해 수정하세요.')
                    if not rows: st.warning('과목 행을 찾지 못했습니다. 인식한 원문을 텍스트 입력으로 정리하거나 표에 직접 입력하세요.')
                except Exception as exc:
                    st.error(f'사진 인식을 완료하지 못했습니다: {exc}')
                    st.info('네트워크 연결과 모델 준비 상태를 확인하세요. 텍스트와 CSV 입력은 모델 없이 사용할 수 있습니다.')
        if st.session_state.get('ocr_lines'):
            with st.expander('인식한 원문 보기'):
                st.text('\n'.join(line['text'] for line in st.session_state['ocr_lines']))
    elif mode=='텍스트 입력':
        text=st.text_area('한 줄에 과목명 학점 성적 순서로 입력',placeholder='컴퓨터프로그래밍1 3 A+\nJAVA 3 B0\nDB이론및실습 3 P',height=160)
        if st.button('텍스트에서 과목 가져오기'):
            rows, unparsed=parse_lines_with_review(text.splitlines(),profile); replace(rows, unparsed)
            st.info(f'{len(rows)}행을 가져왔습니다. 인식되지 않은 줄은 아래 표에서 직접 추가하세요.')
    else:
        st.download_button('CSV 양식 받기','과목명,학점,이수구분,성적\n컴퓨터프로그래밍1,3,전공필수,A+\n'.encode('utf-8-sig'),file_name='transcript-template.csv',mime='text/csv')
        upload=st.file_uploader('과목명·학점·이수구분·성적 열이 있는 CSV',type='csv')
        if upload and st.button('CSV 불러오기'):
            try:
                frame=pd.read_csv(upload).fillna('')
                if not {'과목명','학점','이수구분','성적'}.issubset(frame.columns): raise ValueError('필수 열이 없습니다.')
                rows=[]
                for row in frame.to_dict('records'):
                    row.update({'확인':False,'인식신뢰도':1.0,'메모':'CSV 입력'}); rows.append(row)
                replace(rows)
            except Exception as exc: st.error(f'CSV를 읽을 수 없습니다: {exc}')
    if st.button('예시 이수 내역으로 체험'):
        replace(parse_lines(['컴퓨터프로그래밍1 3 A+','컴퓨터프로그래밍2 3 A0','JAVA 3 B+','DB이론및실습 3 P','자료구조 3 B0','운영체제 3 F'],profile))
    st.subheader('02  인식 결과 검토')
    unparsed = st.session_state.get('unparsed', [])
    unresolved_ok = True
    if unparsed:
        st.warning(f'{len(unparsed)}개 행을 해석하지 못했습니다. 누락 과목은 아래 표에 직접 추가하세요.')
        st.dataframe(pd.DataFrame(unparsed).rename(columns={'text':'원문','reason':'검토 사유'}),hide_index=True)
        unresolved_ok = st.checkbox('미해석 행을 확인하고 필요한 과목을 표에 추가했습니다.',key=f'unparsed-{context}-{st.session_state["version"]}')
    st.caption('이수구분·학점·성적을 확인하고 각 행의 확인 칸을 선택하세요. F·미이수·수강중은 취득학점에서 제외됩니다. 표 하단에서 과목을 추가할 수 있습니다.')
    frame=pd.DataFrame(st.session_state['rows'],columns=COLUMNS)
    frame['학점']=pd.to_numeric(frame['학점'],errors='coerce')
    frame['확인']=frame['확인'].fillna(False).astype(bool)
    edited=st.data_editor(frame,hide_index=True,num_rows='dynamic',width='stretch',
        key=f'editor-{context}-{st.session_state["version"]}',
        column_config={'이수구분':st.column_config.SelectboxColumn(options=CATEGORIES,required=True),
                       '학점':st.column_config.NumberColumn(min_value=0.0,max_value=30.0,step=0.5),
                       '확인':st.column_config.CheckboxColumn(default=False),
                       '인식신뢰도':st.column_config.NumberColumn(format='%.2f')},
        disabled=['인식신뢰도'])
    st.download_button('검토 중인 내역 CSV 저장',edited.to_csv(index=False).encode('utf-8-sig'),file_name='reviewed-transcript.csv',mime='text/csv')
    mandatory=st.multiselect('학과에서 의무 이수로 확인받은 과목 (선택)',[c['name'] for c in profile['courses'] if c['category']=='전공필수'],
        key=f'mandatory-{context}',help='원문의 필수 목록 전체를 의무로 단정하지 않습니다. 학과 확인 후 선택하세요.')
    consent=st.checkbox('원문과 비교하여 과목 누락, 이수구분, 재수강·대체과목 인정 여부를 확인했습니다.',key=f'consent-{context}')
    payload=edited.fillna('').to_dict('records')
    signature=hashlib.sha256(json.dumps([payload,context,mandatory,advanced,consent,unresolved_ok],ensure_ascii=False,default=str).encode()).hexdigest()
    if st.button('졸업요건 사전 점검',type='primary',disabled=not consent or not unresolved_ok or edited.empty):
        st.session_state['result']=(signature,audit(payload,profile,mandatory,advanced))
    stored=st.session_state.get('result')
    if stored and stored[0]!=signature: st.info('입력이나 기준이 변경되었습니다. 사전 점검을 다시 실행하세요.')
    if stored and stored[0]==signature:
        result=stored[1]
        st.subheader('03  나의 점검 결과')
        st.info(result['status'])
        cols=st.columns(3)
        cols[0].metric('인정한 취득학점',f'{result["total"]:g} / {profile["minimums"]["총학점"]:g}')
        cols[1].metric('총학점 부족',f'{max(0,profile["minimums"]["총학점"]-result["total"]):g}학점')
        cols[2].metric('검토할 입력',f'{len(result["issues"])}개')
        st.dataframe(pd.DataFrame(result['checks']),hide_index=True,width='stretch')
        for issue in result['issues']: st.warning(issue)
        if result['missing_mandatory']: st.error('지정한 의무 과목 중 미이수: '+', '.join(result['missing_mandatory']))
        with st.expander('아직 이수하지 않은 교육과정의 전공필수 과목 (의무 여부 별도 확인)'):
            st.dataframe(pd.DataFrame(result['uncompleted_catalog_required']),hide_index=True)
        if result['excluded']:
            with st.expander('제외·중복 처리 내역'): st.write('\n\n'.join(result['excluded']))
        st.warning('공식 졸업요건 확인 대기: 학점 충족과 별개로 아래 항목은 아직 자동 판정하지 못합니다.')
        for pending in result['pending']: st.write('• '+pending)
        st.download_button('점검 보고서 JSON 저장',json.dumps(result,ensure_ascii=False,indent=2),file_name='graduation-check.json',mime='application/json')
