# ⚡ SopravvivenzaAI

Piattaforma satirica di AI tools per i problemi quotidiani non urgenti. Generatore di scuse, traduttore email, decisore di cene, oroscopo cinico e oracolo cosmico.

**Powered by Google Gemini 2.5**

## Features

- 🎭 **Generatore di Scuse** — Messaggi WhatsApp da "basso" ad "apocalittico"
- 📧 **Traduttore Email** — Sfogo → email professionale, oppure decodifica email corporate
- 🍕 **Decisore di Cene** — Il dittatore culinario AI che sceglie per te
- 🪐 **Oroscopo Cinico** — Anti-oroscopo passivo-aggressivo
- 🎱 **L'Oracolo** — Magic 8-ball AI per decisioni difficili
- 👤 **Account Utente** — Salva output, chat con l'agente

## Stack

- **Backend**: Python 3.11 + Flask
- **Database**: SQLite (WAL mode, foreign keys, indexes)
- **AI**: Google Gemini API (model fallback: 2.5-flash → flash-latest)
- **Frontend**: Vanilla HTML/CSS/JS
- **Auth**: Session cookie (utenti) + JWT-style token (CEO dashboard)
- **Security**: PBKDF2-SHA256+salt (werkzeug) per password

## Setup Locale

```bash
git clone <repo-url>
cd scuse
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

Vai su `http://127.0.0.1:5005` e configura la Gemini API Key dalla dashboard CEO.

## Configurazione

Il file `config.json` (escluso da git) viene creato automaticamente al primo avvio.
Per il deploy, imposta le variabili d'ambiente:

| Variabile | Descrizione |
|-----------|-------------|
| `SECRET_KEY` | Chiave segreta Flask (obbligatoria in produzione) |
| `GEMINI_API_KEY` | Chiave Google Gemini (opzionale, configurabile dalla dashboard) |


---

> I contenuti generati sono satirici e non costituiscono consigli reali.
