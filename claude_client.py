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
            f"{db.get_setting('note_generali','')} {db.get_setting('prompt_extra','')}")

def _ask_text(prompt, max_tokens=800):
    """Chiede a Claude testo libero e lo restituisce."""
    r = client.messages.create(
        model=MODEL, max_tokens=max_tokens,
        system=_base(),
        messages=[{"role":"user","content":prompt}],
    )
    return r.content[0].text.strip()

def _parse_list(txt):
    """Estrae righe di testo come lista pulita."""
    lines = []
    for line in txt.splitlines():
        line = re.sub(r'^[-*•\d+\.\)]+\s*','', line).strip()
        if line and len(line) > 3:
            lines.append(line)
    return lines[:6]

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

def _safe_get(d, *keys, default=""):
    """Naviga dizionario annidato in modo sicuro."""
    for k in keys:
        if isinstance(d, dict):
            d = d.get(k, default)
        else:
            return default
    return d if d is not None else default

# ─────────────────────────────────────────────────────────────────────────────
# VALUTAZIONE — costruiamo il dizionario campo per campo
# ─────────────────────────────────────────────────────────────────────────────
def valuta_paziente(paz, imgs=[]):
    ctx = (f"Paziente: {paz['nome']} {paz['cognome']}, {paz['eta']}a, {paz['sesso']}. "
           f"Condizione ({paz['cond_tipo']}): {paz['cond_desc']}")

    diagnosi = _ask_text(
        f"{ctx}\nScrivimi in UNA SOLA FRASE la diagnosi fisioterapica.", 150)

    diff = _parse_list(_ask_text(
        f"{ctx}\nDiagnosi fisioterapica: {diagnosi}\n"
        "Elenca 2-3 diagnosi differenziali, una per riga, solo il nome.", 200))

    strutture = _parse_list(_ask_text(
        f"{ctx}\nElenca le strutture anatomiche coinvolte, una per riga.", 150))

    stadio_txt = _ask_text(
        f"{ctx}\nLo stadio è: acuto, subacuto o cronico? Rispondi con UNA PAROLA sola.", 20)
    stadio = "subacuto"
    for s in ["acuto","subacuto","cronico"]:
        if s in stadio_txt.lower():
            stadio = s; break

    flags_red = _parse_list(_ask_text(
        f"{ctx}\nElenca le RED FLAGS presenti o da monitorare, una per riga. "
        "Se non ce ne sono scrivi: nessuna.", 200))
    flags_yel = _parse_list(_ask_text(
        f"{ctx}\nElenca le YELLOW FLAGS (psicosociali) rilevanti, una per riga. "
        "Se non ce ne sono scrivi: nessuna.", 200))

    test_nome = _ask_text(
        f"{ctx}\nQual è il test clinico più importante da eseguire? Solo il nome.", 80)
    test_proc = _parse_list(_ask_text(
        f"Come si esegue il test {test_nome} per {ctx}? "
        "Elenca i passaggi numerati, uno per riga.", 300))
    test_pos = _ask_text(
        f"Il test {test_nome} è positivo quando:", 100)
    test_sig = _ask_text(
        f"Significato clinico del test {test_nome} positivo in una frase:", 100)

    sett_txt = _ask_text(
        f"{ctx}\nQuante sedute a settimana consigli? Rispondi con UN NUMERO (1, 2 o 3).", 20)
    sett = 2
    for n in [1,2,3]:
        if str(n) in sett_txt:
            sett = n; break

    tot_txt = _ask_text(
        f"{ctx}\nQuante sedute totali stimi necessarie? Rispondi con UN NUMERO.", 20)
    try:
        tot = int(re.search(r'\d+', tot_txt).group())
        tot = max(4, min(tot, 40))
    except Exception:
        tot = 12

    rationale = _ask_text(
        f"{ctx}\nIn una frase: perché {sett} sedute/sett e {tot} totali?", 150)

    obj_b = _ask_text(f"{ctx}\nObiettivo a breve termine (una frase):", 100)
    obj_m = _ask_text(f"{ctx}\nObiettivo a medio termine (una frase):", 100)
    obj_l = _ask_text(f"{ctx}\nObiettivo a lungo termine (una frase):", 100)

    def clean_flags(lst):
        return [f for f in lst if f.lower() != "nessuna"]

    return {
        "diagnosi_fisio": diagnosi,
        "diagnosi_differenziale": diff,
        "strutture_coinvolte": strutture,
        "stadio": stadio,
        "flags": {
            "red": clean_flags(flags_red),
            "yellow": clean_flags(flags_yel),
            "black": [], "orange": [], "blue": []
        },
        "tests_consigliati": [{
            "nome": test_nome,
            "obiettivo": f"Valutare {test_nome}",
            "procedura_passo_passo": test_proc,
            "positivo_se": test_pos,
            "significato_clinico": test_sig,
        }],
        "suggerimento_sedute": {
            "settimanali_consigliato": sett,
            "totali_stimate": tot,
            "rationale": rationale,
        },
        "obiettivi": {
            "breve_termine": obj_b,
            "medio_termine": obj_m,
            "lungo_termine": obj_l,
        },
    }

# ─────────────────────────────────────────────────────────────────────────────
# ESERCIZIO — costruisce un dict esercizio da testo libero
# ─────────────────────────────────────────────────────────────────────────────
def _build_esercizio(eid, diagnosi, stadio, tipo, flags_txt, n_esercizio):
    nome = _ask_text(
        f"Diagnosi: {diagnosi}, stadio: {stadio}, tipo esercizio: {tipo}, "
        f"flags: {flags_txt}, domiciliare. "
        f"Dammi il nome dell'esercizio n.{n_esercizio} adatto. Solo il nome, max 5 parole.", 60)

    posizione = _ask_text(
        f"Esercizio: {nome}. Descrivi la posizione di partenza in una frase.", 80)

    desc_tecnica = _ask_text(
        f"Esercizio: {nome}, posizione: {posizione}. "
        "Descrivi l'esecuzione tecnica in 2-3 frasi per il fisioterapista.", 200)

    desc_paziente = _ask_text(
        f"Esercizio: {nome}. Spiega come farlo al paziente in modo molto semplice, "
        "senza termini tecnici, in 2-3 frasi.", 200)

    downscaling = _ask_text(
        f"Esercizio: {nome}. Come semplificarlo se il paziente non riesce? Una frase.", 100)

    youtube = _ask_text(
        f"Query di ricerca YouTube per trovare un video dell'esercizio: {nome}. "
        "Solo la query, max 5 parole.", 50)

    note = _ask_text(
        f"Esercizio: {nome} per {diagnosi}. Razionale clinico in una frase.", 100)

    serie = 3 if "attiv" in tipo else 2
    rip   = 15 if "attiv" in tipo else 10

    return {
        "id": eid,
        "nome": nome,
        "tipo": tipo,
        "desc_tecnica": desc_tecnica,
        "desc_paziente": desc_paziente,
        "posizione": posizione,
        "serie": serie,
        "ripetizioni": rip,
        "durata_sec": None,
        "downscaling": downscaling,
        "attrezzatura": "corpo libero",
        "youtube": youtube,
        "note_cliniche": note,
    }

def _build_hep_esercizio(eid, diagnosi, stadio, n):
    nome = _ask_text(
        f"Diagnosi: {diagnosi}, stadio: {stadio}. "
        f"Esercizio HEP n.{n} per casa, domiciliare, semplice. Solo il nome.", 60)

    desc = _ask_text(
        f"Esercizio per casa: {nome}. "
        "Spiega come farlo passo per passo in modo molto semplice, "
        "come se lo spiegassi a qualcuno che non ha mai fatto fisioterapia. "
        "Usa frasi brevi e chiare, niente termini tecnici.", 250)

    posizione = _ask_text(
        f"Esercizio: {nome}. Posizione di partenza in una frase semplice.", 60)

    youtube = _ask_text(
        f"Query YouTube per trovare video: {nome}. Max 5 parole.", 50)

    return {
        "id": eid,
        "nome": nome,
        "desc_paziente": desc,
        "posizione": posizione,
        "serie": 2,
        "ripetizioni": 10,
        "durata_sec": None,
        "frequenza": "ogni giorno",
        "attrezzatura": "corpo libero",
        "youtube": youtube,
    }

# ─────────────────────────────────────────────────────────────────────────────
# GENERA SEDUTA
# ─────────────────────────────────────────────────────────────────────────────
def genera_seduta(paziente, piano, numero, totale, freq_sett, obs_prec=""):
    diagnosi = piano.get("diagnosi_fisio","")
    stadio   = piano.get("stadio","subacuto")
    flags    = []
    for k, v in (piano.get("flags") or {}).items():
        if v: flags.append(f"[{k.upper()}] {', '.join(v)}")
    flags_txt = "; ".join(flags) or "nessuna"

    # Rivalutazione
    checklist = _parse_list(_ask_text(
        f"Rivalutazione inizio seduta per {paziente['nome']}, diagnosi: {diagnosi}. "
        f"Obs precedente: {obs_prec or 'prima seduta'}. "
        "Elenca 3 cose da verificare, una per riga.", 200))
    domande = _parse_list(_ask_text(
        f"Rivalutazione per {paziente['nome']}, diagnosi: {diagnosi}. "
        "Elenca 2 domande chiave da fare al paziente, una per riga.", 150))

    rivalutazione = {
        "durata_min": 5,
        "checklist": checklist,
        "domande_chiave": domande,
    }

    # Fase passiva
    desc_passiva = _ask_text(
        f"Descrivi in una frase la fase passiva della seduta per {diagnosi}, stadio {stadio}.", 100)
    es_passivi = [_build_esercizio(f"p{i+1}", diagnosi, stadio, "passivo", flags_txt, i+1)
                  for i in range(2)]

    fase_passiva = {
        "durata_min": 10,
        "descrizione": desc_passiva,
        "esercizi": es_passivi,
    }

    # Fase attiva
    desc_attiva = _ask_text(
        f"Descrivi in una frase la fase attiva della seduta per {diagnosi}, stadio {stadio}.", 100)
    es_attivi = [_build_esercizio(f"a{i+1}", diagnosi, stadio, "attivo", flags_txt, i+1)
                 for i in range(3)]

    fase_attiva = {
        "durata_min": 25,
        "descrizione": desc_attiva,
        "esercizi": es_attivi,
    }

    # HEP
    note_hep = _ask_text(
        f"Nota generale per il paziente {paziente['nome']} sull'HEP per {diagnosi}. "
        "Una frase incoraggiante e semplice.", 100)
    es_hep = [_build_hep_esercizio(f"h{i+1}", diagnosi, stadio, i+1) for i in range(3)]

    hep = {
        "note_generali": note_hep,
        "esercizi": es_hep,
    }

    return {
        "rivalutazione": rivalutazione,
        "fase_passiva":  fase_passiva,
        "fase_attiva":   fase_attiva,
        "hep":           hep,
    }

# ─────────────────────────────────────────────────────────────────────────────
# CHAT IMPOSTAZIONI
# ─────────────────────────────────────────────────────────────────────────────
def chat_impostazioni(history, user_msg):
    msgs = [{"role":m["role"],"content":m["content"]} for m in history]
    msgs.append({"role":"user","content":user_msg})

    risposta = _ask_text(
        f"L'utente dice: {user_msg}\n"
        "Sei l'assistente di configurazione del Dott. Accettura. "
        "Rispondi in modo amichevole confermando cosa hai capito che vuole cambiare.", 150)

    # Determina azioni
    att_add = []
    att_del = []
    prompt_extra = None
    note_gen = None
    stile = None

    lower = user_msg.lower()
    if any(w in lower for w in ["aggiungi","comprato","ho preso","nuovo"]):
        nome_att = _ask_text(
            f"L'utente dice: {user_msg}\n"
            "Qual è il nome dell'attrezzatura da aggiungere? Solo il nome, max 4 parole.", 50)
        desc_att = _ask_text(
            f"Attrezzatura: {nome_att}. Descrizione in una frase.", 80)
        att_add = [{"nome": nome_att, "descrizione": desc_att}]

    if any(w in lower for w in ["togli","rimuovi","elimina"]):
        nome_del = _ask_text(
            f"L'utente dice: {user_msg}\n"
            "Qual è il nome dell'attrezzatura da rimuovere? Solo il nome.", 50)
        att_del = [nome_del]

    if any(w in lower for w in ["stile","risposte","breve","dettagliato","sintetico"]):
        stile = _ask_text(
            f"L'utente dice: {user_msg}\n"
            "Quale stile preferisce? Rispondi con una di queste opzioni esatte: "
            "'tecnico', 'sintetico', 'molto dettagliato con evidenze'.", 50).strip()

    if any(w in lower for w in ["nota","ricorda","sempre","mai","preferisco"]):
        prompt_extra = user_msg

    return {
        "risposta": risposta,
        "azioni": {
            "prompt_extra": prompt_extra,
            "note_generali": note_gen,
            "stile": stile,
        },
        "attrezzatura_aggiungi": att_add,
        "attrezzatura_rimuovi": att_del,
    }
