import { useState } from 'react';
export default function AuthPage({ login, demoEnabled, initialError }) {
  const [registering, setRegistering] = useState(false),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(initialError || '');
  function toggle() {
    setRegistering((v) => !v);
    setError('');
  }
  async function authenticate(studentNo, password, name) {
    setBusy(true);
    setError('');
    try {
      await login(studentNo, password, name);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  function submit(e) {
    e.preventDefault();
    const values = Object.fromEntries(new FormData(e.currentTarget));
    authenticate(values.studentNo, values.password, registering ? values.name : undefined);
  }
  return (
    <div id="auth" className="auth-page">
      <div className="auth-story">
        <a className="brand" href="/">
          <span className="brand-mark">c.</span> CAMPUS<span className="brand-dot">●</span>
        </a>
        <span className="eyebrow">YOUR NEXT CHAPTER</span>
        <h1>
          나의 가능성으로
          <br />
          채우는 한 학기.
        </h1>
        <p>
          배우고 싶은 수업을 찾고,
          <br />
          나만의 시간표를 완성하세요.
        </p>
        <div className="art-schedule" aria-hidden="true">
          <div className="art-head">
            MY WEEK <span>✦</span>
          </div>
          <div className="art-days">MON　 TUE　 WED　 THU　 FRI</div>
          <div className="art-grid">
            <i>새로운 배움</i>
            <i>한 걸음 더</i>
            <i>나의 가능성</i>
            <i>함께 성장</i>
          </div>
        </div>
        <small>2026 FALL SEMESTER · COURSE REGISTRATION</small>
      </div>
      <div className="auth-panel">
        <div className="auth-box">
          <span className="mini-label">CAMPUS PORTAL</span>
          <h2 id="auth-title">
            {registering ? '새로운 학기를 함께해요 ✦' : '다시 만나 반가워요 👋'}
          </h2>
          <p id="auth-subtitle">
            {registering
              ? '학번과 이름으로 나만의 캠퍼스 계정을 만드세요.'
              : '학번으로 로그인하고 나의 학기를 시작하세요.'}
          </p>
          <form id="auth-form" onSubmit={submit}>
            <label>
              학번
              <input
                name="studentNo"
                autoComplete="username"
                placeholder="학번 8~12자리"
                pattern="[0-9]{8,12}"
                required
              />
            </label>
            <label id="name-field" hidden={!registering}>
              이름
              <input
                name="name"
                autoComplete="name"
                placeholder="이름을 입력하세요"
                maxLength="30"
                required={registering}
              />
            </label>
            <label>
              비밀번호
              <input
                name="password"
                type="password"
                autoComplete={registering ? 'new-password' : 'current-password'}
                placeholder="비밀번호를 입력하세요"
                required
                maxLength="64"
                minLength={registering ? 8 : 1}
              />
            </label>
            <p id="auth-error" className="error-text" role="alert">
              {error}
            </p>
            <button className="primary auth-submit" type="submit" disabled={busy}>
              {registering ? '회원가입' : '로그인'} <span>→</span>
            </button>
          </form>
          <div className="auth-divider" hidden={!demoEnabled}>
            <span>또는</span>
          </div>
          <button
            id="demo-login"
            className="demo-button"
            hidden={!demoEnabled}
            onClick={() => authenticate('20260001', 'campus1234')}
            disabled={busy}
          >
            체험 계정으로 둘러보기 <span>↗</span>
          </button>
          <p className="auth-switch">
            처음 방문하셨나요?{' '}
            <button id="auth-toggle" className="text-button" onClick={toggle} disabled={busy}>
              {registering ? '로그인으로 돌아가기' : '회원가입'}
            </button>
          </p>
          <div className="demo-note" hidden={!demoEnabled}>
            체험 계정 <b>20260001</b> / <b>campus1234</b>
            <br />
            샘플 강의와 시간표가 준비되어 있어요.
          </div>
        </div>
      </div>
    </div>
  );
}
