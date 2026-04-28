const dramaMap = { "1": "basso", "2": "medio", "3": "alto", "4": "apocalittico" };
const dramaLabelMap = { "1": "😴 Basso", "2": "😬 Medio", "3": "😱 Alto", "4": "🌋 Apocalittico" };
const loadingPhrases = [
  "Chiamando gli dèi dell'IA...",
  "Rielaborando la realtà quantistica...",
  "Consultando l'Oracolo delle Scuse...",
  "Il CEO sta controllando... ehm, l'IA intende...",
  "Analizzando le probabilità di farla franca...",
  "Tessendo la trama della tua liberazione...",
  "Un attimo, la scusa è in fase di cottura...",
];
let currentTarget = "Il Capo";
let currentDrama = "medio";
let currentReqId = null;
let pollingTimer = null;
let loadingTimer = null;
const formArea = document.getElementById('form-area');
const loadingArea = document.getElementById('loading-area');
const loadingText = document.getElementById('loading-text');
const resultArea = document.getElementById('result-area');
const resultText = document.getElementById('result-text');
document.querySelectorAll('#target-group .chip').forEach(chip => {
  chip.addEventListener('click', () => {
    document.querySelectorAll('#target-group .chip').forEach(c => c.classList.remove('active'));
    chip.classList.add('active');
    currentTarget = chip.dataset.value;
  });
});
const slider = document.getElementById('drama-slider');
const dramaLabel = document.getElementById('drama-label');
slider.addEventListener('input', () => {
  dramaLabel.textContent = dramaLabelMap[slider.value];
  currentDrama = dramaMap[slider.value];
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
  showLoading();
  try {
    const res = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tool: 'scuse', target: currentTarget, drama: currentDrama })
    });
    const data = await res.json();
    if (data.status === 'completed') {
      showResult(data.result);
    } else if (data.status === 'pending') {
      currentReqId = data.req_id;
      pollStatus(currentReqId);
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
  setTimeout(() => { btn.innerHTML = '📋 Copia per WhatsApp'; }, 2000);
});
document.getElementById('retry-btn').addEventListener('click', () => {
  showForm();
});