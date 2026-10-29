import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest

class AppTests(unittest.TestCase):
    def test_profiles_and_review_flow(self):
        at=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py'),default_timeout=30).run()
        self.assertFalse(at.exception)
        def button(label): return next(b for b in at.button if b.label==label)
        def checkbox(label): return next(c for c in at.checkbox if label in c.label)
        for year in [2022,2023,2024,2025]:
            at.selectbox[0].select(year).run()
            for track in ['인공지능빅데이터','정보통신보안','스마트미디어']:
                at.selectbox[1].select(track).run()
                self.assertFalse(at.exception)
        button('예시 이수 내역으로 체험').click().run()
        checkbox('원문과 비교').check().run()
        button('졸업요건 사전 점검').click().run()
        self.assertFalse(at.exception)
        self.assertTrue(any('입력 검토 필요' in x.value for x in at.info))
        at.radio[0].set_value('텍스트 입력').run()
        at.text_area[0].set_value('JAVA 3 A+').run()
        button('텍스트에서 과목 가져오기').click().run()
        self.assertFalse(at.exception)
        at.session_state['rows']=[{'과목명':'JAVA','학점':3.0,'이수구분':'전공필수','성적':'A+',
                                  '확인':True,'인식신뢰도':1.0,'메모':''}]
        at.session_state['version']+=1
        at.run()
        button('졸업요건 사전 점검').click().run()
        self.assertFalse(at.exception)
        self.assertTrue(any('입력 기준 미충족' in x.value for x in at.info))
        at.selectbox[0].select(2022).run()
        self.assertNotIn('result',at.session_state)
