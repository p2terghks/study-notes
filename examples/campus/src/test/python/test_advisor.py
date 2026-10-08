import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('advisor', Path(__file__).parents[2] / 'main/resources/python/advisor.py')
advisor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(advisor)


class AdvisorTest(unittest.TestCase):
    def setUp(self):
        def course(id, day=0, start=600, end=660, **changes):
            value = dict(id=id, code=f'CS{id}', name=f'강의{id}', department='컴퓨터공학과',
                         category='전공필수', credits=3, capacity=10, enrolled=0,
                         meetings=[dict(day=day, start=start, end=end)])
            return dict(value, **changes)
        self.payload = dict(message='추천', previousTopic=None, policy=None,
                            profile=dict(name='학생', university=None, department='컴퓨터공학과', admissionYear=None),
                            state=dict(student=dict(department='컴퓨터공학과', maxCredits=18),
                                       enrolledIds=[1], cartIds=[], courses=[course(1), course(2),
                                       course(3, start=660, end=720), course(4, day=4),
                                       course(5, day=1, enrolled=10)]))

    def test_recommendation_excludes_enrolled_conflicts_full_and_requested_day(self):
        self.payload['message'] = '금요일 공강으로 추천해줘'
        result = advisor.reply(self.payload)
        self.assertEqual([r['course']['id'] for r in result['recommendations']], [3])

    def test_credit_limit(self):
        self.payload['state']['student']['maxCredits'] = 3
        self.assertEqual(advisor.reply(self.payload)['recommendations'], [])

    def test_followup_and_graduation_priority(self):
        self.payload.update(message='더 알려줘', previousTopic='timetable')
        self.assertEqual(advisor.reply(self.payload)['message'], '현재 1과목, 3학점을 신청했어요.')
        self.payload['message'] = '졸업 수업 추천'
        result = advisor.reply(self.payload)
        self.assertEqual(result['topic'], 'graduation')
        self.assertIn('입학년도', result['message'])

    def test_registered_policy(self):
        self.payload['profile'].update(university='테스트대학교', admissionYear=2024)
        self.payload.update(message='졸업요건', policy=dict(university='테스트대학교', department='컴퓨터공학과',
                            admissionYear=2024, title='공식 요건', sourceUrl='https://example.edu/rules',
                            verifiedOn='2026-01-01', requirements=['130학점']))
        result = advisor.reply(self.payload)
        self.assertEqual(result['points'][0], '130학점')
        self.assertEqual(result['sources'][0]['checkedOn'], '2026-01-01')


if __name__ == '__main__':
    unittest.main()
