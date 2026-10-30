import copy
import json
import unittest
from pathlib import Path
from graduation.engine import audit, parse_lines, parse_lines_with_review

DATA=json.loads((Path(__file__).resolve().parents[1]/'data/curriculum.json').read_text())
P=next(p for p in DATA['profiles'] if p['id']=='2025-인공지능빅데이터')
def row(name='JAVA',credits=3,category='전공필수',grade='A+',confirmed=True):
    return {'과목명':name,'학점':credits,'이수구분':category,'성적':grade,'확인':confirmed}

class AuditTests(unittest.TestCase):
    def test_all_requested_cohorts(self):
        self.assertEqual(len(DATA['profiles']),12)
        for p in DATA['profiles']:
            self.assertIn(p['year'],range(2022,2026))
            self.assertEqual(p['minimums']['총학점'],127)
            self.assertIn('JAVA',[c['name'] for c in p['courses']])
            self.assertEqual(len({c['name'] for c in p['courses']}),len(p['courses']))
    def test_year_specific_thresholds(self):
        for p in DATA['profiles']:
            self.assertEqual(p['minimums']['교양합계'],36 if p['year']<2024 else 34)
            self.assertEqual(p['minimums']['전공합계'],75 if p['year']==2022 else 36)
    def test_failed_pending_unknown_not_counted(self):
        r=audit([row(grade='F'),row('B',grade='수강중'),row('C',grade=''),row('D',confirmed=False)],P)
        self.assertEqual(r['total'],0)
        self.assertEqual(len(r['issues']),2)
    def test_duplicates_and_retake(self):
        r=audit([row(grade='F'),row(),row(name=' java ')],P)
        self.assertEqual(r['total'],3)
    def test_conflicting_duplicates_block(self):
        r=audit([row(),row(credits=4)],P)
        self.assertEqual(r['status'],'입력 검토 필요')
    def test_invalid_numbers(self):
        for credit in [float('nan'),float('inf'),-1,0,'oops']:
            self.assertEqual(audit([row(credits=credit)],P)['total'],0)
    def test_advanced_not_double_counted(self):
        r=audit([row('자료구조',category='전공심화')],P,advanced=True)
        self.assertEqual(r['total'],3)
        checks={c['항목']:c for c in r['checks']}
        self.assertEqual(checks['전공선택']['인정학점'],3)
        self.assertEqual(checks['전공합계']['인정학점'],3)
    def test_mandatory_and_catalog_are_separate(self):
        r=audit([row()],P,mandatory=['컴퓨터프로그래밍1'])
        self.assertEqual(r['missing_mandatory'],['컴퓨터프로그래밍1'])
    def test_passed_minima_not_final_graduation(self):
        p=copy.deepcopy(P); p['minimums']={'총학점':3}
        r=audit([row()],p)
        self.assertEqual(r['status'],'입력한 학점·지정 과목 기준 충족 (공식 요건 확인 대기)')
        self.assertTrue(r['pending'])
    def test_parse_preserves_course_number_and_never_confirms(self):
        rows=parse_lines(['컴퓨터프로그래밍1 3 A+','총학점 127','JAVA 3','자료구조 3 F'],P)
        self.assertEqual(len(rows),3)
        self.assertEqual(rows[0]['과목명'],'컴퓨터프로그래밍1')
        self.assertFalse(rows[0]['확인'])
        self.assertEqual(rows[1]['성적'],'')
    def test_close_match_is_only_suggestion(self):
        r=parse_lines(['컴퓨터프로그래밍I 3 A+'],P)[0]
        self.assertEqual(r['이수구분'],'미분류')
        self.assertIn('후보',r['메모'])
    def test_no_implicit_old_course_alias(self):
        r=parse_lines(['C언어응용 3 A+'],P)[0]
        self.assertEqual(r['과목명'],'C언어응용')
        self.assertEqual(r['이수구분'],'미분류')

class ReviewRegressionTests(unittest.TestCase):
    def test_catalog_mismatch_is_not_counted(self):
        for bad in [row(credits=30), row(category='기초교양')]:
            result = audit([bad], P)
            self.assertEqual(result['total'], 0)
            self.assertTrue(result['issues'])

    def test_unknown_major_needs_official_mapping(self):
        result = audit([row(name='JAVA대체과목')], P)
        self.assertEqual(result['total'], 0)
        self.assertIn('대체', result['issues'][0])

    def test_unknown_general_course_can_be_reviewed(self):
        self.assertEqual(audit([row(name='교양 과목', category='기초교양')], P)['total'], 3)

    def test_korean_completed_grade(self):
        rows, rejected = parse_lines_with_review(['JAVA 3 이수완료'], P)
        self.assertFalse(rejected)
        self.assertEqual(rows[0]['성적'], '이수완료')

    def test_grade_points_not_mistaken_for_credits(self):
        rows, rejected = parse_lines_with_review(['JAVA 3 A+ 4.5'], P)
        self.assertFalse(rejected)
        self.assertEqual((rows[0]['과목명'], rows[0]['학점'], rows[0]['성적']), ('JAVA', 3, 'A+'))

    def test_merged_courses_and_bad_grade_are_preserved(self):
        lines = ['JAVA 3 A+ 자료구조 3 B0', 'JAVA 3 BO', '이름만 있는 행']
        rows, rejected = parse_lines_with_review(lines, P)
        self.assertFalse(rows)
        self.assertEqual([r['text'] for r in rejected], lines)

    def test_missing_grade_not_confused_with_gpa(self):
        rows, rejected = parse_lines_with_review(['JAVA 3 4.5'], P)
        self.assertFalse(rows)
        self.assertEqual(len(rejected), 1)

if __name__=='__main__': unittest.main()
