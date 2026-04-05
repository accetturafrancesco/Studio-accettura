import streamlit as st
import base64, json
import database as db
import claude_client as cc
from styles import MOBILE_CSS

st.set_page_config(page_title="Nuovo Paziente", page_icon="👤", layout="wide",
                   initial_sidebar_state="collapsed")
st.markdown(MOBILE_CSS, unsafe_allow_html=True)
db.init_db()

st.markdown("""
<div class="studio-header">
    <h1>👤 Nuovo Paziente</h1>
    <p>Inserisci i dati anagrafici e la condizione clinica</p>
</div>""", unsafe_allow_html=True)

if st.button("← Home"):
    st.switch_page("app.py")

st.markdown("---")

# ── FORM ──────────────────────────────────────────────────────────────────────
with st.form("intake", clear_on_submit=False):
    st.markdown("#### 📋 Anagrafica")
    c1, c2 = st.columns(2)
    nome     = c1.text_input("Nome *", placeholder="Mario")
    cognome  = c2.text_input("Cognome *", placeholder="Rossi")
    c3, c4, c5 = st.columns(3)
    eta      = c3.number_input("Età *", min_value=0, max_value=120, value=50)
    sesso    = c4.selectbox("Sesso *", ["M", "F", "Altro"])
    telefono = c5.text_input("Telefono", placeholder="3xx xxxxxxx")

    st.markdown("---")
    st.markdown("#### 🏥 Condizione Clinica")
    cond_tipo = st.radio(
        "Tipo di presentazione",
        ["Patologia/diagnosi nota", "Sintomatologia senza diagnosi"],
        horizontal=True,
    )

    if cond_tipo == "Patologia/diagnosi nota":
        cond_desc = st.text_area(
            "Diagnosi e condizione clinica",
            height=140,
            placeholder="Es: Esiti ictus ischemico sx 06/2024, emiparesi dx. RMN: lesione capsula interna. "
                        "Attualmente cammina con bastone, ROM spalla dx ridotto, mano destra poco funzionale...",
        )
        st.markdown("##### 🖼 Documenti diagnostici (opzionale)")
        uploaded = st.file_uploader(
            "Carica immagini RMN, TAC, referti (JPG, PNG, PDF)",
            type=["jpg","jpeg","png"],
            accept_multiple_files=True,
        )
    else:
        cond_desc = st.text_area(
            "Descrivi i sintomi",
            height=140,
            placeholder="Es: Dolore alla spalla destra da 3 settimane. Iniziato senza un trauma preciso. "
                        "Peggiora alzando il braccio sopra la testa e di notte. NRS 6/10. "
                        "Nessun intorpidimento. Lavoro sedentario al computer...",
        )
        uploaded = []

    submitted = st.form_submit_button("🔍 Analizza e crea scheda paziente",
                                      use_container_width=True, type="primary")

# ── ELABORAZIONE ──────────────────────────────────────────────────────────────
if submitted:
    if not nome or not cognome or not cond_desc:
        st.error("Compila Nome, Cognome e la descrizione clinica.")
        st.stop()

    # Converti immagini in base64
    imgs_b64 = []
    for f in (uploaded or []):
        data = base64.b64encode(f.read()).decode()
        mt = "image/jpeg" if f.type in ["image/jpg","image/jpeg"] else "image/png"
        imgs_b64.append(f"data:{mt};base64,{data}")

    with st.spinner("🧠 Il Dott. Accettura sta analizzando il quadro clinico..."):
        paziente_dict = dict(
            nome=nome, cognome=cognome, eta=str(eta), sesso=sesso,
            cond_tipo="nota" if "nota" in cond_tipo else "sconosciuta",
            cond_desc=cond_desc,
        )
        try:
            piano = cc.valuta_paziente(paziente_dict, imgs_b64)
            flags = piano.get("flags", {})
        except Exception as e:
            st.error(f"Errore Claude API: {e}")
            st.stop()

    pid = db.insert_paziente(
        nome=nome, cognome=cognome, eta=eta, sesso=sesso, telefono=telefono,
        cond_tipo=paziente_dict["cond_tipo"], cond_desc=cond_desc,
        immagini=imgs_b64, piano=piano, flags=flags,
    )

    st.success(f"✅ Scheda creata per {nome} {cognome}")
    st.session_state.paziente_id = pid

    # Anteprima valutazione
    with st.expander("📄 Valutazione clinica generata", expanded=True):
        st.markdown(f"**Diagnosi fisioterapica:** {piano.get('diagnosi_fisio','')}")
        if piano.get("diagnosi_differenziale"):
            st.markdown("**Diagnosi differenziale:** " + " · ".join(piano["diagnosi_differenziale"]))
        st.markdown(f"**Stadio:** {piano.get('stadio','').upper()}")

        # Flags
        flags_d = piano.get("flags", {})
        flag_labels = {"red":"🔴 Rosse","yellow":"🟡 Gialle","black":"⬛ Nere","orange":"🟠 Arancioni","blue":"🔵 Blu"}
        for fk, fl in flag_labels.items():
            items = flags_d.get(fk, [])
            if items:
                st.markdown(f"**Bandiere {fl}:**")
                for it in items:
                    st.markdown(f"  - {it}")

        # Suggerimento sedute
        sg = piano.get("suggerimento_sedute", {})
        if sg:
            st.markdown(f"**Sedute consigliate:** {sg.get('settimanali_consigliato',2)}/settimana "
                        f"· {sg.get('totali_stimate',10)} totali")
            st.markdown(f"*{sg.get('rationale','')}*")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("→ Apri scheda paziente", use_container_width=True, type="primary"):
            st.switch_page("pages/2_Archivio.py")
    with col2:
        if st.button("← Home", use_container_width=True):
            st.switch_page("app.py")
