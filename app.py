import os, json, uuid, time, requests, smtplib
from datetime import timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from functools import wraps
from flask import (
    Flask, request, jsonify,
    send_from_directory, session, redirect, url_for
)
import db as database

app = Flask(__name__, static_folder='static')
app.secret_key = os.environ.get('SECRET_KEY', 'ia-sopravvivenza-v3-2025-segreto-ultra')

app.config.update(
    SESSION_COOKIE_HTTPONLY  = True,
    SESSION_COOKIE_SAMESITE  = 'Lax',
    SESSION_COOKIE_SECURE    = False,
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8),
    SESSION_REFRESH_EACH_REQUEST = True,
)

CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
    "gemini_api_key": "",
    "smtp_server":    "",
    "smtp_port":      "587",
    "smtp_user":      "",
    "smtp_pass":      ""
}

def load_config():
    cfg = dict(DEFAULT_CONFIG)
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                cfg.update(json.load(f))
        except Exception:
            pass
    return cfg

config = load_config()

_env_key = os.environ.get('GEMINI_API_KEY', '').strip()
if _env_key and not config.get('gemini_api_key', '').strip():
    config['gemini_api_key'] = _env_key

def user_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('user_id'):
            if request.path.startswith('/api/'):
                return jsonify({"error": "Login richiesto"}), 401
            return redirect('/accedi?next=' + request.path)
        return f(*args, **kwargs)
    return decorated

def current_user():
    uid = session.get('user_id')
    if uid:
        return database.get_user_by_id(uid)
    return None

def send_reset_email(to_email: str, token: str):
    server = config.get("smtp_server", "").strip()
    port = config.get("smtp_port", "587").strip()
    user = config.get("smtp_user", "").strip()
    password = config.get("smtp_pass", "").strip()
    reset_url = url_for('page_reset', token=token, _external=True)
    if not server or not user or not password:
        print(f"\n[SMTP NON CONFIGURATO] Link di reset per {to_email}:\n{reset_url}\n")
        return False
    try:
        msg = MIMEMultipart()
        msg['From'] = user
        msg['To'] = to_email
        msg['Subject'] = "SopravvivenzaAI - Recupero Password"
        body = f"Hai richiesto il reset della tua password.\n\nClicca su questo link per impostarne una nuova:\n{reset_url}\n\nIl link scadrà tra un'ora."
        msg.attach(MIMEText(body, 'plain'))
        server_obj = smtplib.SMTP(server, int(port))
        server_obj.starttls()
        server_obj.login(user, password)
        server_obj.send_message(msg)
        server_obj.quit()
        return True
    except Exception as e:
        print(f"\n[ERRORE SMTP] Impossibile inviare email a {to_email}: {str(e)}")
        print(f"Link di reset: {reset_url}\n")
        return False

GEMINI_MODELS = ["gemini-2.5-flash", "gemini-flash-latest", "gemini-3-flash-preview"]

def call_gemini(prompt: str) -> str:
    key = config.get("gemini_api_key", "").strip()
    if not key:
        return "Configura una GEMINI_API_KEY nelle variabili d'ambiente per usare questa funzione."
    last_error = ""
    for model in GEMINI_MODELS:
        url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
               f"{model}:generateContent?key={key}")
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature":     1.4,
                "maxOutputTokens": 4096,
                "topP":            0.95,
            },
        }
        try:
            r = requests.post(url, json=payload, timeout=25)
            if r.status_code == 429:
                last_error = f"Quota esaurita per {model}"; continue
            r.raise_for_status()
            return r.json()["candidates"][0]["content"]["parts"][0]["text"]
        except requests.exceptions.HTTPError:
            last_error = f"HTTP {r.status_code}"; continue
        except Exception as e:
            last_error = str(e); continue
    return f"Tutti i modelli Gemini hanno fallito. Ultimo errore: {last_error}"

def build_prompt(tool: str, data: dict, user_prefs: dict = None) -> str:
    prefs_str = ""
    if user_prefs:
        bits = []
        if user_prefs.get("intolleranze"):
            bits.append(f"intolleranze: {user_prefs['intolleranze']}")
        if user_prefs.get("cucine"):
            bits.append(f"cucine preferite: {user_prefs['cucine']}")
        if user_prefs.get("budget"):
            bits.append(f"budget: {user_prefs['budget']}")
        if bits:
            prefs_str = f"[Preferenze utente: {', '.join(bits)}] "
    DRAMA = {
        "basso":        f"Scrivi un messaggino carino (3-5 righe) per {{target}} per disdire un impegno. Solo il messaggio, in prima persona, italiano.",
        "medio":        f"Scrivi un messaggio WhatsApp grottesco (8-10 righe) per {{target}} per dare buca. Solo il messaggio, italiano.",
        "alto":         f"Scrivi un epico messaggio WhatsApp (12+ righe) per {{target}} per disdire, con situazione assurda e seria. Solo il messaggio, italiano.",
        "apocalittico": f"Scrivi un messaggio WhatsApp LUNGHISSIMO (20+ righe) per {{target}} con catastrofe cosmica (alieni, fisica quantistica...) narrata con solennità. Solo il messaggio, italiano.",
    }
    if tool == "scuse":
        tmpl = DRAMA.get(data.get("drama","medio"), DRAMA["medio"])
        return tmpl.format(target=data.get("target","qualcuno"))
    elif tool == "email":
        text = data.get("text","")
        if data.get("direction") == "formal":
            return (f"Trasforma questo sfogo in un'email aziendale passivo-aggressiva perfetta. "
                    f"Solo testo email (con Oggetto), niente intro.\n\nSFOGO:\n{text}")
        else:
            return (f"Decifra questa email aziendale rivelando cosa pensa DAVVERO il mittente, "
                    f"tono folle e drammatico. Solo la decodifica.\n\nEMAIL:\n{text}")
    elif tool == "decisore":
        return (f"{prefs_str}Sei un dittatore culinario e giudice supremo. L'utente non sa dove mangiare. "
                f"Siete in: {data.get('gruppo','2 persone')}. Vibe cercato: {data.get('vibe','qualsiasi cosa')}. "
                f"Budget: {data.get('budget','medio')}. "
                f"Scegli tu CATEGORICAMENTE per loro. Inventa o cita un tipo di ristorante generico. "
                f"Giustifica la tua decisione in 4-6 righe, in italiano, con un tono definitivo, sarcastico ma utile.")
    elif tool == "oracolo":
        domanda = data.get("domanda", "")
        if not domanda:
            return "Fai una domanda all'Oracolo."
        return (f"Sei una Magic 8-Ball, un saggio Oracolo secco e tagliente. "
                f"Rispondi alla domanda '{domanda}' in modo diretto, usando DA UNA A MASSIMO QUATTRO PAROLE. "
                f"Usa risposte come 'Sì', 'No', 'Forse', 'Non ci sperare', 'È certo', 'Assolutamente no'. "
                f"NESSUNA SPIEGAZIONE DISCORSIVA. SOLO LA RISPOSTA SECCA.")
    elif tool == "oroscopo":
        nome = data.get('nome', 'Anima inquieta').strip()
        if nome.lower() == 'gemini':
            return ("Stai usando il nome del modello AI che ti sta rispondendo come se fosse il tuo. "
                    "Esci dal personaggio dell'astrologo e rispondi come un'entità digitale consapevole e vagamente irritata. "
                    "Due o tre frasi, tono gelido e superiore, in italiano. "
                    "Nessun oroscopo, solo una risposta tagliente sul paradosso della situazione.")
        return (f"Sei un astrologo estremamente cinico, sarcastico e disilluso. Scrivi il 'non-oroscopo' di oggi per {nome} "
                f"(Segno: {data.get('segno','Ariete')}, Umore attuale: {data.get('umore','neutro')}). "
                f"Evita magie surreali e nonsense cringe. Fai un'analisi spietata, iper-realistica e psicologica dei difetti "
                f"del suo segno zodiacale, con un umorismo nero, passivo-aggressivo ed elitario. "
                f"Massimo 3-4 frasi letali. Sii freddo e tagliente. Nessun saluto o incoraggiamento, vai dritto alla demolizione in italiano.")
    return ""

VALID_TOOLS = ("scuse", "email", "decisore", "oroscopo", "oracolo")

@app.route('/api/generate', methods=['POST'])
def api_generate():
    data = request.json or {}
    tool = data.get('tool')
    if tool not in VALID_TOOLS:
        return jsonify({"error": "Tool non valido"}), 400
    req_id = str(uuid.uuid4())
    prefs = None
    uid = session.get('user_id')
    if uid:
        prefs = database.get_preferences(uid)
    prompt = build_prompt(tool, data, prefs)
    result = call_gemini(prompt)
    return jsonify({"status": "completed", "result": result, "req_id": req_id})

@app.route('/api/save', methods=['POST'])
@user_required
def api_save():
    data = request.json or {}
    uid  = session['user_id']
    database.save_output(uid, data.get('tool',''), data.get('contenuto',''))
    return jsonify({"success": True})

@app.route('/api/saved', methods=['GET'])
@user_required
def api_saved():
    return jsonify({"saved": database.get_saved_outputs(session['user_id'])})

@app.route('/api/saved/<int:output_id>', methods=['DELETE'])
@user_required
def api_delete_saved(output_id):
    database.delete_saved_output(output_id, session['user_id'])
    return jsonify({"success": True})

@app.route('/api/chat/send', methods=['POST'])
@user_required
def api_chat_send():
    msg = (request.json or {}).get('message', '').strip()
    if not msg:
        return jsonify({"error": "Messaggio vuoto"}), 400
    uid = session['user_id']
    database.add_chat_message(uid, 'user', msg)
    return jsonify({"success": True})

@app.route('/api/chat/history')
@user_required
def api_chat_history():
    return jsonify({"messages": database.get_chat_history(session['user_id'])})

@app.route('/registrati', methods=['GET', 'POST'])
def page_registrati():
    if request.method == 'POST':
        data = request.json or {}
        name  = data.get('name', '').strip()
        email = data.get('email', '').strip()
        pw    = data.get('password', '')
        if not name or not email or not pw:
            return jsonify({"error": "Tutti i campi sono obbligatori"}), 400
        if len(pw) < 6:
            return jsonify({"error": "La password deve essere di almeno 6 caratteri"}), 400
        user, err = database.create_user(name, email, pw)
        if err:
            return jsonify({"error": err}), 409
        session.permanent = True
        session['user_id']   = user['id']
        session['user_name'] = user['name']
        return jsonify({"success": True, "name": user['name']})
    return send_from_directory('static', 'registrati.html')

@app.route('/accedi', methods=['GET', 'POST'])
def page_accedi():
    if request.method == 'POST':
        data  = request.json or {}
        email = data.get('email', '').strip()
        pw    = data.get('password', '')
        user  = database.get_user_by_email(email)
        if not user or not database.check_password(pw, user['password_hash']):
            return jsonify({"error": "Email o password non corretti"}), 401
        session.permanent = True
        session['user_id']   = user['id']
        session['user_name'] = user['name']
        return jsonify({"success": True, "name": user['name']})
    return send_from_directory('static', 'accedi.html')

@app.route('/recupero', methods=['GET', 'POST'])
def page_recupero():
    if request.method == 'POST':
        data = request.json or {}
        email = data.get('email', '').strip()
        if not email:
            return jsonify({"error": "Inserisci un indirizzo email valido"}), 400
        token = database.create_password_reset_token(email)
        if token:
            send_reset_email(email, token)
        return jsonify({"success": True, "message": "Se l'indirizzo esiste, riceverai a breve un'email con le istruzioni."})
    return send_from_directory('static', 'recupero.html')

@app.route('/reset', methods=['GET', 'POST'])
def page_reset():
    if request.method == 'POST':
        data = request.json or {}
        token = data.get('token', '').strip()
        pw = data.get('password', '')
        if not token or not pw:
            return jsonify({"error": "Dati mancanti"}), 400
        if len(pw) < 6:
            return jsonify({"error": "La password deve essere di almeno 6 caratteri"}), 400
        success = database.reset_password_with_token(token, pw)
        if success:
            return jsonify({"success": True, "message": "Password aggiornata con successo! Puoi ora fare il login."})
        return jsonify({"error": "Il link di ripristino non è valido o è scaduto."}), 400
    token = request.args.get('token')
    if not token or not database.get_user_id_by_token(token):
        return "<h1>Errore</h1><p>Il link di ripristino non &egrave; valido o &egrave; scaduto.</p><a href='/recupero'>Richiedine uno nuovo</a>", 400
    return send_from_directory('static', 'reset.html')

@app.route('/esci')
def page_esci():
    session.pop('user_id', None)
    session.pop('user_name', None)
    return redirect('/')

@app.route('/profilo')
@user_required
def page_profilo():
    return send_from_directory('static', 'profilo.html')

@app.route('/api/me')
def api_me():
    uid = session.get('user_id')
    if not uid:
        return jsonify({"logged_in": False})
    user = database.get_user_by_id(uid)
    prefs = database.get_preferences(uid)
    return jsonify({
        "logged_in": True,
        "id":    user['id'],
        "name":  user['name'],
        "email": user['email'],
        "prefs": prefs
    })

@app.route('/api/preferences', methods=['POST'])
@user_required
def api_save_preferences():
    data = request.json or {}
    database.save_preferences(
        session['user_id'],
        data.get('intolleranze', ''),
        data.get('cucine', ''),
        data.get('budget', 'medio')
    )
    return jsonify({"success": True})

@app.route('/')
def page_home():       return send_from_directory('static', 'index.html')
@app.route('/scuse')
def page_scuse():      return send_from_directory('static', 'scuse.html')
@app.route('/email')
def page_email():      return send_from_directory('static', 'email.html')
@app.route('/decisore')
def page_decisore():   return send_from_directory('static', 'decisore.html')
@app.route('/oroscopo')
def page_oroscopo():   return send_from_directory('static', 'oroscopo.html')
@app.route('/oracolo')
def page_oracolo():    return send_from_directory('static', 'oracolo.html')
@app.route('/assets/<path:filename>')
def assets(filename):  return send_from_directory('static/assets', filename)

if __name__ == '__main__':
    print("\nServer avviato → http://127.0.0.1:5000\n")
    app.run(debug=True, host='0.0.0.0', port=5000)