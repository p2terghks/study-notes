import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, within, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from '../App.jsx';
import { clearCsrf, request } from '../shared/api/api.js';
import { filterCourses } from '../features/courses/courses.js';
const course = (id, name, day, start, end) => ({
  id,
  name,
  code: `C${id}`,
  professor: '교수',
  department: '컴퓨터공학과',
  category: '전공필수',
  credits: 3,
  capacity: 10,
  enrolled: 0,
  room: '공학관',
  color: 'violet',
  meetings: [{ day, start, end }],
});
let state, logged, config, requests;
function response(data, status = 200) {
  return {
    ok: status < 400,
    status,
    json: async () => data,
    text: async () => (data == null ? '' : JSON.stringify(data)),
  };
}
beforeEach(() => {
  clearCsrf();
  logged = false;
  config = { demoEnabled: true };
  requests = [];
  state = {
    student: {
      id: 1,
      name: '학생',
      studentNo: '20260001',
      department: '컴퓨터공학과',
      maxCredits: 18,
    },
    courses: [
      course(1, '자료구조', 0, 540, 600),
      course(2, '웹 프로그래밍', 1, 600, 660),
      course(3, '시간 충돌', 0, 570, 630),
    ],
    enrolledIds: [1],
    cartIds: [],
  };
  state.courses[0].enrolled = 1;
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url, options = {}) => {
      requests.push([url, options]);
      if (url === '/api/config') return response(config);
      if (url === '/api/csrf') return response({ headerName: 'X-CSRF-TOKEN', token: 'test-token' });
      if (url === '/api/state')
        return response(logged ? structuredClone(state) : null, logged ? 200 : 401);
      if (url === '/api/login') {
        logged = true;
        return response(null, 204);
      }
      if (url === '/api/logout') {
        logged = false;
        return response(null, 204);
      }
      if (url === '/api/register') return response(null, 201);
      if (url.startsWith('/api/cart/')) {
        const id = Number(url.split('/').pop());
        state.cartIds =
          options.method === 'POST'
            ? [...state.cartIds, id]
            : state.cartIds.filter((x) => x !== id);
        return response(null, 204);
      }
      if (url.startsWith('/api/enrollments/')) {
        const id = Number(url.split('/').pop());
        if (id === 3) return response({ message: '신청한 강의와 시간이 겹칩니다.' }, 409);
        state.enrolledIds =
          options.method === 'POST'
            ? [...state.enrolledIds, id]
            : state.enrolledIds.filter((x) => x !== id);
        state.cartIds = state.cartIds.filter((x) => x !== id);
        return response(null, 204);
      }
      throw new Error('Unexpected URL ' + url);
    }),
  );
});
async function demo() {
  render(<App />);
  await userEvent.click(await screen.findByRole('button', { name: /체험 계정/ }));
  await screen.findByRole('heading', { name: /수강신청/ });
}
describe('React 학사 화면', () => {
  it('로그인 → 미리보기 → 장바구니 → 신청 → 취소 → 로그아웃', async () => {
    await demo();
    const row = screen.getByRole('row', { name: '웹 프로그래밍 시간표 미리보기' });
    await userEvent.hover(row);
    expect(document.querySelector('.course-block.preview')).toHaveTextContent('웹 프로그래밍');
    await userEvent.click(within(row).getByRole('button', { name: '웹 프로그래밍 장바구니 담기' }));
    await screen.findByText('장바구니에 담았어요.');
    await userEvent.click(within(row).getByRole('button', { name: '신청' }));
    await within(row).findByRole('button', { name: '취소' });
    expect(state.cartIds).toEqual([]);
    expect(document.querySelectorAll('.course-block:not(.preview)')).toHaveLength(2);
    await userEvent.click(within(row).getByRole('button', { name: '취소' }));
    await userEvent.click(screen.getByRole('button', { name: '유지하기' }));
    expect(state.enrolledIds).toContain(2);
    await userEvent.click(within(row).getByRole('button', { name: '취소' }));
    await userEvent.click(screen.getByRole('button', { name: '신청 취소' }));
    await within(row).findByRole('button', { name: '신청' });
    await userEvent.click(screen.getByRole('button', { name: '로그아웃' }));
    await screen.findByRole('button', { name: '로그인 →' });
    expect(screen.queryByText('20260001 · 컴퓨터공학과')).not.toBeInTheDocument();
    const mutations = requests.filter(([u, o]) => o.method === 'POST' || o.method === 'DELETE');
    expect(mutations.every(([, o]) => o.headers['X-CSRF-TOKEN'] === 'test-token')).toBe(true);
  });
  it('검색·키보드 미리보기와 충돌 오류를 표시한다', async () => {
    await demo();
    const row = screen.getByRole('row', { name: '시간 충돌 시간표 미리보기' });
    fireEvent.focus(row);
    expect(document.querySelector('.preview.conflict')).toBeInTheDocument();
    await userEvent.click(within(row).getByRole('button', { name: '신청' }));
    await screen.findByText('신청한 강의와 시간이 겹칩니다.');
    expect(state.enrolledIds).toEqual([1]);
    await userEvent.type(screen.getByRole('textbox', { name: '강의 검색' }), '웹');
    expect(screen.queryByRole('row', { name: '자료구조 시간표 미리보기' })).not.toBeInTheDocument();
  });
  it('회원가입의 본문 없는 201 응답 후 로그인한다', async () => {
    config.demoEnabled = false;
    render(<App />);
    await userEvent.click(await screen.findByRole('button', { name: '회원가입' }));
    expect(screen.queryByRole('button', { name: /체험 계정/ })).not.toBeInTheDocument();
    await userEvent.type(screen.getByLabelText('학번'), '20269999');
    await userEvent.type(screen.getByLabelText('이름'), '새학생');
    await userEvent.type(screen.getByLabelText('비밀번호'), 'password123');
    await userEvent.click(screen.getByRole('button', { name: '회원가입 →' }));
    await screen.findByRole('heading', { name: /수강신청/ });
    expect(requests.some(([url]) => url === '/api/register')).toBe(true);
  });
  it('세션이 만료되면 개인 화면을 제거한다', async () => {
    await demo();
    logged = false;
    await userEvent.click(screen.getByRole('button', { name: '새로고침' }));
    await screen.findByRole('button', { name: '로그인 →' });
    expect(screen.queryByRole('row', { name: '자료구조 시간표 미리보기' })).not.toBeInTheDocument();
  });
  it('신청 가능 필터는 정원·시간·학점을 반영한다', () => {
    state.courses[1].enrolled = 10;
    expect(
      filterCourses(state, 'all', { search: '', department: '', category: '', available: true }),
    ).toEqual([]);
    state.courses[1].enrolled = 0;
    expect(
      filterCourses(state, 'all', {
        search: '',
        department: '',
        category: '',
        available: true,
      }).map((c) => c.id),
    ).toEqual([2]);
    state.student.maxCredits = 3;
    expect(
      filterCourses(state, 'all', { search: '', department: '', category: '', available: true }),
    ).toEqual([]);
  });
  it('403 변경 요청을 자동 재전송하지 않는다', async () => {
    vi.mocked(fetch).mockImplementation(async (url) =>
      url === '/api/csrf'
        ? response({ headerName: 'X-CSRF-TOKEN', token: 'test-token' })
        : response(null, 403),
    );
    await expect(request('/api/cart/2', 'POST')).rejects.toMatchObject({ status: 403 });
    expect(vi.mocked(fetch).mock.calls.filter(([url]) => url === '/api/cart/2')).toHaveLength(1);
  });
});
