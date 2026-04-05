import streamlit as st
import json
import database as db
import claude_client as cc
from styles import MOBILE_CSS

st.set_page_config(page_title="Impostazioni", page_icon="⚙️", layout="wide",
                   initial_sidebar_state="collapsed")
st.markdown(MOBILE_CSS, unsafe_allow_html=True)
db.init_db()

st.markdown("""
<div class="studio-header">
    <h1>⚙️ Impostazioni</h1>
    <p>Modifica il comportamento dell'assistente in linguaggio naturale</p>
</div>""", unsafe_allow_html=True)

if st.button("← Home"):
    st.switch_page("app.py")

tab1, tab2, tab3 = st.tabs(["💬 Chat modifiche", "🏋️ Attrezzatura", "📄 Impostazioni dirette"])

# ──────────────────────────────────────────────────────────────────────────────
#  TAB 1 — CHAT IMPOSTAZIONI
# ──────────────────────────────────────────────────────────────────────────────
with tab1:
    st.markdown("""
    <div class="card-sage">
        <b>Come funziona:</b> scrivi qui qualsiasi modifica vuoi apportare all'assistente
        in linguaggio normale. Esempi:<br>
        <ul style="margin-top:8px;margin-bottom:0">
        <li>"Ho comprato cavigliere da 2 kg, aggiungile all'attrezzatura"</li>
        <li>"Voglio che gli esercizi passivi siano sempre spiegati più lentamente"</li>
        <li>"Aggiungi fisioterapia respiratoria alle mie specializzazioni"</li>
        <li>"Non includere mai i link YouTube nelle sedute"</li>
        <li>"Quando il paziente è anziano, suggerisci sempre un downscaling"</li>
        </ul>
    </div>""", unsafe_allow_html=True)

    history = db.get_chat_settings()

    # Mostra conversazione
    for msg in history:
        if msg["role"] == "user":
            st.markdown(f"""
            <div class="card" style="border-left:4px solid #8B6914">
                <div style="font-size:.75rem;color:#8B6914;font-weight:600;margin-bottom:4px">TU</div>
                {msg['content']}
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="card-sage">
                <div style="font-size:.75rem;color:#3D6B3C;font-weight:600;margin-bottom:4px">🌿 ASSISTENTE</div>
                {msg['content']}
            </div>""", unsafe_allow_html=True)

    # Input
    user_msg = st.text_area("Scrivi la tua modifica",
                            placeholder="Es: aggiungi bastone da passeggio all'attrezzatura",
                            height=80, label_visibility="collapsed")
    col1, col2 = st.columns([3,1])
    with col1:
        invia = st.button("Invia", use_container_width=True, type="primary")
    with col2:
        if st.button("🗑 Reset chat", use_container_width=True):
            db.clear_chat_settings()
            st.rerun()

    if invia and user_msg.strip():
        with st.spinner("Elaborazione..."):
            try:
                resp = cc.chat_impostazioni(history, user_msg.strip())

                # Applica azioni
                azioni = resp.get("azioni", {})
                for k, v in azioni.items():
                    if v is not None:
                        db.set_setting(k, v)

                # Aggiungi attrezzatura
                for att in resp.get("attrezzatura_aggiungi", []):
                    db.insert_attrezzatura(att.get("nome",""), att.get("descrizione",""))

                # Rimuovi attrezzatura
                for nome_r in resp.get("attrezzatura_rimuovi", []):
                    atts = db.get_attrezzatura()
                    for a in atts:
                        if a["nome"].lower() == nome_r.lower():
                            db.delete_attrezzatura(a["id"])

                risposta_txt = resp.get("risposta", "Modifiche applicate.")
                db.append_chat_settings("user", user_msg.strip())
                db.append_chat_settings("assistant", risposta_txt)
                st.rerun()

            except Exception as e:
                st.error(f"Errore: {e}")

# ──────────────────────────────────────────────────────────────────────────────
#  TAB 2 — ATTREZZATURA
# ──────────────────────────────────────────────────────────────────────────────
with tab2:
    st.markdown("#### 🏋️ Attrezzatura disponibile")
    st.markdown("""
    <div class="card-gold">
        L'assistente usa questa lista per suggerire esercizi compatibili con
        quello che hai a disposizione. Aggiorna la lista man mano che acquisti nuovi strumenti.
    </div>""", unsafe_allow_html=True)

    atts = db.get_attrezzatura()
    for a in atts:
        col_a, col_d, col_del = st.columns([2, 4, 1])
        with col_a:
            st.markdown(f"**{a['nome']}**")
        with col_d:
            st.markdown(f"<span style='color:#6B7280;font-size:.9rem'>{a['descrizione']}</span>",
                        unsafe_allow_html=True)
        with col_del:
            if st.button("🗑", key=f"del_att_{a['id']}"):
                db.delete_attrezzatura(a["id"])
                st.rerun()

    st.markdown("---")
    st.markdown("#### ➕ Aggiungi attrezzatura")
    with st.form("new_att"):
        c1, c2 = st.columns(2)
        new_nome = c1.text_input("Nome", placeholder="Es: Pallone Bobath 65cm")
        new_desc = c2.text_input("Descrizione", placeholder="Per propriocezione e core stability")
        if st.form_submit_button("Aggiungi", use_container_width=True):
            if new_nome:
                db.insert_attrezzatura(new_nome, new_desc)
                st.success(f"✅ '{new_nome}' aggiunto! L'assistente lo userà nelle prossime sedute.")
                st.rerun()

# ──────────────────────────────────────────────────────────────────────────────
#  TAB 3 — IMPOSTAZIONI DIRETTE
# ──────────────────────────────────────────────────────────────────────────────
with tab3:
    st.markdown("#### 📄 Modifica diretta impostazioni")

    current_style = db.get_setting("stile", "tecnico e dettagliato")
    style = st.selectbox("Stile risposte cliniche",
                         ["tecnico e dettagliato", "sintetico", "molto dettagliato con evidenze"],
                         index=["tecnico e dettagliato","sintetico","molto dettagliato con evidenze"].index(current_style)
                               if current_style in ["tecnico e dettagliato","sintetico","molto dettagliato con evidenze"] else 0)

    note = st.text_area("Note generali per l'assistente",
                        value=db.get_setting("note_generali",""),
                        height=100,
                        placeholder="Es: i miei pazienti sono prevalentemente anziani over 70. "
                                    "Preferisco esercizi in posizione seduta o supina.")

    extra = st.text_area("Istruzioni aggiuntive al prompt",
                         value=db.get_setting("prompt_extra",""),
                         height=100,
                         placeholder="Es: includi sempre un esercizio di respirazione diaframmatica. "
                                     "Non usare terminologia latina nei report.")

    if st.button("💾 Salva impostazioni", use_container_width=True, type="primary"):
        db.set_setting("stile", style)
        db.set_setting("note_generali", note)
        db.set_setting("prompt_extra", extra)
        st.success("✅ Impostazioni salvate! Avranno effetto dalla prossima sessione.")

    st.markdown("---")
    st.markdown("#### 📊 Stato attuale")
    st.markdown(f"**Stile:** {db.get_setting('stile','—')}")
    st.markdown(f"**Note:** {db.get_setting('note_generali','—') or '(nessuna)'}")
    st.markdown(f"**Extra:** {db.get_setting('prompt_extra','—') or '(nessuno)'}")
    att_list = [a["nome"] for a in db.get_attrezzatura()]
    st.markdown(f"**Attrezzatura:** {', '.join(att_list)}")
