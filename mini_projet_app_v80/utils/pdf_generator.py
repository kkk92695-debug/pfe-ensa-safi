from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io, os
from datetime import datetime

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
LOGO_PATH  = os.path.join(ASSETS_DIR, "logo_ensa.jpg")

# Couleurs ENSA
DARK_BLUE  = colors.HexColor('#0f2557')
MED_BLUE   = colors.HexColor('#1a56a0')
LIGHT_BLUE = colors.HexColor('#dbeafe')
GREEN      = colors.HexColor('#16a34a')
LIGHT_GREEN= colors.HexColor('#dcfce7')
GOLD       = colors.HexColor('#d97706')
GRAY_BG    = colors.HexColor('#f8fafc')
GRAY_LINE  = colors.HexColor('#e2e8f0')

# Filières — abréviations uniquement
FILIERES = ["GIIA","GTR","GATE","GPMA","GINDUS","GMSI"]


def generate_recu_pdf(data: dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=1.8*cm, leftMargin=1.8*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm
    )
    styles = getSampleStyleSheet()

    def style(name, **kw):
        s = ParagraphStyle(name, parent=styles['Normal'], **kw)
        return s

    center_dark  = style('cd',  fontSize=11, fontName='Helvetica-Bold',  textColor=DARK_BLUE,  alignment=TA_CENTER)
    center_med   = style('cm',  fontSize=9,  fontName='Helvetica',       textColor=MED_BLUE,   alignment=TA_CENTER)
    center_gray  = style('cg',  fontSize=8,  fontName='Helvetica-Oblique',textColor=colors.grey,alignment=TA_CENTER)
    section_head = style('sh',  fontSize=9,  fontName='Helvetica-Bold',  textColor=MED_BLUE,   spaceBefore=8, spaceAfter=4)
    footer_s     = style('ft',  fontSize=7.5,fontName='Helvetica-Oblique',textColor=colors.grey,alignment=TA_CENTER)

    story = []
    num_ordre      = data.get('num_ordre', 'N/A')
    date_soumission= data.get('date_soumission', datetime.now().strftime("%Y-%m-%d %H:%M"))
    filiere_code   = data.get('filiere', '')

    # ── HEADER : logo + texte ───────────────────────────────────────────────
    header_data = []
    if os.path.exists(LOGO_PATH):
        logo_cell = Image(LOGO_PATH, width=4.5*cm, height=1.8*cm)
    else:
        logo_cell = Paragraph("ENSA", center_dark)

    text_cell = [
        Paragraph("École Nationale des Sciences Appliquées de Safi", center_dark),
        Paragraph("Université Cadi Ayyad", center_med),
    ]
    header_data = [[logo_cell, text_cell]]
    header_table = Table(header_data, colWidths=[5*cm, 12.6*cm])
    header_table.setStyle(TableStyle([
        ('VALIGN',  (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN',   (0,0), (0,0),   'LEFT'),
        ('ALIGN',   (1,0), (1,0),   'CENTER'),
        ('LEFTPADDING',  (0,0), (0,0), 0),
        ('RIGHTPADDING', (1,0), (1,0), 0),
        ('BOTTOMPADDING',(0,0),(-1,-1), 4),
    ]))
    story.append(header_table)
    story.append(HRFlowable(width="100%", thickness=2.5, color=DARK_BLUE))
    story.append(Spacer(1, 0.3*cm))

    # ── TITRE RECU ─────────────────────────────────────────────────────────
    story.append(Paragraph("REÇU DE DÉPÔT — RAPPORT DE FIN D'ÉTUDES (PFE)", center_dark))
    story.append(Paragraph("Bibliothèque Électronique des Rapports Étudiants", center_med))
    story.append(Spacer(1, 0.3*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=LIGHT_BLUE))
    story.append(Spacer(1, 0.3*cm))

    # ── BADGE N° ORDRE ─────────────────────────────────────────────────────
    badge_data = [[
        Paragraph(f"<b>N° d'ordre : {num_ordre}</b>", style('bn', fontSize=12, fontName='Helvetica-Bold', textColor=colors.white, alignment=TA_CENTER)),
        Paragraph(f"Date : {date_soumission}", style('bd', fontSize=9, fontName='Helvetica', textColor=colors.white, alignment=TA_CENTER)),
        Paragraph("✅ VALIDÉ", style('bv', fontSize=10, fontName='Helvetica-Bold', textColor=colors.white, alignment=TA_CENTER)),
    ]]
    badge_table = Table(badge_data, colWidths=[6*cm, 7*cm, 4.6*cm])
    badge_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (1,0), DARK_BLUE),
        ('BACKGROUND', (2,0), (2,0), GREEN),
        ('ROUNDEDCORNERS', [6]),
        ('ALIGN',  (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING',(0,0), (-1,-1), 10),
        ('GRID',   (0,0), (-1,-1), 0, colors.white),
    ]))
    story.append(badge_table)
    story.append(Spacer(1, 0.4*cm))

    # ── SECTION ÉTUDIANT ───────────────────────────────────────────────────
    story.append(Paragraph("▌ INFORMATIONS DE L'ÉTUDIANT", section_head))
    etudiant_rows = [
        ["Nom & Prénom", f"{data.get('nom','')} {data.get('prenom','')}"],
        ["Email institutionnel", data.get('email','')],
        ["Filière", filiere_code],
        ["Année universitaire", str(data.get('annee',''))],
    ]
    etudiant_table = Table(etudiant_rows, colWidths=[4.5*cm, 13.1*cm])
    etudiant_table.setStyle(TableStyle([
        ('FONTNAME',    (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME',    (1,0), (1,-1), 'Helvetica'),
        ('FONTSIZE',    (0,0), (-1,-1), 9),
        ('TEXTCOLOR',   (0,0), (0,-1), DARK_BLUE),
        ('ALIGN',       (0,0), (-1,-1), 'LEFT'),
        ('VALIGN',      (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING',     (0,0), (-1,-1), 7),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [GRAY_BG, colors.white]),
        ('GRID',        (0,0), (-1,-1), 0.5, GRAY_LINE),
        ('ROUNDEDCORNERS', [4]),
    ]))
    story.append(etudiant_table)
    story.append(Spacer(1, 0.3*cm))

    # ── SECTION RAPPORT ────────────────────────────────────────────────────
    story.append(Paragraph("▌ INFORMATIONS DU RAPPORT PFE", section_head))
    rapport_rows = [
        ["Intitulé du rapport", data.get('intitule_rapport','')],
        ["Encadrant",           data.get('encadrant','')],
        ["Co-encadrant",        data.get('co_encadrant','') or 'Aucun'],
        ["Lieu de stage",       data.get('lieu_stage','')],
        ["Date de dépôt",       str(data.get('date_depot_secretariat',''))],
        ["Rapport PDF",         "✅ Déposé dans la bibliothèque électronique"],
    ]
    rapport_table = Table(rapport_rows, colWidths=[4.5*cm, 13.1*cm])
    rapport_table.setStyle(TableStyle([
        ('FONTNAME',    (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME',    (1,0), (1,-1), 'Helvetica'),
        ('FONTSIZE',    (0,0), (-1,-1), 9),
        ('TEXTCOLOR',   (0,0), (0,-1), DARK_BLUE),
        ('TEXTCOLOR',   (1,5), (1,5),  GREEN),
        ('ALIGN',       (0,0), (-1,-1), 'LEFT'),
        ('VALIGN',      (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING',     (0,0), (-1,-1), 7),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [GRAY_BG, colors.white]),
        ('GRID',        (0,0), (-1,-1), 0.5, GRAY_LINE),
    ]))
    story.append(rapport_table)
    story.append(Spacer(1, 0.4*cm))

    # ── BANNIÈRE CONFIRMATION ──────────────────────────────────────────────
    confirm_data = [[
        Paragraph(
            "✅  Ce reçu confirme que le rapport PFE a bien été soumis dans la bibliothèque électronique de l'ENSA Safi."
            "  Veuillez le présenter au secrétariat du département comme preuve officielle de dépôt.",
            style('conf', fontSize=9, fontName='Helvetica-Bold', textColor=colors.HexColor('#14532d'), alignment=TA_LEFT)
        )
    ]]
    confirm_table = Table(confirm_data, colWidths=[17.6*cm])
    confirm_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), LIGHT_GREEN),
        ('GRID',       (0,0), (-1,-1), 1, GREEN),
        ('PADDING',    (0,0), (-1,-1), 10),
        ('ROUNDEDCORNERS', [6]),
    ]))
    story.append(confirm_table)
    story.append(Spacer(1, 0.6*cm))

    # ── SIGNATURES ─────────────────────────────────────────────────────────
    sig_data = [
        [Paragraph("<b>Signature de l'étudiant(e)</b>", style('sl', fontSize=9, fontName='Helvetica-Bold', textColor=DARK_BLUE, alignment=TA_CENTER)),
         Paragraph("", style('sl2', fontSize=9)),
         Paragraph("<b>Cachet du département</b>", style('sl3', fontSize=9, fontName='Helvetica-Bold', textColor=DARK_BLUE, alignment=TA_CENTER))],
        [Paragraph("\n\n\n_______________________", style('sig1', fontSize=9, alignment=TA_CENTER)),
         Paragraph("", style('sig2', fontSize=9)),
         Paragraph("\n\n\n_______________________", style('sig3', fontSize=9, alignment=TA_CENTER))],
    ]
    sig_table = Table(sig_data, colWidths=[6*cm, 5.6*cm, 6*cm])
    sig_table.setStyle(TableStyle([
        ('ALIGN',  (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
        ('FONTSIZE',(0,0),(-1,-1), 9),
    ]))
    story.append(sig_table)

    # ── FOOTER ─────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRAY_LINE))
    story.append(Spacer(1, 0.15*cm))
    story.append(Paragraph(
        f"ENSA Safi — Système de Gestion PFE  |  Document généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}  |  Réf. PFE-{num_ordre}-{datetime.now().year}",
        footer_s
    ))

    doc.build(story)
    return buffer.getvalue()
