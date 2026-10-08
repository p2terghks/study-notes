import { it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Advisor from '../features/advisor/Advisor.jsx';
import { clearCsrf } from '../shared/api/api.js';
it('독립 학적 정보 저장 후 출처와 21학점 선택 기준을 표시한다', async () => {
  clearCsrf();
  const saved = vi.fn();
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url, options = {}) => {
      let data = {};
      if (url === '/api/csrf') data = { headerName: 'X-CSRF-TOKEN', token: 'test' };
      if (url === '/api/advisor/profile' && options.method === 'PUT')
        data = JSON.parse(options.body);
      if (url === '/api/advisor/chat')
        data = {
          message: '스마트미디어 안내',
          points: ['파란색 과목 중 21학점 선택'],
          sources: [{ title: '사용자 제공 사진' }],
          suggestions: [],
        };
      return {
        ok: true,
        status: 200,
        json: async () => data,
        text: async () => JSON.stringify(data),
      };
    }),
  );
  render(<Advisor onProfileSaved={saved} onSessionExpired={vi.fn()} />);
  await userEvent.click(screen.getByRole('button', { name: '✦ 학사 도우미' }));
  await userEvent.selectOptions(await screen.findByLabelText('트랙'), '스마트미디어');
  await userEvent.click(screen.getByRole('button', { name: '학적 정보 저장' }));
  await userEvent.click(screen.getByRole('button', { name: '졸업 학점 알려줘' }));
  expect(await screen.findByText('파란색 과목 중 21학점 선택')).toBeInTheDocument();
  expect(screen.getByText('사용자 제공 사진')).toBeInTheDocument();
  expect(saved).toHaveBeenCalled();
});
