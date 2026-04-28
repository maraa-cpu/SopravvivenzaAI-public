export function setupChips(groupId, activeClass = 'active') {
  const chips = document.querySelectorAll(`#${groupId} .chip`);
  let selected = chips[0]?.dataset.value ?? '';
  chips.forEach(chip => {
    chip.addEventListener('click', () => {
      chips.forEach(c => c.classList.remove(activeClass));
      chip.classList.add(activeClass);
      selected = chip.dataset.value;
    });
  });
  return { getValue: () => selected };
}
export async function generate(payload, { spinnerClass = '', textClass = '', phrases = [] } = {}) {
  const formArea    = document.getElementById('form-area');
  const loadingArea = document.getElementById('loading-area');
  const resultArea  = document.getElementById('result-area');
  const loadingText = document.getElementById('loading-text');
  const spinner     = document.querySelector('.spinner');
  if (spinner && spinnerClass) spinner.className = `spinner ${spinnerClass}`;
  if (loadingText && textClass) loadingText.className = `loading-text ${textClass}`;
  formArea.style.display    = 'none';
  resultArea.style.display  = 'none';
  loadingArea.style.display = 'block';
  let i = 0;
  let phraseTimer = null;
  if (phrases.length && loadingText) {
    loadingText.textContent = phrases[0];
    phraseTimer = setInterval(() => {
      i = (i + 1) % phrases.length;
      loadingText.textContent = phrases[i];
    }, 3500);
  }
  const resetUI = (text) => {
    if (phraseTimer !== null) clearInterval(phraseTimer);
    loadingArea.style.display = 'none';
    const resultTextEl = document.getElementById('result-text');
    if (resultTextEl) resultTextEl.textContent = text;
    resultArea.style.display = 'block';
  };
  try {
    const res  = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.status === 'completed') {
      resetUI(data.result);
    } else if (data.status === 'pending') {
      poll(data.req_id, resetUI);
    } else {
      resetUI(data.error || 'Errore sconosciuto.');
    }
  } catch {
    resetUI('❌ Errore di connessione al server. Assicurati che il server sia avviato.');
  }
}
function poll(reqId, onDone) {
  setTimeout(async () => {
    try {
      const res  = await fetch(`/api/status/${reqId}`);
      const data = await res.json();
      if (data.status === 'completed') onDone(data.result);
      else if (data.status === 'pending') poll(reqId, onDone);
      else onDone(data.message || 'Errore.');
    } catch {
      onDone('❌ Errore durante il caricamento della risposta.');
    }
  }, 2000);
}
export function setupCopyBtn(btnId, sourceId) {
  document.getElementById(btnId)?.addEventListener('click', async () => {
    const text = document.getElementById(sourceId)?.textContent ?? '';
    await navigator.clipboard.writeText(text);
    const btn = document.getElementById(btnId);
    const orig = btn.textContent;
    btn.textContent = '✅ Copiato!';
    setTimeout(() => { btn.textContent = orig; }, 2000);
  });
}
export function setupRetryBtn(btnId) {
  document.getElementById(btnId)?.addEventListener('click', () => {
    document.getElementById('result-area').style.display  = 'none';
    document.getElementById('loading-area').style.display = 'none';
    document.getElementById('form-area').style.display    = 'block';
  });
}