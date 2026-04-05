import streamlit as st
import json
from datetime import datetime
import database as db
import claude_client as cc
import pdf_hep
from styles import MOBILE_CSS, FLAG_COLORS

st.set_page_config(page_title="Archivio Pazienti", page_icon="📂", layout="wide",
                   initial_sidebar_state="collapsed")
st.markdown(MOBILE_CSS, unsafe_allow_html=True)
db.init_db()

# ── LISTA PAZIENTI ─────────────────────────────────────────────────────────────
if "paziente_id" not in st.session_state:
    st.session_state.paziente_id = None
if "view" not in st.session_state:
    st.session_state.view = "lista"   # lista | scheda | seduta
if "seduta_id" not in st.session_state:
    st.session_state.seduta_id = None

# ──────────────────────────────────────────────────────────────────────────────
#  VISTA LISTA
# ──────────────────────────────────────────────────────────────────────────────
if st.session_state.view == "lista":
    st.markdown("""
    <div class="studio-header">
        <h1>📂 Archivio Pazienti</h1>
        <p>Seleziona un paziente per visualizzare la scheda</p>
    </div>""", unsafe_allow_html=True)

    col_nav1, col_nav2 = st.columns([1,4])
    with col_nav1:
        if st.button("← Home"):
            st.switch_page("app.py")
    with col_nav2:
        if st.button("➕ Nuovo Paziente", type="primary"):
            st.switch_page("pages/1_Nuovo_Paziente.py")

    st.markdown("---")
    pazienti = db.get_pazienti()
    if not pazienti:
        st.markdown("""<div class="empty-state"><div class="icon">📂</div>
        Nessun paziente in archivio.</div>""", unsafe_allow_html=True)
    else:
        cerca = st.text_input("🔍 Cerca paziente", placeholder="Nome o cognome...")
        if cerca:
            pazienti = [p for p in pazienti if cerca.lower() in
                        f"{p['nome']} {p['cognome']}".lower()]
        for p in pazienti:
            initials = f"{p['nome'][0]}{p['cognome'][0]}".upper()
            sedute = db.get_sedute(p["id"])
            n_sed  = len(sedute)
            ultima = sedute[-1]["data"][:10] if sedute else "—"
            col_p, col_b = st.columns([5, 1])
            with col_p:
                st.markdown(f"""
                <div class="patient-chip">
                    <div class="patient-avatar">{initials}</div>
                    <div class="patient-info">
                        <h4>{p['nome']} {p['cognome']}</h4>
                        <p>{p['eta']} anni · {p['sesso']} · {n_sed} sedut{'a' if n_sed==1 else 'e'} · Ultima: {ultima}</p>
                    </div>
                </div>""", unsafe_allow_html=True)
            with col_b:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Apri", key=f"p_{p['id']}", use_container_width=True):
                    st.session_state.paziente_id = p["id"]
                    st.session_state.view = "scheda"
                    st.rerun()

# ──────────────────────────────────────────────────────────────────────────────
#  VISTA SCHEDA PAZIENTE
# ──────────────────────────────────────────────────────────────────────────────
elif st.session_state.view == "scheda":
    pid = st.session_state.paziente_id
    p   = db.get_paziente(pid)
    if not p:
        st.error("Paziente non trovato.")
        st.session_state.view = "lista"
        st.rerun()

    piano  = json.loads(p["piano"]) if p["piano"] else {}
    flags  = json.loads(p["flags"]) if p["flags"] else {}
    sedute = db.get_sedute(pid)

    st.markdown(f"""
    <div class="studio-header">
        <h1>{p['nome']} {p['cognome']}</h1>
        <p>{p['eta']} anni · {p['sesso']} · {p['cond_tipo'].upper()}</p>
    </div>""", unsafe_allow_html=True)

    col_n1, col_n2, col_n3 = st.columns(3)
    with col_n1:
        if st.button("← Archivio"):
            st.session_state.view = "lista"
            st.rerun()
    with col_n2:
        if st.button("🏠 Home"):
            st.switch_page("app.py")

    # ── TABS ──────────────────────────────────────────────────────────────────
    tab1, tab2, tab3 = st.tabs(["🏥 Scheda clinica", "📋 Sedute", "📅 Pianifica"])

    # TAB 1 – scheda clinica
    with tab1:
        col_a, col_b = st.columns([3, 2])
        with col_a:
            st.markdown("#### Diagnosi fisioterapica")
            st.markdown(f'<div class="card-sage">{piano.get("diagnosi_fisio","—")}</div>',
                        unsafe_allow_html=True)

            if piano.get("diagnosi_differenziale"):
                st.markdown("**Diagnosi differenziale:**")
                for d in piano["diagnosi_differenziale"]:
                    st.markdown(f"- {d}")

            st.markdown(f"**Stadio:** `{piano.get('stadio','—').upper()}`")
            st.markdown(f"**Strutture coinvolte:** {', '.join(piano.get('strutture_coinvolte',[]))}")

            if piano.get("obiettivi"):
                ob = piano["obiettivi"]
                st.markdown("#### 🎯 Obiettivi")
                for label, key in [("Breve termine","breve_termine"),
                                    ("Medio termine","medio_termine"),
                                    ("Lungo termine","lungo_termine")]:
                    if ob.get(key):
                        st.markdown(f"**{label}:** {ob[key]}")

        with col_b:
            # Flags
            st.markdown("#### 🚩 Flags cliniche")
            for fk, (icon, label) in FLAG_COLORS.items():
                items = flags.get(fk, [])
                if items:
                    color_class = f"flag-{fk}"
                    st.markdown(f"**{icon} {label.split('—')[0]}**")
                    for it in items:
                        st.markdown(f'<span class="{color_class}">{it}</span>',
                                    unsafe_allow_html=True)
                    st.markdown("")

            # Tests
            if piano.get("tests_consigliati"):
                st.markdown("#### 🔬 Test consigliati")
                for t in piano["tests_consigliati"]:
                    with st.expander(f"📐 {t.get('nome','')}"):
                        st.markdown(f"**Obiettivo:** {t.get('obiettivo','')}")
                        st.markdown("**Procedura:**")
                        for i, step in enumerate(t.get("procedura_passo_passo",[]), 1):
                            st.markdown(f"{i}. {step}")
                        st.markdown(f"**Positivo se:** {t.get('positivo_se','')}")
                        st.markdown(f"**Significato:** {t.get('significato_clinico','')}")

            # Suggerimento sedute
            sg = piano.get("suggerimento_sedute", {})
            if sg:
                st.markdown("#### 📊 Suggerimento sedute")
                st.markdown(f'<div class="card-gold">Consigliato: <b>{sg.get("settimanali_consigliato",2)}/settimana</b> · '
                            f'<b>{sg.get("totali_stimate",10)} sedute totali</b><br><small>{sg.get("rationale","")}</small></div>',
                            unsafe_allow_html=True)

    # TAB 2 – sedute
    with tab2:
        if not sedute:
            st.markdown('<div class="empty-state"><div class="icon">📋</div>Nessuna seduta ancora.</div>',
                        unsafe_allow_html=True)
        else:
            for s in reversed(sedute):
                stato = "✅" if s["completata"] else "🔄"
                with st.expander(f"{stato} Seduta {s['numero']} — {s['data'][:10]}"):
                    prot = json.loads(s["protocollo"]) if s["protocollo"] else {}
                    if prot:
                        st.markdown(f"**Frequenza:** {s['freq_sett']}/sett · **Totale:** {s['totale']} sedute")
                    if s["osservazioni"]:
                        st.markdown(f"**Osservazioni:** {s['osservazioni']}")
                    if st.button("Riapri seduta", key=f"riapri_{s['id']}"):
                        st.session_state.seduta_id = s["id"]
                        st.session_state.view = "seduta"
                        st.rerun()

    # TAB 3 – nuova seduta
    with tab3:
        st.markdown("#### ➕ Avvia nuova seduta")
        sg = piano.get("suggerimento_sedute", {})
        rec = sg.get("settimanali_consigliato", 2)

        st.markdown("**Sedute settimanali — scegli tu:**")
        freq_sett = st.radio("", [1, 2, 3], index=rec-1, horizontal=True,
                             format_func=lambda x: f"{x} {'seduta' if x==1 else 'sedute'}/sett")

        tot_default = sg.get("totali_stimate", 10)
        totale = st.number_input("Sedute totali previste", min_value=1, max_value=60,
                                 value=tot_default)

        n_prossima = len(sedute) + 1
        obs_prec = ""
        if sedute:
            last = sedute[-1]
            obs_prec = last.get("osservazioni","")

        if st.button(f"🚀 Genera protocollo Seduta {n_prossima}", type="primary",
                     use_container_width=True):
            with st.spinner("🧠 Generazione protocollo in corso..."):
                try:
                    prot = cc.genera_seduta(
                        paziente=dict(nome=p["nome"], cognome=p["cognome"],
                                      eta=str(p["eta"]), sesso=p["sesso"]),
                        piano=piano, numero=n_prossima,
                        totale=int(totale), freq_sett=int(freq_sett),
                        obs_prec=obs_prec,
                    )
                    sid = db.insert_seduta(pid, n_prossima, int(freq_sett),
                                           int(totale), prot)
                    st.session_state.seduta_id = sid
                    st.session_state.view = "seduta"
                    st.rerun()
                except Exception as e:
                    st.error(f"Errore: {e}")

# ──────────────────────────────────────────────────────────────────────────────
#  VISTA SEDUTA
# ──────────────────────────────────────────────────────────────────────────────
elif st.session_state.view == "seduta":
    sid = st.session_state.seduta_id
    s   = db.get_seduta(sid)
    pid = s["paziente_id"]
    p   = db.get_paziente(pid)

    prot   = json.loads(s["protocollo"])   if s["protocollo"]   else {}
    checks = json.loads(s["check_esercizi"]) if s["check_esercizi"] else {}

    st.markdown(f"""
    <div class="studio-header">
        <h1>Seduta {s['numero']} — {p['nome']} {p['cognome']}</h1>
        <p>{s['data'][:10]} · {s['freq_sett']}/sett · {s['totale']} sedute totali · 45 min</p>
    </div>""", unsafe_allow_html=True)

    col_n1, col_n2 = st.columns(2)
    with col_n1:
        if st.button("← Scheda paziente"):
            st.session_state.view = "scheda"
            st.rerun()
    with col_n2:
        if st.button("🏠 Home"):
            st.switch_page("app.py")

    # ── RIVALUTAZIONE ─────────────────────────────────────────────────────────
    rv = prot.get("rivalutazione", {})
    with st.expander("⏱ RIVALUTAZIONE INIZIALE (5 min)", expanded=True):
        st.markdown(f"**Scale:** {', '.join(rv.get('scale',[]))}")
        st.markdown("**Domande chiave:**")
        for d in rv.get("domande_chiave", []):
            st.markdown(f"- {d}")
        st.markdown("**Checklist:**")
        for item in rv.get("checklist", []):
            checks[f"rv_{item}"] = st.checkbox(item, value=checks.get(f"rv_{item}", False),
                                                key=f"rv_{item}_{sid}")

    def _render_esercizi(esercizi, prefix):
        for ex in esercizi:
            eid = f"{prefix}_{ex['id']}"
            s_r = f"{ex.get('serie',0)}×{ex.get('ripetizioni',0)}" if ex.get('ripetizioni') \
                  else f"{ex.get('serie',0)}×{ex.get('durata_sec',0)}sec"
            att = ex.get("attrezzatura","")
            yt  = ex.get("youtube","")

            st.markdown(f"""
            <div class="ex-card">
                <div class="ex-card-header">
                    <div class="ex-number">{'✓' if checks.get(eid) else ex['id'][-1]}</div>
                    <div>
                        <div class="ex-title">{ex.get('nome','')}</div>
                        <span class="ex-badge">{s_r} · {att}</span>
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

            col_desc, col_check = st.columns([4,1])
            with col_desc:
                st.markdown(f"**Descrizione tecnica:** {ex.get('desc_tecnica','')}")
                st.markdown(f"*Posizione: {ex.get('posizione','')}*")
                if yt:
                    st.markdown(f"[▶ Guarda su YouTube](https://www.youtube.com/results?search_query={yt.replace(' ','+')})")
                # Downscaling
                if ex.get("downscaling"):
                    st.markdown(f"""
                    <div class="downscale">
                        ⬇ <b>Downscaling:</b> {ex['downscaling']}
                    </div>""", unsafe_allow_html=True)
            with col_check:
                st.markdown("<br>", unsafe_allow_html=True)
                done = st.checkbox("Fatto ✓", value=checks.get(eid, False),
                                   key=f"chk_{eid}_{sid}")
                checks[eid] = done

    # ── FASE PASSIVA ──────────────────────────────────────────────────────────
    fp = prot.get("fase_passiva", {})
    with st.expander(f"🤲 FASE PASSIVA ({fp.get('durata_min',10)} min)", expanded=True):
        if fp.get("descrizione"):
            st.markdown(f'<div class="card-sage">{fp["descrizione"]}</div>', unsafe_allow_html=True)
        _render_esercizi(fp.get("esercizi", []), "passiva")

    # ── FASE ATTIVA ───────────────────────────────────────────────────────────
    fa = prot.get("fase_attiva", {})
    with st.expander(f"💪 FASE ATTIVA ({fa.get('durata_min',25)} min)", expanded=True):
        if fa.get("descrizione"):
            st.markdown(f'<div class="card-sage">{fa["descrizione"]}</div>', unsafe_allow_html=True)
        _render_esercizi(fa.get("esercizi", []), "attiva")

    # ── HEP ───────────────────────────────────────────────────────────────────
    hep = prot.get("hep", {})
    with st.expander("🏠 HOME EXERCISE PROGRAM", expanded=False):
        if hep.get("note_generali"):
            st.markdown(f'<div class="card-gold">{hep["note_generali"]}</div>', unsafe_allow_html=True)
        for ex in hep.get("esercizi", []):
            s_r = f"{ex.get('serie',0)}×{ex.get('ripetizioni',0)}" if ex.get('ripetizioni') \
                  else f"{ex.get('serie',0)}×{ex.get('durata_sec',0)}sec"
            yt  = ex.get("youtube","")
            st.markdown(f"""
            <div class="ex-card">
                <div class="ex-title" style="margin-bottom:6px">{ex.get('nome','')}</div>
                <div style="font-size:.9rem;color:#374151">{ex.get('desc_paziente','')}</div>
                <div style="margin-top:8px"><span class="ex-badge">{s_r} · {ex.get('frequenza','')}</span></div>
            </div>""", unsafe_allow_html=True)
            if yt:
                st.markdown(f"[▶ YouTube](https://www.youtube.com/results?search_query={yt.replace(' ','+')})")

        # PDF HEP
        hep_ex = hep.get("esercizi", [])
        if hep_ex:
            st.markdown("---")
            if st.button("📄 Genera PDF esercizi per il paziente", use_container_width=True, type="primary"):
                pdf_bytes = pdf_hep.genera_hep_pdf(
                    nome=p["nome"], cognome=p["cognome"],
                    seduta_n=s["numero"],
                    esercizi=hep_ex,
                    note_generali=hep.get("note_generali",""),
                )
                st.download_button(
                    "⬇ Scarica PDF",
                    data=pdf_bytes,
                    file_name=f"HEP_{p['cognome']}_{p['nome']}_sed{s['numero']}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )

    # Salva checks
    db.update_seduta(sid, check_esercizi=checks)

    # ── OSSERVAZIONI FINALI ───────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### 📝 Osservazioni e note finali")
    obs = st.text_area("Inserisci le tue osservazioni cliniche sulla seduta",
                       value=s.get("osservazioni",""),
                       height=100,
                       placeholder="Es: paziente riferisce miglioramento NRS 7→5. ROM spalla +15°. "
                                   "Difficoltà nell'esercizio X → downscaling applicato. "
                                   "Motivazione buona. Prossima seduta: aumentare carico.")

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        if st.button("💾 Salva osservazioni", use_container_width=True):
            db.update_seduta(sid, osservazioni=obs)
            st.success("Salvato!")

    with col_s2:
        if st.button("✅ Completa seduta → Pianifica prossima", use_container_width=True, type="primary"):
            db.update_seduta(sid, osservazioni=obs, completata=True)
            # Appuntamento prossima seduta
            st.session_state.view = "scheda"
            st.success("Seduta completata! Vai su 'Pianifica' per la prossima.")
            st.rerun()
