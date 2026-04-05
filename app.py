import streamlit as st
import database as db
from styles import MOBILE_CSS

st.set_page_config(
    page_title="Studio Accettura",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(MOBILE_CSS, unsafe_allow_html=True)
db.init_db()

# ── SESSION STATE ──────────────────────────────────────────────────────────────
if "paziente_id" not in st.session_state:
    st.session_state.paziente_id = None
if "seduta_id" not in st.session_state:
    st.session_state.seduta_id = None

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="studio-header">
    <h1><span class="gold-accent">✦</span> Studio Accettura</h1>
    <p>Fisioterapia Domiciliare · Ortopedia · Neurologia · Pediatria</p>
</div>
""", unsafe_allow_html=True)

# ── QUICK ACTIONS ─────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("👤  Nuovo Paziente", use_container_width=True, type="primary"):
        st.switch_page("pages/1_Nuovo_Paziente.py")
with col2:
    if st.button("📂  Archivio", use_container_width=True):
        st.switch_page("pages/2_Archivio.py")
with col3:
    if st.button("📅  Agenda", use_container_width=True):
        st.switch_page("pages/3_Agenda.py")
with col4:
    if st.button("⚙️  Impostazioni", use_container_width=True):
        st.switch_page("pages/4_Impostazioni.py")

st.markdown("<br>", unsafe_allow_html=True)

# ── PAZIENTI RECENTI ──────────────────────────────────────────────────────────
pazienti = db.get_pazienti()

col_a, col_b = st.columns([2, 1])

with col_a:
    st.markdown("### 👥 Pazienti")
    if not pazienti:
        st.markdown("""
        <div class="empty-state">
            <div class="icon">🌿</div>
            Nessun paziente ancora.<br>Inizia con <b>Nuovo Paziente</b>.
        </div>""", unsafe_allow_html=True)
    else:
        for p in pazienti:
            initials = f"{p['nome'][0]}{p['cognome'][0]}".upper()
            sedute = db.get_sedute(p["id"])
            n_sed = len(sedute)
            ultima = sedute[-1]["data"][:10] if sedute else "—"
            col_p, col_btn = st.columns([4, 1])
            with col_p:
                st.markdown(f"""
                <div class="patient-chip">
                    <div class="patient-avatar">{initials}</div>
                    <div class="patient-info">
                        <h4>{p['nome']} {p['cognome']}</h4>
                        <p>{p['eta']} anni · {p['sesso']} · {n_sed} sedut{'a' if n_sed==1 else 'e'} · Ultima: {ultima}</p>
                    </div>
                </div>""", unsafe_allow_html=True)
            with col_btn:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Apri →", key=f"open_{p['id']}", use_container_width=True):
                    st.session_state.paziente_id = p["id"]
                    st.switch_page("pages/2_Archivio.py")

with col_b:
    st.markdown("### 📊 Riepilogo")
    tot_pz = len(pazienti)
    tot_sed = sum(len(db.get_sedute(p["id"])) for p in pazienti)
    sed_oggi = 0  # da agenda
    from datetime import date
    app_oggi = [a for a in db.get_appuntamenti()
                if a["data_ora"] and a["data_ora"][:10] == str(date.today())]

    st.markdown(f"""
    <div class="card-sage">
        <div style="font-size:.8rem;color:#6B7280;font-weight:600;text-transform:uppercase;letter-spacing:.5px">Pazienti attivi</div>
        <div style="font-size:2rem;font-weight:700;color:#3D6B3C">{tot_pz}</div>
    </div>
    <div class="card-sage">
        <div style="font-size:.8rem;color:#6B7280;font-weight:600;text-transform:uppercase;letter-spacing:.5px">Sedute totali</div>
        <div style="font-size:2rem;font-weight:700;color:#3D6B3C">{tot_sed}</div>
    </div>
    <div class="card-gold">
        <div style="font-size:.8rem;color:#6B7280;font-weight:600;text-transform:uppercase;letter-spacing:.5px">Appuntamenti oggi</div>
        <div style="font-size:2rem;font-weight:700;color:#8B6914">{len(app_oggi)}</div>
    </div>""", unsafe_allow_html=True)

    if app_oggi:
        st.markdown("**Oggi:**")
        for a in app_oggi:
            st.markdown(f"- {a['data_ora'][11:16]} · {a.get('nome','')} {a.get('cognome','')}")
