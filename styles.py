MOBILE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;1,400&display=swap');

html, body, [class*="css"], .stApp { font-family: 'DM Sans', sans-serif !important; }

/* ── HEADER STUDIO ──────────────────────────────────────────────────── */
.studio-header {
    background: linear-gradient(135deg, #5B8C5A 0%, #3D6B3C 100%);
    border-radius: 14px; padding: 20px 24px 16px;
    margin-bottom: 20px; position: relative; overflow: hidden;
}
.studio-header::before {
    content:''; position:absolute; top:-20px; right:-20px;
    width:120px; height:120px; border-radius:50%;
    background: rgba(255,255,255,0.08);
}
.studio-header h1 {
    font-family: 'DM Serif Display', serif;
    color:white; font-size:1.6rem; margin:0; letter-spacing:.3px;
}
.studio-header p { color:rgba(255,255,255,.75); margin:3px 0 0; font-size:.85rem; }
.gold-accent { color: #D4AF5A; }

/* ── CARDS ──────────────────────────────────────────────────────────── */
.card {
    background: white; border-radius: 12px;
    border: 1px solid #C8DEC7; padding: 16px;
    margin-bottom: 10px; transition: box-shadow .2s;
}
.card:hover { box-shadow: 0 4px 16px rgba(91,140,90,.15); }
.card-sage {
    background: #EDF4EC; border-radius: 12px;
    border-left: 4px solid #5B8C5A; padding: 14px 16px;
    margin-bottom: 8px;
}
.card-gold {
    background: #FDF8EE; border-radius: 12px;
    border-left: 4px solid #8B6914; padding: 14px 16px;
    margin-bottom: 8px;
}
.card-red {
    background: #FEF2F2; border-radius: 12px;
    border-left: 4px solid #DC2626; padding: 12px 16px;
    margin-bottom: 8px;
}

/* ── BADGE FLAGS ────────────────────────────────────────────────────── */
.flag-red    { background:#FEE2E2; color:#991B1B; border-radius:6px; padding:2px 8px; font-size:.78rem; font-weight:600; display:inline-block; margin:2px; }
.flag-yellow { background:#FEF9C3; color:#854D0E; border-radius:6px; padding:2px 8px; font-size:.78rem; font-weight:600; display:inline-block; margin:2px; }
.flag-black  { background:#1F2937; color:white;   border-radius:6px; padding:2px 8px; font-size:.78rem; font-weight:600; display:inline-block; margin:2px; }
.flag-orange { background:#FED7AA; color:#9A3412; border-radius:6px; padding:2px 8px; font-size:.78rem; font-weight:600; display:inline-block; margin:2px; }
.flag-blue   { background:#DBEAFE; color:#1E3A8A; border-radius:6px; padding:2px 8px; font-size:.78rem; font-weight:600; display:inline-block; margin:2px; }

/* ── PATIENT CHIP ───────────────────────────────────────────────────── */
.patient-chip {
    display:flex; align-items:center; gap:12px;
    background:white; border-radius:12px; padding:14px 16px;
    border:1px solid #C8DEC7; margin-bottom:8px; cursor:pointer;
    transition: all .2s;
}
.patient-chip:hover { background:#EDF4EC; border-color:#5B8C5A; }
.patient-avatar {
    width:42px; height:42px; border-radius:50%;
    background:#5B8C5A; color:white; display:flex;
    align-items:center; justify-content:center;
    font-weight:700; font-size:1rem; flex-shrink:0;
}
.patient-info h4 { margin:0; font-size:.95rem; color:#1F2937; font-weight:600; }
.patient-info p  { margin:0; font-size:.8rem;  color:#6B7280; }

/* ── EXERCISE CARD ──────────────────────────────────────────────────── */
.ex-card {
    background:#FAFAF8; border-radius:10px; padding:14px;
    border:1px solid #E5E7EB; margin-bottom:8px;
}
.ex-card-header { display:flex; align-items:center; gap:10px; margin-bottom:8px; }
.ex-number {
    width:30px; height:30px; border-radius:50%;
    background:#5B8C5A; color:white;
    display:flex; align-items:center; justify-content:center;
    font-weight:700; font-size:.9rem; flex-shrink:0;
}
.ex-title { font-weight:600; color:#1F2937; font-size:.95rem; }
.ex-badge {
    background:#EDF4EC; color:#3D6B3C; border-radius:20px;
    padding:2px 10px; font-size:.78rem; font-weight:600; display:inline-block;
}
.downscale {
    background:#FDF8EE; border-radius:8px; padding:8px 12px;
    font-size:.82rem; color:#6B7280; margin-top:6px;
    border-left:3px solid #D4AF5A;
}

/* ── TIMER ──────────────────────────────────────────────────────────── */
.timer-display {
    font-family: 'DM Serif Display', serif;
    font-size:2.5rem; color:#5B8C5A; text-align:center;
}

/* ── MOBILE TOUCH TARGETS ───────────────────────────────────────────── */
.stButton > button {
    min-height: 48px !important;
    border-radius: 12px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
}
.stTextArea textarea, .stTextInput input, .stSelectbox select {
    font-size: 16px !important;
    border-radius: 10px !important;
}
/* Evita zoom automatico su iOS */
input, textarea, select { font-size: 16px !important; }

/* ── SIDEBAR MOBILE ─────────────────────────────────────────────────── */
@media (max-width: 768px) {
    .studio-header h1 { font-size: 1.3rem; }
    .studio-header { padding: 16px; }
    section[data-testid="stSidebar"] { min-width: 80vw !important; }
}

/* ── SEZIONE PLACEHOLDER ────────────────────────────────────────────── */
.empty-state {
    text-align:center; padding:40px 20px;
    color:#9CA3AF; font-size:.95rem;
}
.empty-state .icon { font-size:3rem; margin-bottom:12px; }
</style>
"""

FLAG_COLORS = {
    "red":    ("🔴", "Bandiere Rosse — Stop e invio al medico"),
    "yellow": ("🟡", "Bandiere Gialle — Fattori psicosociali"),
    "black":  ("⬛", "Bandiere Nere — Fattori lavorativi/assicurativi"),
    "orange": ("🟠", "Bandiere Arancioni — Disturbi psichiatrici"),
    "blue":   ("🔵", "Bandiere Blu — Percezione del lavoro"),
}
