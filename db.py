import sqlite3
import hashlib
import os
import uuid
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash as wz_check_hash

DB_PATH = "database.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f', 'now'))
);
CREATE TABLE IF NOT EXISTS preferences (
    user_id INTEGER PRIMARY KEY,
    intolleranze TEXT NOT NULL DEFAULT '',
    cucine TEXT NOT NULL DEFAULT '',
    budget TEXT NOT NULL DEFAULT 'medio',
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f', 'now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS saved_outputs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    tool TEXT NOT NULL,
    contenuto TEXT NOT NULL,
    saved_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f', 'now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS chats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    sender TEXT NOT NULL CHECK(sender IN ('user', 'ceo')),
    message TEXT NOT NULL,
    sent_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f', 'now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS password_resets (
    token TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f', 'now')),
    expires_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_saved_user ON saved_outputs(user_id);
CREATE INDEX IF NOT EXISTS idx_chats_user ON chats(user_id);
CREATE INDEX IF NOT EXISTS idx_resets_user ON password_resets(user_id);
"""

def get_db():
    conn = sqlite3.connect(DB_PATH, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA foreign_keys=ON')
    conn.execute('PRAGMA synchronous=NORMAL')
    return conn

def init_db():
    conn = get_db()
    conn.executescript(SCHEMA)
    conn.close()

def hash_password(password: str) -> str:
    return generate_password_hash(password, method='pbkdf2:sha256')

def _legacy_hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(password: str, stored_hash: str) -> bool:
    if stored_hash.startswith('pbkdf2:'):
        return wz_check_hash(stored_hash, password)
    return _legacy_hash(password) == stored_hash

def create_user(name: str, email: str, password: str):
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (name, email, password_hash, created_at) VALUES (?,?,?,?)",
            (name, email.lower().strip(), hash_password(password), datetime.now().isoformat())
        )
        conn.commit()
        row = conn.execute("SELECT * FROM users WHERE email=?", (email.lower().strip(),)).fetchone()
        conn.execute("INSERT OR IGNORE INTO preferences (user_id) VALUES (?)", (row['id'],))
        conn.commit()
        return dict(row), None
    except sqlite3.IntegrityError:
        return None, "Email già registrata."
    finally:
        conn.close()

def get_user_by_email(email: str):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE email=?", (email.lower().strip(),)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_user_by_id(user_id: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_preferences(user_id: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM preferences WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else {"user_id": user_id, "intolleranze": "", "cucine": "", "budget": "medio"}

def save_preferences(user_id: int, intolleranze: str, cucine: str, budget: str):
    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO preferences (user_id, intolleranze, cucine, budget) VALUES (?,?,?,?)",
        (user_id, intolleranze, cucine, budget)
    )
    conn.commit()
    conn.close()

def save_output(user_id: int, tool: str, contenuto: str):
    conn = get_db()
    conn.execute(
        "INSERT INTO saved_outputs (user_id, tool, contenuto, saved_at) VALUES (?,?,?,?)",
        (user_id, tool, contenuto, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def get_saved_outputs(user_id: int):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM saved_outputs WHERE user_id=? ORDER BY saved_at DESC LIMIT 50",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_saved_output(output_id: int, user_id: int):
    conn = get_db()
    conn.execute("DELETE FROM saved_outputs WHERE id=? AND user_id=?", (output_id, user_id))
    conn.commit()
    conn.close()

def add_chat_message(user_id: int, sender: str, message: str):
    conn = get_db()
    conn.execute(
        "INSERT INTO chats (user_id, sender, message, sent_at) VALUES (?,?,?,?)",
        (user_id, sender, message, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def get_chat_history(user_id: int, limit: int = 50):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM chats WHERE user_id=? ORDER BY sent_at ASC LIMIT ?",
        (user_id, limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_all_active_chats():
    conn = get_db()
    rows = conn.execute("""
        SELECT u.id, u.name, u.email,
               MAX(c.sent_at) as last_message,
               SUM(CASE WHEN c.sender='user' THEN 1 ELSE 0 END) as user_messages,
               (SELECT message FROM chats WHERE user_id=u.id ORDER BY sent_at DESC LIMIT 1) as preview
        FROM users u
        JOIN chats c ON u.id = c.user_id
        GROUP BY u.id
        ORDER BY last_message DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_all_users():
    conn = get_db()
    rows = conn.execute("SELECT id, name, email, created_at FROM users ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def create_password_reset_token(email: str):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email=?", (email.lower().strip(),)).fetchone()
    if not user:
        conn.close()
        return None
    token = str(uuid.uuid4())
    expires = datetime.fromtimestamp(datetime.now().timestamp() + 3600).isoformat()
    conn.execute(
        "INSERT INTO password_resets (token, user_id, expires_at) VALUES (?,?,?)",
        (token, user['id'], expires)
    )
    conn.commit()
    conn.close()
    return token

def get_user_id_by_token(token: str):
    conn = get_db()
    row = conn.execute("SELECT user_id, expires_at FROM password_resets WHERE token=?", (token,)).fetchone()
    conn.close()
    if not row:
        return None
    if datetime.now().isoformat() > row['expires_at']:
        return None
    return row['user_id']

def reset_password_with_token(token: str, new_password: str):
    user_id = get_user_id_by_token(token)
    if not user_id:
        return False
    conn = get_db()
    conn.execute("UPDATE users SET password_hash=? WHERE id=?", (hash_password(new_password), user_id))
    conn.execute("DELETE FROM password_resets WHERE token=?", (token,))
    conn.commit()
    conn.close()
    return True

def get_stats_by_tool():
    conn = get_db()
    rows = conn.execute("SELECT tool, COUNT(*) as cnt FROM saved_outputs GROUP BY tool").fetchall()
    conn.close()
    return {r['tool']: r['cnt'] for r in rows}

init_db()