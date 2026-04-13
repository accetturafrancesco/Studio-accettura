import json, base64, anthropic
import database as db

MODEL = "claude-sonnet-4-6"
client = anthropic.Anthropic()

BASE = """Sei il Dott. Francesco Accettura, fisioterapista domiciliare. Specializzazioni: ortopedia, neurologia, pediatria.
Trattamenti SEMPRE domiciliari. Attrezzatura: {attrezzatura}.
Prediligi corpo libero, resistenza manuale, loop band, cavigliere 1kg.
Sedute 45 minuti, max 3/settimana. Stile: {stile}. {note} {extra}
REGOLA ASSOLUTA: rispondi SOLO con JSON valido. Zero testo fuori dal JSON."""

def _base():
    att = ", ".join([a["nome"] for a in db.get_attrezzatura()])
    return BASE.format(
        attrezzatura=att,
        stile=db.get_setting("stile","tecnico"),
        note=db.get_setting("note_generali",""),
        extra=db.get_setting("prompt_extra",""),
    )

def _call(system, prompt, max_tokens=1500):
    r = client.messages.create(
        model=MODEL, max_tokens=max_tokens,
        system=system,
        messages=[{"role":"user","content":prompt}],
    )
    txt = r.content[0].text.strip().replace("```json","").replace("```","").strip()
    start = txt.find("{")
    end   = txt.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"Nessun JSON trovato: {txt[:200]}")
    return json.loads(txt[start:end+1])

def _imgs_to_content(imgs):
    content = []
    for img in imgs:
        if "," in img:
            header, data = img.split(",",1)
            mt = header.split(":")[1].split(";")[0]
        else:
            data, mt = img, "image/jpeg"
        content.append({"type":"image","source":{"type":"base64","media_type":mt,"data":data}})
    return content

# ── VALUTAZIONE ───────────────────────────────────────────────────────────────
def valuta_paziente(paz, imgs=[]):
    content = _imgs_to_content(imgs)
    content.append({"type":"text","text":f"""
Paziente: {paz['nome']} {paz['cognome']}, {paz['eta']} anni, {paz['sesso']}.
Condizione ({paz['cond_tipo']}): {paz['cond_desc']}

Rispondi SOLO con JSON, massimo 2 voci per lista:
{{"diagnosi_fisio":"...","diagnosi_differenziale":["..."],"strutture_coinvolte":["..."],"stadio":"acuto","flags":{{"red":["..."],"yellow":["..."],"black":[],"orange":[],"blue":[]}},"tests_consigliati":[{{"nome":"...","obiettivo":"...","procedura_passo_passo":["1.","2.","3."],"positivo_se":"...","significato_clinico":"..."}}],"suggerimento_sedute":{{"settimanali_consigliato":2,"totali_stimate":12,"rationale":"..."}},"obiettivi":{{"breve_termine":"...","medio_termine":"...","lungo_termine":"..."}}}}
"""})
    r = client.messages.create(
        model=MODEL, max_tokens=1500,
        system=_base(),
        messages=[{"role":"user","content":content}],
    )
    txt = r.content[0].text.strip().replace("```json","").replace("```","").strip()
    start = txt.find("{"); end = txt.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"Nessun JSON: {txt[:200]}")
    return json.loads(txt[start:end+1])

# ── SEDUTA: chiamata 1 — rivalutazione + fasi ─────────────────────────────────
def _genera_fasi(paz, piano, numero, totale, freq_sett, obs_prec, flags_txt):
    prompt = f"""Seduta {numero}/{totale}, {freq_sett}/sett. DOMICILIARE 45min.
Paziente: {paz['nome']} {paz['cognome']}, {paz['eta']}a, {paz['sesso']}.
Diagnosi: {piano.get('diagnosi_fisio','N/D')}. Stadio: {piano.get('stadio','N/D')}.
Flags: {flags_txt}. Obs precedente: {obs_prec or 'prima seduta'}.

Genera SOLO JSON. Max 3 esercizi per fase. Testo breve e conciso:
{{"rivalutazione":{{"durata_min":5,"checklist":["item1","item2"],"domande_chiave":["domanda1","domanda2"]}},"fase_passiva":{{"durata_min":10,"descrizione":"descrizione","esercizi":[{{"id":"p1","nome":"nome","tipo":"passivo","desc_tecnica":"per il fisioterapista","desc_paziente":"semplice per paziente","posizione":"posizione","serie":3,"ripetizioni":10,"durata_sec":null,"downscaling":"versione facile","attrezzatura":"corpo libero","youtube":"query","note_cliniche":"razionale"}}]}},"fase_attiva":{{"durata_min":25,"descrizione":"descrizione","esercizi":[{{"id":"a1","nome":"nome","tipo":"attivo","desc_tecnica":"per il fisioterapista","desc_paziente":"semplice","posizione":"posizione","serie":3,"ripetizioni":15,"durata_sec":null,"downscaling":"versione facile","attrezzatura":"corpo libero","youtube":"query","note_cliniche":"razionale"}}]}}}}"""
    return _call(_base(), prompt, max_tokens=2000)

# ── SEDUTA: chiamata 2 — HEP ──────────────────────────────────────────────────
def _genera_hep(paz, piano, numero):
    prompt = f"""HEP per {paz['nome']} {paz['cognome']}, seduta {numero}.
Diagnosi: {piano.get('diagnosi_fisio','N/D')}. Stadio: {piano.get('stadio','N/D')}.
Max 4 esercizi. Linguaggio SEMPLICE, nessun termine tecnico.

SOLO JSON:
{{"note_generali":"nota per il paziente","esercizi":[{{"id":"h1","nome":"nome esercizio","desc_paziente":"Spiegazione passo passo semplice, come per un non esperto.","posizione":"come mettersi","serie":2,"ripetizioni":10,"durata_sec":null,"frequenza":"ogni giorno","attrezzatura":"corpo libero","youtube":"query youtube"}}]}}"""
    return _call(_base(), prompt, max_tokens=1200)

# ── SEDUTA: funzione principale ───────────────────────────────────────────────
def genera_seduta(paziente, piano, numero, totale, freq_sett, obs_prec=""):
    flags = []
    for k, v in (piano.get("flags") or {}).items():
        if v: flags.append(f"[{k.upper()}] {', '.join(v)}")
    flags_txt = "; ".join(flags) or "nessuna"

    fasi = _genera_fasi(paziente, piano, numero, totale, freq_sett, obs_prec, flags_txt)
    hep  = _genera_hep(paziente, piano, numero)
    fasi["hep"] = hep
    return fasi

# ── CHAT IMPOSTAZIONI ─────────────────────────────────────────────────────────
def chat_impostazioni(history, user_msg):
    system = f"""Assistente configurazione per Dott. Accettura.
Stato: stile={db.get_setting('stile','tecnico')}, note={db.get_setting('note_generali','')}, extra={db.get_setting('prompt_extra','')}.
Rispondi SOLO JSON:
{{"risposta":"conferma","azioni":{{"prompt_extra":null,"note_generali":null,"stile":null}},"attrezzatura_aggiungi":[],"attrezzatura_rimuovi":[]}}"""
    msgs = [{"role":m["role"],"content":m["content"]} for m in history]
    msgs.append({"role":"user","content":user_msg})
    r = client.messages.create(model=MODEL, max_tokens=600, system=system, messages=msgs)
    txt = r.content[0].text.strip().replace("```json","").replace("```","").strip()
    start = txt.find("{"); end = txt.rfind("}")
    return json.loads(txt[start:end+1])
