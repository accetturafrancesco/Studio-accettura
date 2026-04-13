import sqlite3, json
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "accettura.db"

def conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    with conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS pazienti (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nome        TEXT NOT NULL,
            cognome     TEXT NOT NULL,
            eta         INTEGER,
            sesso       TEXT,
            telefono    TEXT,
            created_at  TEXT DEFAULT (datetime('now','localtime')),
            cond_tipo   TEXT,
            cond_desc   TEXT,
            immagini    TEXT DEFAULT '[]',
            piano       TEXT DEFAULT '{}',
            flags       TEXT DEFAULT '{}'
        );
        CREATE TABLE IF NOT EXISTS sedute (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            paziente_id     INTEGER NOT NULL,
            numero          INTEGER NOT NULL,
            data            TEXT DEFAULT (datetime('now','localtime')),
            freq_sett       INTEGER DEFAULT 2,
            totale          INTEGER DEFAULT 10,
            protocollo      TEXT DEFAULT '{}',
            completata      INTEGER DEFAULT 0,
            osservazioni    TEXT DEFAULT '',
            check_esercizi  TEXT DEFAULT '{}',
            FOREIGN KEY (paziente_id) REFERENCES pazienti(id)
        );
        CREATE TABLE IF NOT EXISTS appuntamenti (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            paziente_id INTEGER,
            titolo      TEXT,
            data_ora    TEXT,
            durata_min  INTEGER DEFAULT 45,
            note        TEXT DEFAULT '',
            FOREIGN KEY (paziente_id) REFERENCES pazienti(id)
        );
        CREATE TABLE IF NOT EXISTS attrezzatura (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nome        TEXT NOT NULL,
            descrizione TEXT DEFAULT '',
            added_at    TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS impostazioni (
            chiave      TEXT PRIMARY KEY,
            valore      TEXT DEFAULT '',
            updated_at  TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS chat_settings (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            role        TEXT,
            content     TEXT,
            created_at  TEXT DEFAULT (datetime('now','localtime'))
        );
        """)
        if c.execute("SELECT COUNT(*) FROM attrezzatura").fetchone()[0] == 0:
            c.executemany("INSERT INTO attrezzatura (nome, descrizione) VALUES (?,?)", [
                ("Corpo libero",         "Esercizi a peso corporeo, senza attrezzi"),
                ("Loop band",            "Elastico circolare per resistenza progressiva"),
                ("Cavigliere 1 kg ×2",   "Per rinforzo arto superiore e inferiore"),
                ("Resistenza manuale",   "Resistenza offerta direttamente dal terapista"),
            ])
        for k, v in [("prompt_extra",""), ("note_generali",""), ("stile","tecnico")]:
            c.execute("INSERT OR IGNORE INTO impostazioni (chiave, valore) VALUES (?,?)", (k,v))

# ── PAZIENTI ──────────────────────────────────────────────────────────────────
def get_pazienti():
    with conn() as c:
        return [dict(r) for r in c.execute(
            "SELECT * FROM pazienti ORDER BY cognome, nome").fetchall()]

def get_paziente(pid):
    with conn() as c:
        r = c.execute("SELECT * FROM pazienti WHERE id=?", (pid,)).fetchone()
        return dict(r) if r else None

def insert_paziente(nome, cognome, eta, sesso, telefono, cond_tipo, cond_desc, immagini, piano, flags):
    with conn() as c:
        cur = c.execute(
            "INSERT INTO pazienti (nome,cognome,eta,sesso,telefono,cond_tipo,cond_desc,immagini,piano,flags)"
            " VALUES (?,?,?,?,?,?,?,?,?,?)",
            (nome, cognome, eta, sesso, telefono, cond_tipo, cond_desc,
             json.dumps(immagini), json.dumps(piano), json.dumps(flags))
        )
        return cur.lastrowid

def delete_paziente(pid):
    with conn() as c:
        c.execute("DELETE FROM sedute WHERE paziente_id=?", (pid,))
        c.execute("DELETE FROM appuntamenti WHERE paziente_id=?", (pid,))
        c.execute("DELETE FROM pazienti WHERE id=?", (pid,))

def update_paziente_piano(pid, piano, flags):
    with conn() as c:
        c.execute("UPDATE pazienti SET piano=?, flags=? WHERE id=?",
                  (json.dumps(piano), json.dumps(flags), pid))

# ── SEDUTE ────────────────────────────────────────────────────────────────────
def get_sedute(paziente_id):
    with conn() as c:
        return [dict(r) for r in c.execute(
            "SELECT * FROM sedute WHERE paziente_id=? ORDER BY numero", (paziente_id,)).fetchall()]

def get_seduta(sid):
    with conn() as c:
        r = c.execute("SELECT * FROM sedute WHERE id=?", (sid,)).fetchone()
        return dict(r) if r else None

def insert_seduta(paziente_id, numero, freq_sett, totale, protocollo):
    with conn() as c:
        cur = c.execute(
            "INSERT INTO sedute (paziente_id,numero,freq_sett,totale,protocollo) VALUES (?,?,?,?,?)",
            (paziente_id, numero, freq_sett, totale, json.dumps(protocollo))
        )
        return cur.lastrowid

def update_seduta(sid, check_esercizi=None, osservazioni=None, completata=None):
    with conn() as c:
        if check_esercizi is not None:
            c.execute("UPDATE sedute SET check_esercizi=? WHERE id=?", (json.dumps(check_esercizi), sid))
        if osservazioni is not None:
            c.execute("UPDATE sedute SET osservazioni=? WHERE id=?", (osservazioni, sid))
        if completata is not None:
            c.execute("UPDATE sedute SET completata=? WHERE id=?", (int(completata), sid))

# ── APPUNTAMENTI ─────────────────────────────────────────────────────────────
def get_appuntamenti():
    with conn() as c:
        return [dict(r) for r in c.execute(
            "SELECT a.*, p.nome, p.cognome FROM appuntamenti a "
            "LEFT JOIN pazienti p ON a.paziente_id=p.id "
            "ORDER BY a.data_ora").fetchall()]

def insert_appuntamento(paziente_id, titolo, data_ora, durata_min=45, note=""):
    with conn() as c:
        c.execute("INSERT INTO appuntamenti (paziente_id,titolo,data_ora,durata_min,note) VALUES (?,?,?,?,?)",
                  (paziente_id, titolo, data_ora, durata_min, note))

def delete_appuntamento(aid):
    with conn() as c:
        c.execute("DELETE FROM appuntamenti WHERE id=?", (aid,))

# ── ATTREZZATURA ─────────────────────────────────────────────────────────────
def get_attrezzatura():
    with conn() as c:
        return [dict(r) for r in c.execute("SELECT * FROM attrezzatura ORDER BY nome").fetchall()]

def insert_attrezzatura(nome, descrizione):
    with conn() as c:
        c.execute("INSERT INTO attrezzatura (nome, descrizione) VALUES (?,?)", (nome, descrizione))

def delete_attrezzatura(aid):
    with conn() as c:
        c.execute("DELETE FROM attrezzatura WHERE id=?", (aid,))

# ── IMPOSTAZIONI ─────────────────────────────────────────────────────────────
def get_setting(chiave, default=""):
    with conn() as c:
        r = c.execute("SELECT valore FROM impostazioni WHERE chiave=?", (chiave,)).fetchone()
        return r[0] if r else default

def set_setting(chiave, valore):
    with conn() as c:
        c.execute("INSERT OR REPLACE INTO impostazioni (chiave, valore, updated_at) VALUES (?,?,datetime('now','localtime'))",
                  (chiave, valore))

# ── CHAT SETTINGS ─────────────────────────────────────────────────────────────
def get_chat_settings():
    with conn() as c:
        return [dict(r) for r in c.execute("SELECT * FROM chat_settings ORDER BY created_at").fetchall()]

def append_chat_settings(role, content):
    with conn() as c:
        c.execute("INSERT INTO chat_settings (role, content) VALUES (?,?)", (role, content))

def clear_chat_settings():
    with conn() as c:
        c.execute("DELETE FROM chat_settings")
