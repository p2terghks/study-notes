import { useState } from 'react';
import { flushSync } from 'react-dom';
import Icon from '../../shared/ui/Icon.jsx';
import CourseRows from '../courses/CourseRows.jsx';
import Schedule from '../timetable/Schedule.jsx';
import Modal from '../../shared/ui/Modal.jsx';
import { credits, filterCourses } from '../courses/courses.js';
const defaults = { search: '', department: '', category: '', available: false };
export default function Dashboard({ state, busy, logout, refresh, mutate, onDialogChange }) {
  const [tab, setTab] = useState('all'),
    [filters, setFilters] = useState(defaults),
    [previewId, setPreviewId] = useState(null),
    [pending, setPending] = useState(null),
    [help, setHelp] = useState(false);
  const total = credits(state),
    visible = filterCourses(state, tab, filters);
  const title = { all: '수강신청', cart: '장바구니', enrolled: '내 시간표' }[tab],
    subtitle = {
      all: '새로운 배움, 나만의 한 학기를 설계해 보세요.',
      cart: '관심 있는 강의를 모아두고, 내 시간표에 담아보세요.',
      enrolled: '이번 학기 나의 배움을 한눈에 확인하세요.',
    }[tab],
    catalogTitle = { all: '개설 강의', cart: '담아둔 강의', enrolled: '신청한 강의' }[tab];
  function changeTab(value) {
    setTab(value);
    setPreviewId(null);
  }
  function updateFilter(key, value) {
    setFilters((f) => ({ ...f, [key]: value }));
    setPreviewId(null);
  }
  function resetFilters() {
    setFilters(defaults);
    setPreviewId(null);
  }
  function print() {
    flushSync(() => setPreviewId(null));
    window.print();
  }
  function closeCancel() {
    setPending(null);
    onDialogChange(false);
  }
  function onAction(action, course) {
    if (busy) return;
    if (action === 'cancel') {
      setPending(course);
      onDialogChange(true);
    } else {
      setPreviewId(null);
      mutate(action, course.id);
    }
  }
  return (
    <>
      <div id="app">
        <aside className="sidebar">
          <a className="brand" href="/">
            <span className="brand-mark">c.</span> CAMPUS<span className="brand-dot">●</span>
          </a>
          <div className="semester-tag">
            <span className="tiny-dot"></span> 2026학년도 2학기
          </div>
          <div className="nav-label">MY CAMPUS</div>
          <nav aria-label="주 메뉴">
            <button
              data-tab="all"
              className={`nav-item ${tab === 'all' ? 'active' : ''}`}
              onClick={() => changeTab('all')}
            >
              <span>
                <Icon name="grid" />
              </span>
              수강신청<span className="nav-arrow">↗</span>
            </button>
            <button
              data-tab="cart"
              className={`nav-item ${tab === 'cart' ? 'active' : ''}`}
              onClick={() => changeTab('cart')}
            >
              <span>
                <Icon name="bag" />
              </span>
              장바구니
              <span id="cart-badge" className="nav-badge">
                {state.cartIds.length}
              </span>
            </button>
            <button
              data-tab="enrolled"
              className={`nav-item ${tab === 'enrolled' ? 'active' : ''}`}
              onClick={() => changeTab('enrolled')}
            >
              <span>
                <Icon name="calendar" />
              </span>
              내 시간표
            </button>
          </nav>
          <div className="sidebar-bottom">
            <div className="help-card">
              <span className="help-symbol">?</span>
              <b>수강신청이 처음인가요?</b>
              <p>신청 전에 꼭 확인해주세요.</p>
              <button id="help-button" onClick={() => setHelp(true)}>
                수강신청 안내 <span>↗</span>
              </button>
            </div>
            <div className="sidebar-footer">
              <span className="tiny-dot"></span> 모든 시스템 정상 운영 중
              <small>© 2026 CAMPUS</small>
            </div>
          </div>
        </aside>
        <div className="workspace">
          <header className="topbar">
            <div className="breadcrumb">
              학사 서비스 <span>/</span> <b id="breadcrumb-current">{title}</b>
            </div>
            <div className="header-right">
              <span className="header-term">2026 FALL</span>
              <span className="header-divider"></span>
              <span className="avatar">{state.student.name[0]}</span>
              <div className="user-small">
                <b id="user-name">{state.student.name}</b>
                <small id="user-number">{`${state.student.studentNo} · ${state.student.department}`}</small>
              </div>
              <button
                id="logout"
                className="icon-button"
                title="로그아웃"
                aria-label="로그아웃"
                onClick={logout}
                disabled={busy}
              >
                <span>
                  <Icon name="logout" />
                </span>
              </button>
            </div>
          </header>
          <main>
            <div className="page-title">
              <div>
                <div className="eyebrow">PLAN YOUR SEMESTER</div>
                <h1 id="page-title">
                  {title}
                  <span className="title-dot">.</span>
                </h1>
                <p id="page-subtitle">{subtitle}</p>
              </div>
              <div className="registration-status">
                <span className="tiny-dot"></span> 수강신청 진행 중
                <span className="status-line">|</span> 2026 · 2학기
              </div>
            </div>

            <section className="summary-grid" aria-label="신청 현황">
              <div className="summary-card">
                <div className="stat-icon lavender">
                  <Icon name="book" />
                </div>
                <div>
                  <span>신청 학점</span>
                  <div className="stat-value">
                    <b id="credit-count">{total}</b>
                    <small>/ 18 학점</small>
                  </div>
                </div>
                <div className="credit-track">
                  <i
                    id="credit-progress"
                    style={{ width: `${(total / state.student.maxCredits) * 100}%` }}
                  ></i>
                </div>
              </div>
              <div className="summary-card">
                <div className="stat-icon mint">
                  <Icon name="check" />
                </div>
                <div>
                  <span>신청 완료</span>
                  <div className="stat-value">
                    <b id="enrolled-count">{state.enrolledIds.length}</b>
                    <small>과목</small>
                  </div>
                </div>
                <span className="stat-caption">나의 이번 학기</span>
              </div>
              <div className="summary-card">
                <div className="stat-icon apricot">
                  <Icon name="bag" />
                </div>
                <div>
                  <span>장바구니</span>
                  <div className="stat-value">
                    <b id="cart-count">{state.cartIds.length}</b>
                    <small>과목</small>
                  </div>
                </div>
                <button
                  className="stat-link"
                  id="view-cart"
                  aria-label="장바구니 보기"
                  onClick={() => changeTab('cart')}
                >
                  ↗
                </button>
              </div>
            </section>

            <div className="content-grid">
              <section className="catalog panel">
                <div className="panel-heading">
                  <h2 id="catalog-title">
                    {catalogTitle} <span>{visible.length}</span>
                  </h2>
                  <button id="refresh" className="subtle-button" onClick={refresh} disabled={busy}>
                    <span>
                      <Icon name="refresh" />
                    </span>{' '}
                    새로고침
                  </button>
                </div>
                <div className="catalog-controls">
                  <div className="search-wrap">
                    <span>
                      <Icon name="search" />
                    </span>
                    <input
                      id="search"
                      aria-label="강의 검색"
                      placeholder="강의명, 교수명, 학수번호 검색"
                      value={filters.search}
                      onChange={(e) => updateFilter('search', e.target.value)}
                    />
                    <kbd>⌕</kbd>
                  </div>
                  <div className="filter-row">
                    <select
                      id="department"
                      aria-label="학과 선택"
                      value={filters.department}
                      onChange={(e) => updateFilter('department', e.target.value)}
                    >
                      <option value="">전체 학과</option>
                      {[...new Set(state.courses.map((c) => c.department))].map((value) => (
                        <option key={value}>{value}</option>
                      ))}
                    </select>
                    <select
                      id="category"
                      aria-label="이수 구분 선택"
                      value={filters.category}
                      onChange={(e) => updateFilter('category', e.target.value)}
                    >
                      <option value="">전체 이수구분</option>
                      {[...new Set(state.courses.map((c) => c.category))].map((value) => (
                        <option key={value}>{value}</option>
                      ))}
                    </select>
                    <label className="available-filter">
                      <input
                        type="checkbox"
                        id="available"
                        checked={filters.available}
                        onChange={(e) => updateFilter('available', e.target.checked)}
                      />{' '}
                      신청 가능 강의만
                    </label>
                  </div>
                </div>
                <div className="list-tabs" role="tablist" aria-label="강의 목록">
                  <button
                    role="tab"
                    data-tab="all"
                    className={`${tab === 'all' ? 'active' : ''}`}
                    onClick={() => changeTab('all')}
                    aria-selected={tab === 'all'}
                  >
                    전체 강의 <span id="all-tab-count">{state.courses.length}</span>
                  </button>
                  <button
                    role="tab"
                    data-tab="cart"
                    onClick={() => changeTab('cart')}
                    className={`${tab === 'cart' ? 'active' : ''}`}
                    aria-selected={tab === 'cart'}
                  >
                    장바구니 <span id="cart-tab-count">{state.cartIds.length}</span>
                  </button>
                  <button
                    role="tab"
                    data-tab="enrolled"
                    onClick={() => changeTab('enrolled')}
                    className={`${tab === 'enrolled' ? 'active' : ''}`}
                    aria-selected={tab === 'enrolled'}
                  >
                    신청 내역 <span id="enrolled-tab-count">{state.enrolledIds.length}</span>
                  </button>
                </div>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>강의 정보</th>
                        <th>학점</th>
                        <th>시간 / 강의실</th>
                        <th>신청 현황</th>
                        <th>신청</th>
                      </tr>
                    </thead>
                    <CourseRows
                      courses={visible}
                      state={state}
                      busy={busy}
                      onPreview={setPreviewId}
                      onAction={onAction}
                    />
                  </table>
                </div>
                <div id="empty-list" className="empty-list" hidden={visible.length !== 0}>
                  <span>
                    <Icon name="search" />
                  </span>
                  <b>표시할 강의가 없어요</b>
                  <p id="empty-message">
                    {tab === 'cart'
                      ? '강의 목록에서 장바구니 아이콘을 눌러 담아보세요.'
                      : tab === 'enrolled'
                        ? '강의를 신청하면 시간표에 표시됩니다.'
                        : '검색어나 필터를 변경해 보세요.'}
                  </p>
                  <button id="reset-filters" className="text-button" onClick={resetFilters}>
                    필터 초기화
                  </button>
                </div>
                <footer className="catalog-footer">
                  <span id="result-count">{`총 ${visible.length}개 강의`}</span>
                  <span>
                    <span className="tiny-dot"></span> 강의에 마우스를 올려 시간표를 미리 보세요
                  </span>
                </footer>
              </section>
              <aside className="schedule-column">
                <Schedule state={state} previewId={previewId} onPrint={print} />
                <div className="notice-card">
                  <span>
                    <Icon name="info" />
                  </span>
                  <div>
                    <b>신청 전, 확인해주세요</b>
                    <ul>
                      <li>
                        학기당 최대 <strong>18학점</strong>까지 신청할 수 있어요.
                      </li>
                      <li>시간이 겹치는 강의는 중복 신청할 수 없어요.</li>
                      <li>장바구니에 담아도 수강신청은 별도로 필요해요.</li>
                    </ul>
                  </div>
                </div>
                <p className="saved-note">
                  <span>
                    <Icon name="shield" />
                  </span>{' '}
                  신청한 시간표는 자동으로 저장됩니다.
                </p>
              </aside>
            </div>
            <footer className="page-footer">
              배움의 모든 순간, CAMPUS와 함께.<span>COURSE REGISTRATION SYSTEM</span>
            </footer>
          </main>
        </div>
      </div>
      {pending && (
        <Modal title="수강신청을 취소할까요?" onClose={closeCancel}>
          <p>‘{pending.name}’ 강의가 시간표에서 삭제되고 자리가 반환됩니다.</p>
          <div className="dialog-actions">
            <button className="secondary" onClick={closeCancel}>
              유지하기
            </button>
            <button
              className="danger"
              onClick={() => {
                const id = pending.id;
                closeCancel();
                setPreviewId(null);
                mutate('cancel', id);
              }}
            >
              신청 취소
            </button>
          </div>
        </Modal>
      )}
      {help && (
        <Modal title="한 학기 준비, 이렇게 시작해요" onClose={() => setHelp(false)}>
          <ol className="guide-list">
            <li>강의명·교수명으로 검색하세요.</li>
            <li>강의에 마우스를 올리거나 키보드로 초점을 맞추면 시간표에 미리 표시됩니다.</li>
            <li>장바구니는 관심 목록이며 신청 버튼을 눌러야 등록됩니다.</li>
            <li>최대 {state.student.maxCredits}학점까지 신청할 수 있습니다.</li>
          </ol>
          <button className="primary" onClick={() => setHelp(false)}>
            확인했어요
          </button>
        </Modal>
      )}
    </>
  );
}
