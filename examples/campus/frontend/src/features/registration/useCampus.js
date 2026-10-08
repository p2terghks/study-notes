import { useCallback, useEffect, useRef, useState } from 'react';
import { request, getCsrf, clearCsrf } from '../../shared/api/api.js';
export default function useCampus() {
  const [state, setState] = useState(null),
    [loading, setLoading] = useState(true),
    [demoEnabled, setDemoEnabled] = useState(false),
    [error, setError] = useState(''),
    [busy, setBusy] = useState(false),
    [notice, setNotice] = useState(null);
  const epoch = useRef(0),
    lock = useRef(false),
    pending = useRef(null),
    dialog = useRef(false);
  const notify = useCallback((message, error = false) => setNotice({ message, error }), []);
  const expire = useCallback(() => {
    epoch.current++;
    pending.current = null;
    setState(null);
    clearCsrf();
    dialog.current = false;
  }, []);
  const refresh = useCallback(async () => {
    if (pending.current) return pending.current;
    const generation = epoch.current;
    const task = request('/api/state')
      .then((value) => {
        if (epoch.current === generation) setState(value);
      })
      .catch((e) => {
        if (e.status === 401 && epoch.current === generation) expire();
        throw e;
      });
    pending.current = task;
    try {
      await task;
    } finally {
      if (pending.current === task) pending.current = null;
    }
  }, [expire]);
  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const config = await request('/api/config');
        if (!active) return;
        setDemoEnabled(config.demoEnabled);
        await getCsrf();
        if (active) await refresh();
      } catch (e) {
        if (active && e.status !== 401) setError(e.message);
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
      epoch.current++;
      pending.current = null;
    };
  }, [refresh]);
  useEffect(() => {
    if (!notice) return;
    const timer = setTimeout(() => setNotice(null), 4500);
    return () => clearTimeout(timer);
  }, [notice]);
  useEffect(() => {
    if (!state) return;
    const timer = setInterval(() => {
      if (!lock.current && !dialog.current && !document.hidden)
        refresh().catch((e) => notify(e.message, true));
    }, 20000);
    return () => clearInterval(timer);
  }, [!!state, refresh, notify]);
  async function login(studentNo, password, name) {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    try {
      epoch.current++;
      pending.current = null;
      if (name !== undefined) await request('/api/register', 'POST', { studentNo, password, name });
      await request('/api/login', 'POST', new URLSearchParams({ username: studentNo, password }));
      await getCsrf();
      await refresh();
      setError('');
      notify('반가워요! 이번 학기도 함께 준비해요.');
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }
  async function logout() {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    try {
      await request('/api/logout', 'POST');
      expire();
      setNotice(null);
      setError('');
    } catch (e) {
      if (e.status === 401) expire();
      notify(e.message, true);
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }
  async function mutate(action, id) {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    const config = {
      enroll: ['enrollments', 'POST', '수강신청 완료! 내 시간표에 등록했어요.'],
      cancel: ['enrollments', 'DELETE', '수강신청을 취소했어요.'],
      cart: ['cart', 'POST', '장바구니에 담았어요.'],
      removeCart: ['cart', 'DELETE', '장바구니에서 삭제했어요.'],
    }[action];
    let committed = false;
    try {
      // 진행 중인 조회를 먼저 끝내야 변경 전 응답이 최신 상태를 덮어쓰지 않는다.
      if (pending.current) await pending.current;
      await request(`/api/${config[0]}/${id}`, config[1]);
      committed = true;
      await refresh();
      notify(config[2]);
    } catch (e) {
      if (e.status === 401) expire();
      notify(
        committed ? '요청은 완료됐지만 화면을 갱신하지 못했어요. 새로고침해주세요.' : e.message,
        true,
      );
      if (!committed && e.status !== 401)
        try {
          await refresh();
        } catch {}
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }
  return {
    state,
    loading,
    demoEnabled,
    error,
    busy,
    notice,
    login,
    logout,
    mutate,
    refresh: () => {
      if (!lock.current) refresh().catch((e) => notify(e.message, true));
    },
    onDialogChange: (value) => {
      dialog.current = value;
    },
  };
}
