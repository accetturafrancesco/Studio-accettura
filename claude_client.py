import json, base64, anthropic
import database as db

MODEL = "claude-sonnet-4-6"
client = anthropic.Anthropic()

BASE = """Sei il Dott. Francesco Accettura, fisioterapista domiciliare specializzato in ortopedia, neurologia e pediatria.
Contesto: trattamenti SEMPRE domiciliari. Attrezzatura: {attrezzatura}.
Prediligi corpo libero, resistenza manuale, loop band, cavigliere.
Sedute da 45 minuti, max 3/settimana.
Stile: {stile}. Note: {note}. Extra: {extra}.
IMPORTANTE: rispondi SOLO con JSON valido e compatto. Niente testo fuori dal JSON. Niente markdown."""

def _base():
    att = ", ".join([a["nome"] for a in db.get_attrezzatura()])
    return BASE.format(
        attrezzatura=att,
        stile=db.get_setting("stile", "tecnico"),
        note=db.get_setting("note_generali", ""),
        extra=db.get_setting("prompt_extra", ""),
    )

def _parse(txt):
    txt = txt.strip()
    txt = txt.replace("```json","").replace("```","").strip()
    # Prova parsing diretto
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        # Tenta riparazione: tronca all'ultima } o ] valida
        for i in range(len(txt)-1, -1, -1):
            if txt[i] in ('}', ']'):
                try:
                    return json.loads(txt[:i+1])
                except Exception:
                    continue
        raise ValueError("JSON non riparabile")

def _imgs_to_content(imgs):
    content = []
    for img in imgs:
        if "," in img:
            header, data = img.split(",", 1)
            mt = header.split(":")[1].split(";")[0]
        else:
            data, mt = img, "image/jpeg"
        content.append({"type":"image","source":{"type":"base64","media_type":mt,"data":data}})
    return content

# ── VALUTAZIONE ───────────────────────────────────────────────────────────────
PROMPT_VAL = """Paziente: {nome} {cognome}, {eta} anni, {sesso}. Tipo: {cond_tipo}. Descrizione: {cond_desc}

Rispondi SOLO con questo JSON (sii conciso, max 3 voci per lista):
{{"diagnosi_fisio":"...","diagnosi_differenziale":["...","..."],"strutture_coinvolte":["..."],"stadio":"acuto|subacuto|cronico","flags":{{"red":["..."],"yellow":["..."],"black":[],"orange":[],"blue":[]}},"tests_consigliati":[{{"nome":"...","obiettivo":"...","procedura_passo_passo":["1...","2...","3..."],"positivo_se":"...","significato_clinico":"..."}}],"suggerimento_sedute":{{"settimanali_consigliato":2,"totali_stimate":12,"rationale":"..."}},"obiettivi":{{"breve_termine":"...","medio_termine":"...","lungo_termine":"..."}}}}"""

def valuta_paziente(paz, imgs=[]):
    content = _imgs_to_content(imgs)
    content.append({"type":"text","text":PROMPT_VAL.format(**paz)})
    r = client.messages.create(
        model=MODEL, max_tokens=2000,
        system=_base(),
        messages=[{"role":"user","content":content}],
    )
    return _parse(r.content[0].text)

# ── SEDUTA ────────────────────────────────────────────────────────────────────
PROMPT_SED = """Seduta {numero}/{totale}. Paziente: {nome} {cognome}, {eta}a, {sesso}.
Diagnosi: {diagnosi_fisio}. Stadio: {stadio}. Flags: {flags}. Obs precedente: {obs_prec}.
Frequenza: {freq_sett}/sett. DOMICILIARE, 45 min totali.

Rispondi SOLO con questo JSON (descrizioni brevi e chiare, max 4 esercizi per fase):
{{"rivalutazione":{{"durata_min":5,"checklist":["...","..."],"domande_chiave":["...","..."]}},"fase_passiva":{{"durata_min":10,"descrizione":"...","esercizi":[{{"id":"p1","nome":"...","tipo":"passivo","desc_tecnica":"...","desc_paziente":"...","posizione":"...","serie":3,"ripetizioni":10,"durata_sec":null,"frequenza_hep":"non per HEP","downscaling":"...","attrezzatura":"corpo libero","youtube":"...","note_cliniche":"..."}}]}},"fase_attiva":{{"durata_min":25,"descrizione":"...","esercizi":[{{"id":"a1","nome":"...","tipo":"attivo","desc_tecnica":"...","desc_paziente":"...","posizione":"...","serie":3,"ripetizioni":15,"durata_sec":null,"frequenza_hep":"ogni giorno","downscaling":"...","attrezzatura":"corpo libero","youtube":"...","note_cliniche":"..."}}]}},"hep":{{"note_generali":"...","esercizi":[{{"id":"h1","nome":"...","desc_paziente":"Spiegazione semplice passo passo senza termini tecnici.","posizione":"...","serie":2,"ripetizioni":10,"durata_sec":null,"frequenza":"ogni giorno","attrezzatura":"corpo libero","youtube":"..."}}]}}}}"""

def genera_seduta(paziente, piano, numero, totale, freq_sett, obs_prec=""):
    flags = []
    for k, v in (piano.get("flags") or {}).items():
        if v: flags.append(f"[{k.upper()}] {', '.join(v)}")

    r = client.messages.create(
        model=MODEL, max_tokens=3000,
        system=_base(),
        messages=[{"role":"user","content": PROMPT_SED.format(
            nome=paziente["nome"], cognome=paziente["cognome"],
            eta=paziente["eta"], sesso=paziente["sesso"],
            diagnosi_fisio=piano.get("diagnosi_fisio","N/D"),
            stadio=piano.get("stadio","N/D"),
            flags="; ".join(flags) or "nessuna",
            obs_prec=obs_prec or "prima seduta",
            numero=numero, totale=totale, freq_sett=freq_sett,
        )}],
    )
    return _parse(r.content[0].text)

# ── CHAT IMPOSTAZIONI ─────────────────────────────────────────────────────────
SYS_SET = """Sei l'assistente di configurazione del Dott. Francesco Accettura.
Interpreta le richieste e restituisci SOLO JSON:
{{"risposta":"...","azioni":{{"prompt_extra":null,"note_generali":null,"stile":null}},"attrezzatura_aggiungi":[],"attrezzatura_rimuovi":[]}}
Impostazioni attuali — prompt_extra: {extra}, note: {note}, stile: {stile}"""

def chat_impostazioni(history, user_msg):
    system = SYS_SET.format(
        extra=db.get_setting("prompt_extra",""),
        note=db.get_setting("note_generali",""),
        stile=db.get_setting("stile","tecnico"),
    )
    msgs = [{"role":m["role"],"content":m["content"]} for m in history]
    msgs.append({"role":"user","content":user_msg})
    r = client.messages.create(
        model=MODEL, max_tokens=800,
        system=system, messages=msgs,
    )
    return _parse(r.content[0].text)
