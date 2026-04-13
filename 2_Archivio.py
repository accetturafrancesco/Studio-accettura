import streamlit as st
from datetime import datetime, date, timedelta
import database as db
from styles import MOBILE_CSS

try:
    from icalendar import Calendar, Event
    ICS_OK = True
except ImportError:
    ICS_OK = False

st.set_page_config(page_title="Agenda", page_icon="📅", layout="wide",
                   initial_sidebar_state="collapsed")
st.markdown(MOBILE_CSS, unsafe_allow_html=True)
db.init_db()

st.markdown("""
<div class="studio-header">
    <h1>📅 Agenda</h1>
    <p>Martedì · Giovedì 8:30–12:00 · Sabato 8:30–12:00 / 16:00+</p>
</div>""", unsafe_allow_html=True)

if st.button("← Home"):
    st.switch_page("app.py")

# Orari di lavoro
SLOT_MATTINA    = ["08:30","09:15","10:00","10:45","11:15"]
SLOT_POMERIGGIO = ["16:00","16:45","17:30","18:15","19:00"]
GIORNI_LAVORO   = {1: "Martedì", 3: "Giovedì", 5: "Sabato"}  # weekday()

pazienti = db.get_pazienti()
pz_map   = {p["id"]: f"{p['nome']} {p['cognome']}" for p in pazienti}

tab1, tab2, tab3 = st.tabs(["📆 Settimana corrente", "➕ Nuovo appuntamento", "📋 Tutti"])

# ── SETTIMANA CORRENTE ────────────────────────────────────────────────────────
with tab1:
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    apps   = db.get_appuntamenti()

    st.markdown(f"**Settimana dal {monday.strftime('%d/%m')} al {(monday+timedelta(6)).strftime('%d/%m/%Y')}**")

    for offset, (wd, nome_g) in enumerate([(1,"Martedì"),(3,"Giovedì"),(5,"Sabato")]):
        giorno = monday + timedelta(days=wd)
        apps_g = [a for a in apps if a["data_ora"] and a["data_ora"][:10] == str(giorno)]

        is_today = (giorno == today)
        bg = "#EDF4EC" if is_today else "white"
        border = "#5B8C5A" if is_today else "#E5E7EB"

        st.markdown(f"""
        <div style="background:{bg};border-radius:12px;border:1.5px solid {border};
                    padding:14px;margin-bottom:10px;">
            <div style="font-weight:700;color:#3D6B3C;font-size:1rem">
                {'📍 ' if is_today else ''}{nome_g} {giorno.strftime('%d/%m')}
            </div>""", unsafe_allow_html=True)

        if apps_g:
            for a in sorted(apps_g, key=lambda x: x["data_ora"]):
                ora = a["data_ora"][11:16] if len(a["data_ora"]) > 10 else "—"
                pz  = f"{a.get('nome','')} {a.get('cognome','')}".strip() or a.get("titolo","")
                note = a.get("note","")
                col_a, col_del = st.columns([5,1])
                with col_a:
                    st.markdown(f"""
                    <div style="display:flex;gap:12px;align-items:center;padding:8px 0;border-bottom:1px solid #F0F0F0">
                        <div style="background:#5B8C5A;color:white;border-radius:8px;
                                    padding:4px 10px;font-weight:600;font-size:.85rem">{ora}</div>
                        <div>
                            <div style="font-weight:600;font-size:.9rem">{pz}</div>
                            {f'<div style="font-size:.8rem;color:#6B7280">{note}</div>' if note else ''}
                        </div>
                    </div>""", unsafe_allow_html=True)
                with col_del:
                    if st.button("🗑", key=f"del_{a['id']}"):
                        db.delete_appuntamento(a["id"])
                        st.rerun()
        else:
            st.markdown('<div style="color:#9CA3AF;font-size:.85rem;padding:4px 0">Nessun appuntamento</div>',
                        unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

# ── NUOVO APPUNTAMENTO ────────────────────────────────────────────────────────
with tab2:
    st.markdown("#### ➕ Aggiungi appuntamento")

    with st.form("new_app"):
        pz_sel = st.selectbox("Paziente", ["—"] + list(pz_map.values()))

        col1, col2 = st.columns(2)
        data_sel = col1.date_input("Data", value=date.today())
        wd = data_sel.weekday()

        if wd in GIORNI_LAVORO:
            turno = col2.radio("Turno", ["Mattina","Pomeriggio"] if wd == 5 else ["Mattina"],
                               horizontal=True)
            slots = SLOT_POMERIGGIO if turno == "Pomeriggio" else SLOT_MATTINA
        else:
            st.warning(f"⚠ {data_sel.strftime('%A')} non è un giorno lavorativo standard. "
                       "Puoi comunque aggiungere l'appuntamento.")
            slots = SLOT_MATTINA + SLOT_POMERIGGIO

        ora_sel = st.selectbox("Orario", slots)
        note_ap = st.text_input("Note (opzionale)", placeholder="Es: 45 min + 20 min spostamento")

        if st.form_submit_button("Aggiungi", use_container_width=True, type="primary"):
            data_ora = f"{data_sel} {ora_sel}:00"
            pid_sel  = None
            for pid_k, nome_v in pz_map.items():
                if nome_v == pz_sel:
                    pid_sel = pid_k
                    break
            db.insert_appuntamento(
                paziente_id=pid_sel,
                titolo=pz_sel if pz_sel != "—" else "Appuntamento",
                data_ora=data_ora,
                durata_min=45,
                note=note_ap,
            )
            st.success("Appuntamento aggiunto!")
            st.rerun()

# ── TUTTI + EXPORT ICS ───────────────────────────────────────────────────────
with tab3:
    all_apps = db.get_appuntamenti()
    st.markdown(f"**{len(all_apps)} appuntamenti totali**")

    if all_apps:
        for a in sorted(all_apps, key=lambda x: x.get("data_ora",""), reverse=True):
            dt   = a.get("data_ora","—")[:16]
            pz   = f"{a.get('nome','')} {a.get('cognome','')}".strip() or a.get("titolo","")
            note = a.get("note","")
            st.markdown(f"""
            <div class="card">
                <div style="display:flex;gap:12px;align-items:center">
                    <div style="background:#EDF4EC;border-radius:8px;padding:4px 10px;
                                font-weight:600;color:#3D6B3C;font-size:.85rem">{dt}</div>
                    <div>
                        <div style="font-weight:600">{pz}</div>
                        {f'<div style="font-size:.8rem;color:#6B7280">{note}</div>' if note else ''}
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

        # Export ICS
        if ICS_OK:
            st.markdown("---")
            if st.button("📥 Esporta tutto in formato Calendario (.ics)", use_container_width=True):
                cal = Calendar()
                cal.add("prodid", "-//Studio Accettura//IT")
                cal.add("version", "2.0")
                cal.add("calscale", "GREGORIAN")
                for a in all_apps:
                    try:
                        ev = Event()
                        dt_obj = datetime.strptime(a["data_ora"], "%Y-%m-%d %H:%M:%S")
                        ev.add("summary", f"Fisio – {a.get('nome','')} {a.get('cognome','')}")
                        ev.add("dtstart", dt_obj)
                        ev.add("dtend",   dt_obj + timedelta(minutes=int(a.get("durata_min",45))))
                        if a.get("note"):
                            ev.add("description", a["note"])
                        cal.add_component(ev)
                    except Exception:
                        pass
                st.download_button(
                    "⬇ Scarica .ics (importa in Google/Apple Calendar)",
                    data=cal.to_ical(),
                    file_name="agenda_accettura.ics",
                    mime="text/calendar",
                    use_container_width=True,
                )
        else:
            st.info("Installa icalendar per l'export: pip install icalendar")
    else:
        st.markdown('<div class="empty-state"><div class="icon">📅</div>Nessun appuntamento.</div>',
                    unsafe_allow_html=True)
