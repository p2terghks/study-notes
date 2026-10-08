import { useEffect, useRef, useState } from 'react';
import { request } from '../../shared/api/api.js';
import './advisor.css';
const initialProfile = {
  university: '나사렛대학교',
  department: '인공지능학부',
  admissionYear: 2024,
  track: '',
};
const initialQuestions = [
  '졸업 학점 알려줘',
  '2학년 전공필수 알려줘',
  '3학년 교육과정 알려줘',
  '파란색 심화 후보 알려줘',
];
// 대화는 브라우저 메모리에만 보관한다. 새로고침 시 제거된다.
export default function Advisor({ onProfileSaved, onSessionExpired }) {
  const [open, setOpen] = useState(false),
    [profile, setProfile] = useState(initialProfile),
    [editing, setEditing] = useState(true),
    [messages, setMessages] = useState([]),
    [question, setQuestion] = useState(''),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(''),
    [topic, setTopic] = useState(null),
    [suggestions, setSuggestions] = useState(initialQuestions);
  const input = useRef(null),
    launcher = useRef(null),
    log = useRef(null),
    active = useRef(true),
    inFlight = useRef(false);
  useEffect(
    () => () => {
      active.current = false;
    },
    [],
  );
  useEffect(() => {
    if (open) input.current?.focus();
  }, [open]);
  useEffect(() => {
    if (log.current) log.current.scrollTop = log.current.scrollHeight;
  }, [messages, busy]);
  function fail(e) {
    if (!active.current) return;
    if (e.status === 401) onSessionExpired();
    else setError(e.message);
  }
  async function toggle() {
    if (open) {
      close();
      return;
    }
    setOpen(true);
    setError('');
    if (inFlight.current) return;
    inFlight.current = true;
    setBusy(true);
    try {
      const p = await request('/api/advisor/profile');
      if (!active.current) return;
      setProfile(p.university ? { ...p, track: p.track || '' } : initialProfile);
      setEditing(!p.university || !p.track);
    } catch (e) {
      fail(e);
    } finally {
      inFlight.current = false;
      if (active.current) setBusy(false);
    }
  }
  function close() {
    setOpen(false);
    launcher.current?.focus();
  }
  async function save(e) {
    e.preventDefault();
    if (inFlight.current) return;
    inFlight.current = true;
    setBusy(true);
    setError('');
    try {
      const p = await request('/api/advisor/profile', 'PUT', {
        ...profile,
        admissionYear: Number(profile.admissionYear),
        track: profile.track || null,
      });
      if (!active.current) return;
      setProfile({ ...p, track: p.track || '' });
      setEditing(false);
      setMessages([]);
      setTopic(null);
      setSuggestions(initialQuestions);
      await onProfileSaved();
    } catch (e) {
      fail(e);
    } finally {
      inFlight.current = false;
      if (active.current) setBusy(false);
    }
  }
  async function send(value) {
    const text = value.trim();
    if (!text || inFlight.current) return;
    inFlight.current = true;
    setBusy(true);
    setError('');
    setQuestion('');
    setMessages((m) => [...m, { role: 'user', message: text }]);
    try {
      const answer = await request('/api/advisor/chat', 'POST', {
        message: text,
        previousTopic: topic,
      });
      if (!active.current) return;
      setMessages((m) => [...m, { role: 'assistant', ...answer }]);
      setTopic(answer.topic);
      setSuggestions(answer.suggestions || initialQuestions);
    } catch (e) {
      fail(e);
      if (active.current) setQuestion(text);
    } finally {
      inFlight.current = false;
      if (active.current) {
        setBusy(false);
        input.current?.focus();
      }
    }
  }
  return (
    <>
      <button
        ref={launcher}
        className="advisor-launch"
        aria-expanded={open}
        aria-controls="advisor-panel"
        onClick={toggle}
      >
        ✦ 학사 도우미
      </button>
      {open && (
        <section
          id="advisor-panel"
          className="advisor-panel"
          role="dialog"
          aria-labelledby="advisor-title"
          onKeyDown={(e) => {
            if (e.key === 'Escape') {
              e.stopPropagation();
              close();
            }
          }}
        >
          <header>
            <div>
              <small>CAMPUS ADVISOR</small>
              <h2 id="advisor-title">나의 학사 도우미</h2>
            </div>
            <button aria-label="상담 닫기" onClick={close}>
              ×
            </button>
          </header>
          <p className="advisor-notice">
            나사렛대학교 2024학번 · 사용자 제공 자료
            <br />
            자료 조회와 규칙 기반 안내입니다. 공식 원문·성적표는 연결되지 않았습니다.
          </p>
          <details open={editing} onToggle={(e) => setEditing(e.currentTarget.open)}>
            <summary>학적 정보 · {profile.track || '트랙을 선택하세요'}</summary>
            <form className="advisor-profile" onSubmit={save}>
              <label>
                대학교
                <input
                  required
                  maxLength={100}
                  value={profile.university}
                  onChange={(e) => setProfile((p) => ({ ...p, university: e.target.value }))}
                />
              </label>
              <label>
                학과·학부
                <input
                  required
                  maxLength={50}
                  value={profile.department}
                  onChange={(e) => setProfile((p) => ({ ...p, department: e.target.value }))}
                />
              </label>
              <label>
                입학년도
                <input
                  type="number"
                  min={1980}
                  max={2100}
                  required
                  value={profile.admissionYear}
                  onChange={(e) => setProfile((p) => ({ ...p, admissionYear: e.target.value }))}
                />
              </label>
              <label>
                트랙
                <select
                  required
                  value={profile.track}
                  onChange={(e) => setProfile((p) => ({ ...p, track: e.target.value }))}
                >
                  <option value="">트랙 선택</option>
                  {['인공지능빅데이터', '정보통신보안', '스마트미디어'].map((t) => (
                    <option key={t}>{t}</option>
                  ))}
                </select>
              </label>
              <button disabled={busy}>학적 정보 저장</button>
              <small>
                본인 정보 확인 후 저장하세요. 정보는 이 독립 시제품의 현재 세션에만 저장됩니다.
              </small>
            </form>
          </details>
          <div
            className="advisor-messages"
            ref={log}
            role="log"
            aria-live="polite"
            aria-label="상담 내용"
          >
            {!messages.length && (
              <article className="advisor-bubble">
                <b>어떤 내용이 궁금한가요?</b>
                <p>
                  학적 정보를 저장하면 트랙별 과목과 졸업 학점을 안내할게요. 교육과정 탐색 후보를
                  안내하며 실시간 개설 강의·개인 시간표에는 연결되지 않습니다.
                </p>
              </article>
            )}
            {messages.map((m, i) => (
              <article key={i} className={`advisor-bubble ${m.role === 'user' ? 'from-user' : ''}`}>
                <b>{m.role === 'user' ? '나' : '학사 도우미'}</b>
                <p>{m.message}</p>
                {m.points?.length > 0 && (
                  <ul>
                    {m.points.map((p, j) => (
                      <li key={j}>{p}</li>
                    ))}
                  </ul>
                )}
                {m.sources?.map((s, j) => (
                  <small className="advisor-source" key={j}>
                    {s.url?.startsWith('https://') ? (
                      <a href={s.url} target="_blank" rel="noreferrer">
                        {s.title}
                      </a>
                    ) : (
                      s.title
                    )}
                    {s.checkedOn && ` · 확인일 ${s.checkedOn}`}
                  </small>
                ))}
              </article>
            ))}
            {busy && <p role="status">확인 중입니다…</p>}
          </div>
          <div className="advisor-suggestions">
            {suggestions.map((s) => (
              <button key={s} disabled={busy} onClick={() => send(s)}>
                {s}
              </button>
            ))}
          </div>
          {error && (
            <p className="advisor-error" role="alert">
              {error}
            </p>
          )}
          <form
            className="advisor-question"
            onSubmit={(e) => {
              e.preventDefault();
              send(question);
            }}
          >
            <label className="advisor-sr" htmlFor="advisor-question">
              학사 질문
            </label>
            <textarea
              ref={input}
              id="advisor-question"
              value={question}
              maxLength={1000}
              required
              placeholder="예: 스마트미디어 2학년 필수 과목"
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
                  e.preventDefault();
                  send(question);
                }
              }}
            />
            <button disabled={busy || !question.trim()}>보내기</button>
          </form>
          <footer>
            <span>현재 대화는 새로고침하면 지워집니다.</span>
            <button
              disabled={busy}
              onClick={() => {
                setMessages([]);
                setTopic(null);
                setError('');
                setSuggestions(initialQuestions);
              }}
            >
              대화 지우기
            </button>
          </footer>
        </section>
      )}
    </>
  );
}
