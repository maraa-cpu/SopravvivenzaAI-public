const loadingPhrases = [
  "Analizzando la rabbia latente...",
  "Convertendo lo sfogo in linguaggio corporativo...",
  "Applicando il filtro passivo-aggressivo...",
  "Decodificando il linguaggio aziendale...",
  "Un attimo, stiamo censurando le parolacce...",
  "Processando le emozioni represse...",
];
let currentDirection = 'formal';
let pollingTimer = null;
let loadingTimer = null;
const formArea = document.getElementById('form-area');
const loadingArea = document.getElementById('loading-area');
const loadingText = document.getElementById('loading-text');
const resultArea = document.getElementById('result-area');
const resultText = document.getElementById('result-text');
const textareaLabel = document.getElementById('textarea-label');
const emailInput = document.getElementById('email-input');
const placeholders = {
  formal: 'Es: Marco sei uno scansafatiche e non hai fatto niente di quello che ti avevo chiesto...',
  informal: 'Es: Come da accordi, mi permetto di portare alla sua attenzione alcune inefficienze riscontrate...'
};
document.querySelectorAll('#direction-group .chip').forEach(chip => {
  chip.addEventListener('click', () => {
    document.querySelectorAll('#direction-group .chip').forEach(c => c.classList.remove('active'));
    chip.classList.add('active');
    currentDirection = chip.dataset.value;
    if (currentDirection === 'formal') {
      textareaLabel.textContent = '✍️ Scrivi il tuo sfogo qui:';
      emailInput.placeholder = placeholders.formal;
    } else {
      textareaLabel.textContent = '✍️ Incolla l\'email formale qui:';
      emailInput.placeholder = placeholders.informal;
    }
  });
});
function showLoading() {
  formArea.style.display = 'none';
  resultArea.style.display = 'none';
  loadingArea.style.display = 'block';
  let i = 0;
  loadingText.textContent = loadingPhrases[0];
  loadingTimer = setInterval(() => {
    i = (i + 1) % loadingPhrases.length;
    loadingText.textContent = loadingPhrases[i];
  }, 3500);
}
function showResult(text) {
  clearInterval(loadingTimer);
  loadingArea.style.display = 'none';
  resultText.textContent = text;
  resultArea.style.display = 'block';
}
function showForm() {
  clearInterval(loadingTimer);
  clearInterval(pollingTimer);
  loadingArea.style.display = 'none';
  resultArea.style.display = 'none';
  formArea.style.display = 'block';
}
async function pollStatus(reqId) {
  try {
    const res = await fetch(`/api/status/${reqId}`);
    const data = await res.json();
    if (data.status === 'completed') {
      showResult(data.result);
    } else if (data.status === 'pending') {
      pollingTimer = setTimeout(() => pollStatus(reqId), 2000);
    } else {
      showResult(data.message || "Errore sconosciuto.");
    }
  } catch {
    showResult("Errore di connessione.");
  }
}
async function generate() {
  const text = emailInput.value.trim();
  if (!text) {
    emailInput.style.borderColor = 'var(--danger)';
    emailInput.focus();
    setTimeout(() => { emailInput.style.borderColor = ''; }, 2000);
    return;
  }
  showLoading();
  try {
    const res = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tool: 'email', text, direction: currentDirection })
    });
    const data = await res.json();
    if (data.status === 'completed') {
      showResult(data.result);
    } else if (data.status === 'pending') {
      pollStatus(data.req_id);
    } else {
      showResult(data.error || "Errore.");
    }
  } catch {
    showResult("Errore di connessione al server.");
  }
}
document.getElementById('generate-btn').addEventListener('click', generate);
document.getElementById('copy-btn').addEventListener('click', async () => {
  await navigator.clipboard.writeText(resultText.textContent);
  const btn = document.getElementById('copy-btn');
  btn.textContent = '✅ Copiato!';
  setTimeout(() => { btn.innerHTML = '📋 Copia Testo'; }, 2000);
});
document.getElementById('retry-btn').addEventListener('click', showForm);