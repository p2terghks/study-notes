import AuthPage from './features/auth/AuthPage.jsx';
import Dashboard from './features/dashboard/Dashboard.jsx';
import useCampus from './features/registration/useCampus.js';
export default function App() {
  const campus = useCampus();
  if (campus.loading)
    return (
      <div className="auth-page" role="status">
        캠퍼스를 불러오는 중입니다…
      </div>
    );
  return (
    <>
      {campus.state ? (
        <Dashboard key={campus.state.student.id} {...campus} />
      ) : (
        <AuthPage
          login={campus.login}
          demoEnabled={campus.demoEnabled}
          initialError={campus.error}
        />
      )}
      <div
        id="toast"
        role="status"
        aria-live="polite"
        hidden={!campus.notice}
        className={campus.notice?.error ? 'error' : ''}
      >
        {campus.notice?.message}
      </div>
    </>
  );
}
