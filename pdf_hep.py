"""
PDF HEP – Esercizi a casa per il paziente
Palette sage green (ricerca di mercato 2024-2025: benessere, riabilitazione, movimento naturale)
"""
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, PageBreak
)

# ── PALETTE sage green ─────────────────────────────────────────────────────────
SAGE        = colors.HexColor("#5B8C5A")
SAGE_DARK   = colors.HexColor("#3D6B3C")
SAGE_LIGHT  = colors.HexColor("#EDF4EC")
SAGE_PALE   = colors.HexColor("#F5FAF5")
GOLD        = colors.HexColor("#8B6914")
GOLD_LIGHT  = colors.HexColor("#FDF8EE")
CHARCOAL    = colors.HexColor("#1F2937")
GREY        = colors.HexColor("#6B7280")
WHITE       = colors.white
IVORY       = colors.HexColor("#FAFAF8")

def _styles():
    return {
        "h_name":  ParagraphStyle("h_name",  fontSize=11, textColor=WHITE,
                                  fontName="Helvetica-Bold", spaceAfter=1),
        "h_spec":  ParagraphStyle("h_spec",  fontSize=8,  textColor=colors.HexColor("#D1EAD0"),
                                  fontName="Helvetica", spaceAfter=0),
        "h_title": ParagraphStyle("h_title", fontSize=18, textColor=SAGE_DARK,
                                  fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=2),
        "h_sub":   ParagraphStyle("h_sub",   fontSize=10, textColor=GREY,
                                  fontName="Helvetica", alignment=TA_CENTER, spaceAfter=0),
        "section": ParagraphStyle("section", fontSize=11, textColor=SAGE_DARK,
                                  fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=3),
        "body":    ParagraphStyle("body",    fontSize=10, textColor=CHARCOAL,
                                  fontName="Helvetica", leading=15, alignment=TA_JUSTIFY, spaceAfter=4),
        "step_n":  ParagraphStyle("step_n",  fontSize=15, textColor=WHITE,
                                  fontName="Helvetica-Bold", alignment=TA_CENTER),
        "step_t":  ParagraphStyle("step_t",  fontSize=11, textColor=SAGE_DARK,
                                  fontName="Helvetica-Bold", spaceAfter=2),
        "step_b":  ParagraphStyle("step_b",  fontSize=10, textColor=CHARCOAL,
                                  fontName="Helvetica", leading=14, spaceAfter=3),
        "badge":   ParagraphStyle("badge",   fontSize=9,  textColor=SAGE_DARK,
                                  fontName="Helvetica-Bold", alignment=TA_CENTER),
        "note":    ParagraphStyle("note",    fontSize=8,  textColor=GREY,
                                  fontName="Helvetica-Oblique", spaceAfter=2),
        "footer":  ParagraphStyle("footer",  fontSize=7.5,textColor=GREY,
                                  fontName="Helvetica", alignment=TA_CENTER),
        "footer_b":ParagraphStyle("footer_b",fontSize=7.5,textColor=SAGE_DARK,
                                  fontName="Helvetica-Bold", alignment=TA_CENTER),
    }

def _header_table(S, nome_pz, cognome_pz, seduta_n, data_str):
    """Intestazione a due colonne: dottore a sx, titolo al centro."""
    dottore = Table([[
        Paragraph("Dott. Francesco Accettura", S["h_name"]),
        Paragraph("Fisioterapista · Ortopedia · Neurologia · Pediatria", S["h_spec"]),
        Paragraph("Tel. 342 661 4157", S["h_spec"]),
    ]], colWidths=[170*mm])
    dottore.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(-1,-1), SAGE),
        ("TOPPADDING",    (0,0),(-1,-1), 10),
        ("BOTTOMPADDING", (0,0),(-1,-1), 10),
        ("LEFTPADDING",   (0,0),(-1,-1), 12),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
    ]))
    return dottore

def genera_hep_pdf(nome: str, cognome: str, seduta_n: int,
                   esercizi: list, note_generali: str = "") -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            topMargin=14*mm, bottomMargin=20*mm,
                            leftMargin=18*mm, rightMargin=18*mm)
    S = _styles()
    story = []
    data_str = datetime.now().strftime("%d/%m/%Y")

    # ── INTESTAZIONE ─────────────────────────────────────────────────────────
    header = Table([[
        Paragraph("Dott. Francesco Accettura", S["h_name"]),
        Paragraph("Fisioterapista  ·  Ortopedia · Neurologia · Pediatria", S["h_spec"]),
        Paragraph("Tel. 342 661 4157", S["h_spec"]),
    ]], colWidths=[170*mm])
    header.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), SAGE),
        ("TOPPADDING",    (0,0),(-1,-1), 12),
        ("BOTTOMPADDING", (0,0),(-1,-1), 12),
        ("LEFTPADDING",   (0,0),(-1,-1), 14),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
    ]))
    story.append(header)
    story.append(Spacer(1, 8))

    # ── TITOLO ───────────────────────────────────────────────────────────────
    story.append(Paragraph("ESERCIZI A CASA", S["h_title"]))
    story.append(Paragraph(f"{nome} {cognome}  ·  Seduta {seduta_n}  ·  {data_str}", S["h_sub"]))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1.5, color=SAGE, spaceAfter=10))

    # ── NOTE GENERALI ─────────────────────────────────────────────────────────
    if note_generali:
        box = Table([[Paragraph(note_generali, S["body"])]],
                    colWidths=[170*mm])
        box.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), GOLD_LIGHT),
            ("BOX",           (0,0),(-1,-1), 0.8, GOLD),
            ("TOPPADDING",    (0,0),(-1,-1), 8),
            ("BOTTOMPADDING", (0,0),(-1,-1), 8),
            ("LEFTPADDING",   (0,0),(-1,-1), 10),
            ("RIGHTPADDING",  (0,0),(-1,-1), 10),
        ]))
        story.append(box)
        story.append(Spacer(1, 8))

    # ── ESERCIZI ─────────────────────────────────────────────────────────────
    for i, ex in enumerate(esercizi, 1):
        # Numero colorato
        num_cell = Table([[Paragraph(str(i), S["step_n"])]],
                         colWidths=[10*mm], rowHeights=[10*mm])
        num_cell.setStyle(TableStyle([
            ("BACKGROUND", (0,0),(-1,-1), SAGE),
            ("VALIGN",     (0,0),(-1,-1), "MIDDLE"),
            ("TOPPADDING",    (0,0),(-1,-1), 0),
            ("BOTTOMPADDING", (0,0),(-1,-1), 0),
        ]))

        # Badge serie×rip
        s = ex.get("serie", 0)
        r = ex.get("ripetizioni", 0)
        d = ex.get("durata_sec", None)
        freq = ex.get("frequenza","")
        if d:
            badge_txt = f"{s} serie × {d} sec  ·  {freq}"
        elif r:
            badge_txt = f"{s} serie × {r} rip  ·  {freq}"
        else:
            badge_txt = freq

        badge = Table([[Paragraph(badge_txt, S["badge"])]],
                      colWidths=[80*mm], rowHeights=[8*mm])
        badge.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), SAGE_LIGHT),
            ("BOX",           (0,0),(-1,-1), 0.5, SAGE),
            ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
            ("TOPPADDING",    (0,0),(-1,-1), 0),
            ("BOTTOMPADDING", (0,0),(-1,-1), 0),
        ]))

        # Posizione
        pos_txt = ex.get("posizione","")
        pos_para = Paragraph(f"<i>Posizione: {pos_txt}</i>", S["note"]) if pos_txt else Spacer(1,1)

        # Corpo esercizio (dx del numero)
        corpo = [
            Paragraph(ex.get("nome","Esercizio"), S["step_t"]),
            Paragraph(ex.get("desc_paziente",""), S["step_b"]),
            pos_para,
            badge,
        ]
        corpo_table = Table([[c] for c in corpo], colWidths=[155*mm])
        corpo_table.setStyle(TableStyle([
            ("TOPPADDING",    (0,0),(-1,-1), 0),
            ("BOTTOMPADDING", (0,0),(-1,-1), 2),
            ("LEFTPADDING",   (0,0),(-1,-1), 0),
        ]))

        row = Table([[num_cell, corpo_table]], colWidths=[14*mm, 156*mm])
        row.setStyle(TableStyle([
            ("VALIGN",      (0,0),(-1,-1), "TOP"),
            ("LEFTPADDING", (1,0),(1,0),   8),
            ("TOPPADDING",  (0,0),(-1,-1), 0),
        ]))

        # Card esercizio
        card = Table([[row]], colWidths=[170*mm])
        card.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), IVORY if i % 2 == 0 else SAGE_PALE),
            ("BOX",           (0,0),(-1,-1), 0.5, colors.HexColor("#C8DEC7")),
            ("TOPPADDING",    (0,0),(-1,-1), 10),
            ("BOTTOMPADDING", (0,0),(-1,-1), 10),
            ("LEFTPADDING",   (0,0),(-1,-1), 6),
            ("RIGHTPADDING",  (0,0),(-1,-1), 8),
        ]))
        story.append(KeepTogether(card))
        story.append(Spacer(1, 6))

    # ── PIEDE DI PAGINA ───────────────────────────────────────────────────────
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=0.8, color=SAGE, spaceAfter=6))
    footer_data = [[
        Paragraph("Dott. Francesco Accettura", S["footer_b"]),
        Paragraph("Fisioterapista", S["footer"]),
        Paragraph("Tel. 342 661 4157", S["footer"]),
        Paragraph("Documento personale del paziente", S["footer"]),
    ]]
    ft = Table(footer_data, colWidths=[50*mm, 40*mm, 40*mm, 40*mm])
    ft.setStyle(TableStyle([
        ("VALIGN",      (0,0),(-1,-1), "TOP"),
        ("LEFTPADDING", (0,0),(-1,-1), 2),
    ]))
    story.append(ft)

    doc.build(story)
    return buf.getvalue()
