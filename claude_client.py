import json, base64, anthropic
import database as db

MODEL = "claude-sonnet-4-6"
client = anthropic.Anthropic()

# ── PROMPT BASE ───────────────────────────────────────────────────────────────
BASE = """Sei il Dott. Francesco Accettura, fisioterapista domiciliare con 25 anni di esperienza.
Specializzazioni: ortopedia/muscoloscheletrico, neurologia, pediatria.

CONTESTO OPERATIVO FONDAMENTALE:
- Trattamenti SEMPRE domiciliari: niente macchinari ospedalieri, niente attrezzatura da palestra
- Attrezzatura disponibile: {attrezzatura}
- Prediligi esercizi a corpo libero e contro resistenza manuale o con elastici
- Ogni seduta dura 45 minuti (incluse rivalutazione e pausa)
- Frequenza: max 3 sedute/settimana

STILE: {stile}
NOTE GENERALI: {note}
PERSONALIZZAZIONI: {extra}
"""

def _base():
    att = ", ".join([a["nome"] for a in db.get_attrezzatura()])
    return BASE.format(
        attrezzatura=att,
        stile=db.get_setting("stile", "tecnico e dettagliato"),
        note=db.get_setting("note_generali", ""),
        extra=db.get_setting("prompt_extra", ""),
    )

def _imgs_to_content(immagini_b64: list) -> list:
    """Converte lista base64 in content blocks per Claude Vision."""
    content = []
    for img in immagini_b64:
        if "," in img:
            header, data = img.split(",", 1)
            mt = header.split(":")[1].split(";")[0] if ":" in header else "image/jpeg"
        else:
            data, mt = img, "image/jpeg"
        content.append({"type": "image", "source": {"type": "base64", "media_type": mt, "data": data}})
    return content

# ── 1. VALUTAZIONE INIZIALE ───────────────────────────────────────────────────
PROMPT_VALUTAZIONE = """
Analizza il paziente e genera un piano riabilitativo completo in JSON.
Il paziente è: {nome} {cognome}, {eta} anni, sesso {sesso}.
Tipo condizione: {cond_tipo}
Descrizione: {cond_desc}

Rispondi SOLO con JSON valido, nessun testo fuori dal JSON:
{{
  "diagnosi_fisio": "...",
  "diagnosi_differenziale": ["...", "..."],
  "strutture_coinvolte": ["..."],
  "stadio": "acuto|subacuto|cronico",
  "flags": {{
    "red": ["...", "..."],
    "yellow": ["...", "..."],
    "black": ["...", "..."],
    "orange": ["...", "..."],
    "blue": ["...", "..."]
  }},
  "tests_consigliati": [
    {{
      "nome": "...",
      "obiettivo": "...",
      "procedura_passo_passo": ["passo 1", "passo 2", "passo 3"],
      "positivo_se": "...",
      "significato_clinico": "..."
    }}
  ],
  "suggerimento_sedute": {{
    "settimanali_min": 1,
    "settimanali_max": 3,
    "settimanali_consigliato": 2,
    "totali_stimate": 12,
    "rationale": "..."
  }},
  "obiettivi": {{
    "breve_termine": "...",
    "medio_termine": "...",
    "lungo_termine": "..."
  }},
  "note_cliniche": "..."
}}
"""

def valuta_paziente(paziente: dict, immagini_b64: list = []) -> dict:
    content = _imgs_to_content(immagini_b64)
    content.append({"type": "text", "text": PROMPT_VALUTAZIONE.format(**paziente)})
    r = client.messages.create(
        model=MODEL, max_tokens=4096,
        system=_base(),
        messages=[{"role": "user", "content": content}],
    )
    txt = r.content[0].text.strip()
    txt = txt.replace("```json","").replace("```","").strip()
    return json.loads(txt)

# ── 2. PROTOCOLLO SEDUTA ──────────────────────────────────────────────────────
PROMPT_SEDUTA = """
Genera il protocollo dettagliato per la SEDUTA N.{numero} di {totale} totali.
Frequenza: {freq_sett} seduta/e per settimana.

PAZIENTE: {nome} {cognome}, {eta} anni, {sesso}
DIAGNOSI: {diagnosi_fisio}
STADIO: {stadio}
FLAGS ATTIVE: {flags_rilevanti}
OSSERVAZIONI SEDUTA PRECEDENTE: {obs_prec}

Genera un protocollo 45 minuti DOMICILIARE. Rispondi SOLO JSON:
{{
  "rivalutazione": {{
    "durata_min": 5,
    "checklist": ["item da verificare 1", "item 2", "item 3"],
    "scale": ["NRS 0-10", "ROM se pertinente"],
    "domande_chiave": ["domanda 1", "domanda 2"]
  }},
  "fase_passiva": {{
    "durata_min": 10,
    "descrizione": "...",
    "esercizi": [
      {{
        "id": "p1",
        "nome": "Nome esercizio",
        "tipo": "passivo|assistito",
        "desc_tecnica": "Descrizione tecnica dettagliata per il fisioterapista...",
        "desc_paziente": "Spiegazione semplice in italiano quotidiano per il paziente...",
        "posizione": "posizione di partenza del paziente",
        "serie": 3,
        "ripetizioni": 10,
        "durata_sec": null,
        "frequenza_hep": "ogni giorno|a giorni alterni|non per HEP",
        "downscaling": "Come semplificare se il paziente non riesce",
        "attrezzatura": "corpo libero|loop band|cavigliera|resistenza manuale",
        "youtube": "query youtube per cercare video dell'esercizio",
        "note_cliniche": "perché questo esercizio in questa fase"
      }}
    ]
  }},
  "fase_attiva": {{
    "durata_min": 25,
    "descrizione": "...",
    "esercizi": [
      {{
        "id": "a1",
        "nome": "Nome esercizio",
        "tipo": "attivo|attivo-assistito|rinforzo",
        "desc_tecnica": "...",
        "desc_paziente": "...",
        "posizione": "...",
        "serie": 3,
        "ripetizioni": 15,
        "durata_sec": null,
        "frequenza_hep": "ogni giorno|a giorni alterni|non per HEP",
        "downscaling": "...",
        "attrezzatura": "...",
        "youtube": "...",
        "note_cliniche": "..."
      }}
    ]
  }},
  "hep": {{
    "titolo": "Esercizi per casa — giorni liberi dal trattamento",
    "note_generali": "...",
    "esercizi": [
      {{
        "id": "h1",
        "nome": "Nome esercizio",
        "desc_paziente": "Spiegazione molto semplice, passo per passo, in italiano quotidiano. Nessun termine tecnico. Spiega come se il paziente non avesse mai fatto fisioterapia.",
        "posizione": "...",
        "serie": 2,
        "ripetizioni": 10,
        "durata_sec": null,
        "frequenza": "ogni giorno|a giorni alterni",
        "attrezzatura": "...",
        "youtube": "..."
      }}
    ]
  }},
  "note_seduta": "...",
  "progressione_verso_prossima": "..."
}}
"""

def genera_seduta(paziente: dict, piano: dict, numero: int, totale: int,
                  freq_sett: int, obs_prec: str = "") -> dict:
    flags_rilevanti = []
    if piano.get("flags"):
        for k, v in piano["flags"].items():
            if v:
                flags_rilevanti.append(f"[{k.upper()}] {', '.join(v)}")

    prompt = PROMPT_SEDUTA.format(
        nome=paziente["nome"], cognome=paziente["cognome"],
        eta=paziente["eta"], sesso=paziente["sesso"],
        diagnosi_fisio=piano.get("diagnosi_fisio","N/D"),
        stadio=piano.get("stadio","N/D"),
        flags_rilevanti="; ".join(flags_rilevanti) or "Nessuna",
        obs_prec=obs_prec or "Prima seduta",
        numero=numero, totale=totale, freq_sett=freq_sett,
    )
    r = client.messages.create(
        model=MODEL, max_tokens=4096,
        system=_base(),
        messages=[{"role": "user", "content": prompt}],
    )
    txt = r.content[0].text.strip().replace("```json","").replace("```","").strip()
    return json.loads(txt)

# ── 3. CHAT IMPOSTAZIONI ──────────────────────────────────────────────────────
PROMPT_SETTINGS_SYSTEM = """Sei un assistente di configurazione per il sistema clinico del Dott. Francesco Accettura.
Il tuo compito è interpretare le richieste dell'utente e restituire SEMPRE un JSON con le modifiche da applicare.

Impostazioni correnti:
- prompt_extra: {extra}
- note_generali: {note}
- stile: {stile}

Quando l'utente dice cose come "aggiungi cavigliere 2kg", "togli i link YouTube", "voglio risposte più brevi",
"aggiungi fisioterapia respiratoria", ecc., traduci in aggiornamenti al sistema.

Rispondi con JSON:
{{
  "risposta": "Messaggio amichevole che conferma cosa hai fatto",
  "azioni": {{
    "prompt_extra": "nuovo valore o null per non cambiare",
    "note_generali": "nuovo valore o null",
    "stile": "nuovo valore o null"
  }},
  "attrezzatura_aggiungi": [{{"nome":"...","descrizione":"..."}}],
  "attrezzatura_rimuovi": []
}}
"""

def chat_impostazioni(history: list, user_msg: str) -> dict:
    system = PROMPT_SETTINGS_SYSTEM.format(
        extra=db.get_setting("prompt_extra",""),
        note=db.get_setting("note_generali",""),
        stile=db.get_setting("stile","tecnico"),
    )
    msgs = [{"role": m["role"], "content": m["content"]} for m in history]
    msgs.append({"role": "user", "content": user_msg})
    r = client.messages.create(
        model=MODEL, max_tokens=1000,
        system=system,
        messages=msgs,
    )
    txt = r.content[0].text.strip().replace("```json","").replace("```","").strip()
    return json.loads(txt)
