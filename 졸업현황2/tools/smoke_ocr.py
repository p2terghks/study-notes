"""Real model smoke test using a synthetic transcript without student data."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from graduation.ocr import recognize
from graduation.engine import parse_lines, parse_lines_with_review, audit

if __name__=='__main__':
    data=json.loads((ROOT/'data/curriculum.json').read_text())
    profile=next(p for p in data['profiles'] if p['id']=='2025-인공지능빅데이터')
    lines,_=recognize((ROOT/'data/sample-transcript.png').read_bytes())
    rows,rejected=parse_lines_with_review(lines,profile)
    print(json.dumps({'lines':lines,'rows':rows,'rejected':rejected},ensure_ascii=False,indent=2))
    expected={'컴퓨터프로그래밍1','JAVA','DB이론및실습','자료구조'}
    assert len(rows)+len(rejected)==4, '샘플의 4개 행이 후보 또는 검토 목록에 모두 남아야 합니다.'
    exact=sum(r['과목명'] in expected for r in rows)
    print(f'구조화한 후보 중 정확한 과목명: {exact}/4. 나머지 후보는 사용자 검토가 필요합니다.')
    corrected=parse_lines(['컴퓨터프로그래밍1 3 A+','JAVA 3 B0','DB이론및실습 3 P','자료구조 3 F'],profile)
    for row in corrected: row['확인']=True
    result=audit(corrected,profile)
    assert result['total']==9 and not result['issues'], '사용자 수정 후 학점 계산 오류'
    assert all(not r['확인'] for r in rows), '인식 결과는 사용자 확인을 요구해야 합니다.'
    print('실제 OCR 4행의 후보·미해석 보존 및 사용자 수정 후 9학점 계산 검증 완료')
