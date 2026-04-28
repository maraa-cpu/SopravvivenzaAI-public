(async function() {
  let me = { logged_in: false };
  try {
    const r = await fetch('/api/me');
    if (r.ok) me = await r.json();
  } catch (_) {  }
  const area = document.getElementById('nav-user-area');
  if(me.logged_in) {
    if(area) area.innerHTML = `<a href="/profilo" class="nav-user"><span class="nav-user-dot"></span>${me.name.split(' ')[0]}</a>`;
    const heroBtns = document.getElementById('hero-auth-buttons');
    if(heroBtns) {
      heroBtns.innerHTML = `
        <a href="/profilo" class="btn btn-primary" style="padding:12px 28px;font-size:.95rem;">👤 Il tuo Pannello</a>
        <a href="/scuse" class="btn btn-ghost" style="padding:12px 28px;font-size:.95rem;">Esplora i Tool →</a>
      `;
    }
  } else {
    if(area) area.innerHTML = `<a href="/accedi" class="btn btn-ghost" style="padding:7px 16px;font-size:.88rem;">Accedi</a>`;
  }
})();