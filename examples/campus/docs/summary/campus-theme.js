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
      button.textContent = dark ? '☀ 라이트 모드' : '☾ 다크 모드';
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
    (document.querySelector('.toolbar') || document.querySelector('main') || document.body).append(button);
  });
})();
