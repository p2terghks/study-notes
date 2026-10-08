import { createRoot } from 'react-dom/client';
import Advisor from './features/advisor/Advisor.jsx';
import './styles.css';
createRoot(document.getElementById('root')).render(
  <main>
    <small>NAZARENE · ACADEMIC ADVISOR</small>
    <h1>
      나의 졸업까지,
      <br />한 과목씩 알아보기.
    </h1>
    <p>2024학번 · 인공지능빅데이터 / 정보통신보안 / 스마트미디어</p>
    <section>
      <h2>수강신청 사이트와 분리된 학사 도우미</h2>
      <p>오른쪽 아래 ‘학사 도우미’를 열고 본인 트랙을 저장하세요.</p>
      <ul>
        <li>총 졸업 학점과 교양·전공 기준 안내</li>
        <li>학년·학기·트랙별 교육과정 조회</li>
        <li>파란색 과목 중 전공심화 21학점 선택 후보 안내</li>
      </ul>
      <p>
        사용자 제공 설명·사진 기반의 규칙형 시제품입니다. 성적표나 실시간 수강신청 DB에 접근하지
        않습니다.
      </p>
    </section>
    <Advisor onProfileSaved={async () => {}} onSessionExpired={() => location.reload()} />
  </main>,
);
