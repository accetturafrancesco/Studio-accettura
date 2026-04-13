import json, re, anthropic
import database as db

MODEL  = "claude-sonnet-4-6"
client = anthropic.Anthropic()

def _base():
    att = ", ".join([a["nome"] for a in db.get_attrezzatura()])
    return (f"Sei il Dott. Francesco Accettura, fisioterapista domiciliare. "
            f"Ortopedia, neurologia, pediatria. Sempre domiciliare. "
            f"Attrezzatura: {att}. Corpo libero preferito. Sedute 45 min, max 3/sett. "
            f"Stile: {db.get_setting('stile','tecnico')}. "
            f"{db.get_setting('note_generali','')} {db.get_setting('prompt_extra','')} "
            "IMPORTANTE: usa SOLO stringhe semplici negli array, mai oggetti annidati.")

def _ask(prompt, max_tokens=600):
    r = client.messages.create(
        model=MODEL, max_tokens=max_tokens,
        system=_base(),
        messages=[{"role":"user","content":prompt}],
    )
    txt = r.content[0].text.strip()
    txt = re.sub(r"```json|```","",txt).strip()
    s = txt.find("{"); e = txt.rfind("}")
    if s == -1 or e == -1:
        raise ValueError(f"Nessun JSON: {txt[:200]}")
    txt = txt[s:e+1]
    try:
        return json.loads(txt)
    except Exception as err:
        raise ValueError(f"JSON non riparabile: {err}. Testo: {txt[:400]}")

def _imgs_to_content(imgs):
    out = []
    for img in imgs:
        if "," in img:
            h, d = img.split(",",1)
            mt = h.split(":")[1].split(";")[0]
        else:
            d, mt = img, "image/jpeg"
        out.append({"type":"image","source":{"type":"base64","media_type":mt,"data":d}})
    return out

# ── VALUTAZIONE ───────────────────────────────────────────────────────────────
def valuta_paziente(paz, imgs=[]):
    content = _imgs_to_content(imgs)
    content.append({"type":"text","text":
        f"Paziente: {paz['nome']} {paz['cognome']}, {paz['eta']}a, {paz['sesso']}. "
        f"Condizione ({paz['cond_tipo']}): {paz['cond_desc']}\n\n"
        "Rispondi SOLO con JSON. Tutti gli array devono contenere SOLO stringhe semplici, MAI oggetti.\n"
        '{"diagnosi_fisio":"una sola frase","diagnosi_differenziale":["diagnosi 1","diagnosi 2"],'
        '"strutture_coinvolte":["struttura 1","struttura 2"],"stadio":"subacuto",'
        '"flags":{"red":["flag 1"],"yellow":["flag 1"],"black":[],"orange":[],"blue":[]},'
        '"tests_consigliati":[{"nome":"nome test","obiettivo":"obiettivo","procedura_passo_passo":["passo 1","passo 2","passo 3"],"positivo_se":"quando e positivo","significato_clinico":"significato"}],'
        '"suggerimento_sedute":{"settimanali_consigliato":2,"totali_stimate":12,"rationale":"motivo"},'
        '"obiettivi":{"breve_termine":"obiettivo","medio_termine":"obiettivo","lungo_termine":"obiettivo"}}'
    })
    r = client.messages.create(
        model=MODEL, max_tokens=1200,
        system=_base(),
        messages=[{"role":"user","content":content}],
    )
    txt = r.content[0].text.strip()
    txt = re.sub(r"```json|```","",txt).strip()
    s = txt.find("{"); e = txt.rfind("}")
    if s == -1 or e == -1:
        raise ValueError(f"Nessun JSON: {txt[:200]}")
    return json.loads(txt[s:e+1])

# ── RIVALUTAZIONE ─────────────────────────────────────────────────────────────
def _rivalutazione(paz, piano, obs_prec):
    return _ask(
        f"Rivalutazione 5 min per {paz['nome']}, diagnosi: {piano.get('diagnosi_fisio','')}. "
        f"Obs precedente: {obs_prec or 'prima seduta'}.\n"
        "SOLO JSON con array di STRINGHE SEMPLICI (non oggetti):\n"
        '{"durata_min":5,'
        '"checklist":["cosa verificare 1","cosa verificare 2","cosa verificare 3"],'
        '"domande_chiave":["domanda 1","domanda 2"]}',
        max_tokens=300)

# ── FASE PASSIVA ──────────────────────────────────────────────────────────────
def _fase_passiva(paz, piano, flags_txt):
    return _ask(
        f"Fase passiva 10 min per {paz['nome']}, diagnosi: {piano.get('diagnosi_fisio','')}. "
        f"Stadio: {piano.get('stadio','')}. Flags: {flags_txt}. DOMICILIARE.\n"
        "2 esercizi massimo. Array con SOLE STRINGHE. SOLO JSON:\n"
        '{"durata_min":10,"descrizione":"descrizione fase",'
        '"esercizi":[{"id":"p1","nome":"nome esercizio","tipo":"passivo",'
        '"desc_tecnica":"descrizione tecnica breve","desc_paziente":"spiegazione semplice",'
        '"posizione":"posizione di partenza","serie":3,"ripetizioni":10,"durata_sec":null,'
        '"downscaling":"versione piu facile","attrezzatura":"corpo libero",'
        '"youtube":"query youtube","note_cliniche":"razionale clinico"}]}',
        max_tokens=600)

# ── FASE ATTIVA ───────────────────────────────────────────────────────────────
def _fase_attiva(paz, piano, flags_txt):
    return _ask(
        f"Fase attiva 25 min per {paz['nome']}, diagnosi: {piano.get('diagnosi_fisio','')}. "
        f"Stadio: {piano.get('stadio','')}. Flags: {flags_txt}. DOMICILIARE.\n"
        "3 esercizi massimo. Array con SOLE STRINGHE. SOLO JSON:\n"
        '{"durata_min":25,"descrizione":"descrizione fase",'
        '"esercizi":[{"id":"a1","nome":"nome esercizio","tipo":"attivo",'
        '"desc_tecnica":"descrizione tecnica breve","desc_paziente":"spiegazione semplice",'
        '"posizione":"posizione di partenza","serie":3,"ripetizioni":15,"durata_sec":null,'
        '"downscaling":"versione piu facile","attrezzatura":"corpo libero",'
        '"youtube":"query youtube","note_cliniche":"razionale clinico"}]}',
        max_tokens=800)

# ── HEP ───────────────────────────────────────────────────────────────────────
def _hep(paz, piano, numero):
    return _ask(
        f"HEP seduta {numero} per {paz['nome']}, diagnosi: {piano.get('diagnosi_fisio','')}. "
        f"Stadio: {piano.get('stadio','')}. Esercizi per casa, giorni liberi.\n"
        "3 esercizi max. Linguaggio SEMPLICISSIMO per paziente non esperto. SOLO JSON:\n"
        '{"note_generali":"nota generale per il paziente",'
        '"esercizi":[{"id":"h1","nome":"nome esercizio",'
        '"desc_paziente":"spiegazione passo passo molto semplice senza termini tecnici",'
        '"posizione":"come mettersi","serie":2,"ripetizioni":10,"durata_sec":null,'
        '"frequenza":"ogni giorno","attrezzatura":"corpo libero","youtube":"query youtube"}]}',
        max_tokens=700)

# ── GENERA SEDUTA ─────────────────────────────────────────────────────────────
def genera_seduta(paziente, piano, numero, totale, freq_sett, obs_prec=""):
    flags = []
    for k, v in (piano.get("flags") or {}).items():
        if v: flags.append(f"[{k.upper()}] {', '.join(v)}")
    flags_txt = "; ".join(flags) or "nessuna"
    return {
        "rivalutazione": _rivalutazione(paziente, piano, obs_prec),
        "fase_passiva":  _fase_passiva(paziente, piano, flags_txt),
        "fase_attiva":   _fase_attiva(paziente, piano, flags_txt),
        "hep":           _hep(paziente, piano, numero),
    }

# ── CHAT IMPOSTAZIONI ─────────────────────────────────────────────────────────
def chat_impostazioni(history, user_msg):
    system = (f"Assistente config Dott. Accettura. "
              f"Stile={db.get_setting('stile','tecnico')}, "
              f"note={db.get_setting('note_generali','')}, "
              f"extra={db.get_setting('prompt_extra','')}. "
              "Rispondi SOLO JSON:\n"
              '{"risposta":"conferma azione","azioni":{"prompt_extra":null,"note_generali":null,"stile":null},'
              '"attrezzatura_aggiungi":[],"attrezzatura_rimuovi":[]}')
    msgs = [{"role":m["role"],"content":m["content"]} for m in history]
    msgs.append({"role":"user","content":user_msg})
    r = client.messages.create(model=MODEL, max_tokens=400, system=system, messages=msgs)
    txt = r.content[0].text.strip()
    txt = re.sub(r"```json|```","",txt).strip()
    s = txt.find("{"); e = txt.rfind("}")
    return json.loads(txt[s:e+1])
