(() => {
  const form = document.querySelector('#answer-form');
  if (!form) return;
  const status = document.querySelector('#save-status');
  const retry = document.querySelector('#retry-save');
  const csrf = form.querySelector('[name=csrfmiddlewaretoken]').value;
  let timer, queue = Promise.resolve(), navigating = false;
  const value = () => form.querySelector('textarea')?.value ?? form.querySelector('input[name=answer]:checked')?.value ?? '';
  function save() {
    const answer = value();
    status.textContent = '저장 중…';
    queue = queue.catch(() => {}).then(async () => {
      try {
        const response = await fetch(form.dataset.saveUrl, {method:'POST', headers:{'Content-Type':'application/json','X-CSRFToken':csrf}, body:JSON.stringify({answer})});
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || '저장하지 못했습니다.');
        status.textContent = '저장 완료';
        status.className = 'muted'; retry.hidden = true;
        const indicator = document.querySelector(`[data-position="${form.dataset.position}"] .status`);
        indicator.textContent = data.answered ? '●' : '○';
        indicator.setAttribute('aria-label', data.answered ? '응답 완료' : '미응답');
      } catch (error) {
        status.textContent = `${error.message} 답안은 화면에 유지됩니다. 저장을 재시도하세요.`;
        status.className = 'error'; retry.hidden = false;
        throw error;
      }
    });
    return queue;
  }
  form.addEventListener('submit', event => event.preventDefault());
  form.addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(() => save().catch(() => {}), 350); });
  form.addEventListener('change', () => { clearTimeout(timer); save().catch(() => {}); });
  retry.addEventListener('click', () => save().catch(() => {}));
  document.querySelectorAll('[data-nav]').forEach(link => link.addEventListener('click', async event => {
    event.preventDefault(); if (navigating) return; navigating = true; clearTimeout(timer);
    try { await save(); window.location.assign(link.href); } catch { navigating = false; }
  }));
})();
