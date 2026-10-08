let csrf;
export async function getCsrf() {
  const response = await fetch('/api/csrf', { credentials: 'same-origin' });
  if (!response.ok) throw new Error('서버에 연결할 수 없습니다.');
  csrf = await response.json();
}
export function clearCsrf() {
  csrf = null;
}
// 세션 쿠키와 CSRF를 유지한다. 변경 요청은 실패해도 자동 재전송하지 않는다.
export async function request(url, method = 'GET', body) {
  const headers = {};
  if (method !== 'GET') {
    if (!csrf) await getCsrf();
    headers[csrf.headerName] = csrf.token;
  }
  if (body instanceof URLSearchParams)
    headers['Content-Type'] = 'application/x-www-form-urlencoded';
  else if (body) {
    headers['Content-Type'] = 'application/json';
    body = JSON.stringify(body);
  }
  const response = await fetch(url, { method, headers, body, credentials: 'same-origin' });
  const text = await response.text();
  let data;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = null;
  }
  if (!response.ok) {
    const error = new Error(
      data?.message ||
        (response.status === 401
          ? url === '/api/login'
            ? '학번 또는 비밀번호가 올바르지 않습니다.'
            : '로그인이 만료되었습니다. 다시 로그인해주세요.'
          : response.status === 403
            ? '세션이 갱신되었습니다. 다시 시도해주세요.'
            : '요청을 처리하지 못했습니다.'),
    );
    error.status = response.status;
    if (response.status === 403) {
      clearCsrf();
    }
    throw error;
  }
  return data;
}
