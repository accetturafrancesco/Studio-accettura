import json, re, anthropic
import database as db

MODEL  = "claude-sonnet-4-6"
client = anthropic.Anthropic()

def _base():
    att = ", ".join([a["nome"] for a in db.get_attrezzatura()])
    return (f"Sei il Dott. Francesco Accettura, fisioterapista domiciliare. "
            f"Specializzazioni: ortopedia, neurologia, pediatria. "
            f"Trattamenti SEMPRE domiciliari. Attrezzatura: {att}. "
            f"Prediligi corpo libero, resistenza manuale, loop band, cavigliere 1kg. "
            f"Sedute 45 minuti, max 3/sett. "
            f"Stile: {db.get_setting('stile','tecnico')}. "
            f"{db.get_setting('note_generali','')} {db.get_setting('prompt_extra','')} "
            f"REGOLA: rispondi SEMPRE e SOLO con JSON valido. Niente testo fuori dal JSON.")

def _ask(prompt, max_tokens=1200):
    r = client.messages.create(
        model=MODEL, max_tokens=max_tokens,
        system=_base(),
        messages=[{"role":"user","content":prompt}],
    )
    return _parse(r.content[0].text)

def _parse(txt):
    txt = txt.strip()
    # rimuovi markdown
    txt = re.sub(r"```json|```","",txt).strip()
    # estrai da { a }
    s = txt.find("{"); e = txt.rfind("}")
    if s == -1 or e == -1:
        raise ValueError(f"Nessun JSON: {txt[:300]}")
    txt = txt[s:e+1]
    # rimuovi newline dentro stringhe (causa errori parser)
    txt = re.sub(r'(?<=[^\\])\n(?=[^"\{\}\[\]])',' ', txt)
    try:
        return json.loads(txt)
    except json.JSONDecodeError as err:
        # prova a riparare troncature
        for i in range(len(txt)-1,-1,-1):
            if txt[i] in "}]":
                try:
                    return json.loads(txt[:i+1])
                except Exception:
                    continue
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

# ─────────────────────────────────────────────────────────────────────────────
#  VALUTAZIONE
# ─────────────────────────────────────────────────────────────────────────────
def valuta_paziente(paz, imgs=[]):
    content = _imgs_to_content(imgs)
    content.append({"type":"text","text":
        f"Paziente: {paz['nome']} {paz['cognome']}, {paz['eta']}a, {paz['sesso']}. "
        f"Condizione ({paz['cond_tipo']}): {paz['cond_desc']}\n\n"
        "Restituisci SOLO questo JSON (stringhe su una riga, no a capo dentro le stringhe):\n"
        '{"diagnosi_fisio":"...","diagnosi_differenziale":["...","..."],'
        '"strutture_coinvolte":["..."],"stadio":"subacuto",'
        '"flags":{"red":["..."],"yellow":["..."],"black":[],"orange":[],"blue":[]},'
        '"tests_consigliati":[{"nome":"...","obiettivo":"...","procedura_passo_passo":["1.","2.","3."],"positivo_se":"...","significato_clinico":"..."}],'
        '"suggerimento_sedute":{"settimanali_consigliato":2,"totali_stimate":12,"rationale":"..."},'
        '"obiettivi":{"breve_termine":"...","medio_termine":"...","lungo_termine":"..."}}'
    })
    r = client.messages.create(
        model=MODEL, max_tokens=1500,
        system=_base(),
        messages=[{"role":"user","content":content}],
    )
    return _parse(r.content[0].text)

# ─────────────────────────────────────────────────────────────────────────────
#  SEDUTA — 4 chiamate separate, ognuna piccola e sicura
# ─────────────────────────────────────────────────────────────────────────────
def _rivalutazione(paz, piano, obs_prec):
    return _ask(
        f"Rivalutazione iniziale (5 min) per {paz['nome']} {paz['cognome']}, "
        f"diagnosi: {piano.get('diagnosi_fisio','')}, stadio: {piano.get('stadio','')}. "
        f"Obs precedente: {obs_prec or 'prima seduta'}.\n"
        "SOLO JSON su una riga:\n"
        '{"durata_min":5,"checklist":["verifica NRS","verifica ROM"],"domande_chiave":["come si sente?","ha fatto HEP?"]}',
        max_tokens=400)

def _fase_passiva(paz, piano, flags_txt):
    return _ask(
        f"Fase passiva (10 min) per {paz['nome']}, diagnosi: {piano.get('diagnosi_fisio','')}, "
        f"stadio: {piano.get('stadio','')}. Flags: {flags_txt}. DOMICILIARE.\n"
        "Max 2 esercizi. Ogni stringa su UNA RIGA senza a capo. SOLO JSON:\n"
        '{"durata_min":10,"descrizione":"...","esercizi":[{"id":"p1","nome":"...","tipo":"passivo",'
        '"desc_tecnica":"...","desc_paziente":"...","posizione":"...",'
        '"serie":3,"ripetizioni":10,"durata_sec":null,"downscaling":"...",'
        '"attrezzatura":"corpo libero","youtube":"...","note_cliniche":"..."}]}',
        max_tokens=800)

def _fase_attiva(paz, piano, flags_txt):
    return _ask(
        f"Fase attiva (25 min) per {paz['nome']}, diagnosi: {piano.get('diagnosi_fisio','')}, "
        f"stadio: {piano.get('stadio','')}. Flags: {flags_txt}. DOMICILIARE.\n"
        "Max 3 esercizi. Ogni stringa su UNA RIGA. SOLO JSON:\n"
        '{"durata_min":25,"descrizione":"...","esercizi":[{"id":"a1","nome":"...","tipo":"attivo",'
        '"desc_tecnica":"...","desc_paziente":"...","posizione":"...",'
        '"serie":3,"ripetizioni":15,"durata_sec":null,"downscaling":"...",'
        '"attrezzatura":"corpo libero","youtube":"...","note_cliniche":"..."}]}',
        max_tokens=1000)

def _hep(paz, piano, numero):
    return _ask(
        f"HEP seduta {numero} per {paz['nome']}, diagnosi: {piano.get('diagnosi_fisio','')}, "
        f"stadio: {piano.get('stadio','')}. Esercizi per casa nei giorni liberi.\n"
        "Max 3 esercizi. Linguaggio SEMPLICISSIMO per paziente non esperto. "
        "Ogni stringa su UNA RIGA senza a capo. SOLO JSON:\n"
        '{"note_generali":"...","esercizi":[{"id":"h1","nome":"...","desc_paziente":"...",'
        '"posizione":"...","serie":2,"ripetizioni":10,"durata_sec":null,'
        '"frequenza":"ogni giorno","attrezzatura":"corpo libero","youtube":"..."}]}',
        max_tokens=800)

def genera_seduta(paziente, piano, numero, totale, freq_sett, obs_prec=""):
    flags = []
    for k, v in (piano.get("flags") or {}).items():
        if v: flags.append(f"[{k.upper()}] {', '.join(v)}")
    flags_txt = "; ".join(flags) or "nessuna"

    return {
        "rivalutazione":  _rivalutazione(paziente, piano, obs_prec),
        "fase_passiva":   _fase_passiva(paziente, piano, flags_txt),
        "fase_attiva":    _fase_attiva(paziente, piano, flags_txt),
        "hep":            _hep(paziente, piano, numero),
    }

# ─────────────────────────────────────────────────────────────────────────────
#  CHAT IMPOSTAZIONI
# ─────────────────────────────────────────────────────────────────────────────
def chat_impostazioni(history, user_msg):
    system = (f"Assistente config Dott. Accettura. "
              f"Stato: stile={db.get_setting('stile','tecnico')}, "
              f"note={db.get_setting('note_generali','')}, "
              f"extra={db.get_setting('prompt_extra','')}. "
              "Rispondi SOLO JSON su una riga: "
              '{"risposta":"...","azioni":{"prompt_extra":null,"note_generali":null,"stile":null},'
              '"attrezzatura_aggiungi":[],"attrezzatura_rimuovi":[]}')
    msgs = [{"role":m["role"],"content":m["content"]} for m in history]
    msgs.append({"role":"user","content":user_msg})
    r = client.messages.create(model=MODEL, max_tokens=500, system=system, messages=msgs)
    return _parse(r.content[0].text)
