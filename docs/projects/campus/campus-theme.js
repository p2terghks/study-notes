(() => {
  const key = 'study-notes-theme';
  let theme = 'light';
  try { if (localStorage.getItem(key) === 'dark') theme = 'dark'; } catch {}
  document.documentElement.dataset.theme = theme;
  document.addEventListener('DOMContentLoaded', () => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'theme-toggle';
    const update = () => {
      const dark = document.documentElement.dataset.theme === 'dark';
      button.textContent = dark ? '라이트 모드' : '다크 모드';
      button.setAttribute('aria-label', dark ? '라이트 모드로 전환' : '다크 모드로 전환');
      button.setAttribute('aria-pressed', String(dark));
    };
    button.addEventListener('click', () => {
      const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
      document.documentElement.dataset.theme = next;
      try { localStorage.setItem(key, next); } catch {}
      update();
    });
    update();
    document.body.append(button);

    const search = document.querySelector('#toc-search');
    const links = [...document.querySelectorAll('.chapter-links a')];
    if (search) {
      const filter = () => {
        const terms = search.value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
        let count = 0;
        for (const link of links) {
          const match = terms.every(term => link.textContent.toLocaleLowerCase().includes(term));
          link.hidden = !match;
          if (match) count++;
        }
        document.querySelector('#toc-count').textContent = `${count}개 항목 / 전체 ${links.length}개`;
      };
      search.addEventListener('input', filter);
      filter();
    }

    document.addEventListener('click', async event => {
      const copy = event.target.closest('.copy');
      if (!copy) return;
      const code = copy.closest('.codebox').querySelector('pre code');
      const lines = [...code.querySelectorAll('.line-text')];
      const text = lines.length ? lines.map(line => line.textContent).join('\n') : code.textContent;
      const status = document.querySelector('#copy-status');
      try {
        await navigator.clipboard.writeText(text);
        status.textContent = '코드를 복사했습니다.';
      } catch {
        status.textContent = '복사를 사용할 수 없습니다. 코드 내용을 선택해 복사해주세요.';
      }
      setTimeout(() => { status.textContent = ''; }, 2500);
    });
  });
})();
