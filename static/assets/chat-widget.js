(async function initChat() {
  const me = await fetch('/api/me').then(r=>r.json());
  const fab = document.createElement('button');
  fab.className = 'chat-fab';
  fab.title = me.logged_in ? 'Chatta con l\'agente' : 'Login per chattare';
  fab.innerHTML = '💬';
  document.body.appendChild(fab);
  const win = document.createElement('div');
  win.className = 'chat-window';
  win.innerHTML = me.logged_in ? `
    <div class="chat-header">
      <div>
        <h4>💬 Assistenza Umana</h4>
        <p>Risponde il CEO in persona ✨</p>
      </div>
      <button class="chat-close" id="chat-close-btn">×</button>
    </div>
    <div class="chat-messages" id="chat-msgs"></div>
    <div class="chat-input-area">
      <input class="chat-input" id="chat-input" placeholder="Scrivi un messaggio..." maxlength="500">
      <button class="chat-send" id="chat-send-btn">Invia</button>
    </div>
  ` : `
    <div class="chat-header">
      <div><h4>💬 Assistenza Umana</h4><p>Feature esclusiva</p></div>
      <button class="chat-close" id="chat-close-btn">×</button>
    </div>
    <div class="chat-locked">
      <strong>🔐 Feature per Utenti Registrati</strong>
      Crea un account gratuito per chattare direttamente con l'agente reale!<br><br>
      <a href="/registrati" class="btn btn-primary" style="font-size:.88rem;padding:10px 22px;">Registrati Gratis →</a>
    </div>
  `;
  document.body.appendChild(win);
  fab.addEventListener('click', () => {
    win.classList.toggle('open');
    if(win.classList.contains('open') && me.logged_in) loadHistory();
  });
  document.getElementById('chat-close-btn')?.addEventListener('click', () => win.classList.remove('open'));
  if(!me.logged_in) return;
  const msgContainer   = document.getElementById('chat-msgs');
  const inputEl        = document.getElementById('chat-input');
  const sendBtn        = document.getElementById('chat-send-btn');
  let   lastMsgCount   = 0;
  const renderMsg = (m) => {
    const div = document.createElement('div');
    div.className = `chat-msg ${m.sender}`;
    const names = { user: me.name, ceo: '⚡ Agente' };
    div.innerHTML = `<div class="msg-sender">${names[m.sender]||m.sender}</div>${m.message.replace(/</g,'&lt;')}`;
    msgContainer.appendChild(div);
    msgContainer.scrollTop = msgContainer.scrollHeight;
  };
  const loadHistory = async () => {
    const r = await fetch('/api/chat/history');
    const d = await r.json();
    if(d.messages.length !== lastMsgCount) {
      msgContainer.innerHTML = '';
      d.messages.forEach(renderMsg);
      lastMsgCount = d.messages.length;
    }
  };
  const send = async () => {
    const msg = inputEl.value.trim();
    if(!msg) return;
    inputEl.value = '';
    await fetch('/api/chat/send', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ message: msg })
    });
    loadHistory();
  };
  sendBtn.addEventListener('click', send);
  inputEl.addEventListener('keydown', e => { if(e.key==='Enter') send(); });
  setInterval(() => { if(win.classList.contains('open')) loadHistory(); }, 4000);
})();