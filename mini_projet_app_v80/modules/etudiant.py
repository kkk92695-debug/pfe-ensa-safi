import streamlit as st
from utils.data_manager import add_student
from utils.pdf_generator import generate_recu_pdf
from datetime import datetime
import re

FILIERE_LABELS = {
    "GINDUS": "GINDUS",
    "GPMA":   "GPMA",
    "GIIA":   "GIIA",
    "GTR":    "GTR",
    "GATE":   "GATE",
    "GMSI":   "GMSI",
}

def validate_uca_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+\-]+@uca\.ac\.ma$'
    return bool(re.match(pattern, email.strip().lower()))


def show_etudiant_page():

    # ════════════════════════════════════════════════════════════════════════
    # CSS
    # ════════════════════════════════════════════════════════════════════════
    st.markdown("""
    <style>
    #MainMenu, footer, header { visibility: hidden; }
    .stApp { background: #f0f4f8; }

    /* ── Cards ─────────────────────────────────────────── */
    .s-card {
        background: #fff;
        border-radius: 16px;
        padding: 1.6rem 1.8rem;
        margin-bottom: 1.1rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 6px rgba(0,0,0,0.06);
    }
    .s-title {
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: #1a56a0;
        margin-bottom: 1.1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e8f0fb;
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }

    /* ── Labels & inputs ────────────────────────────────── */
    label,
    .stTextInput label,
    .stSelectbox label,
    .stTextArea label {
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        color: #374151 !important;
    }
    .stTextInput input,
    .stTextArea textarea {
        border-radius: 9px !important;
        border: 1.5px solid #d1d5db !important;
        font-size: 0.9rem !important;
        transition: border-color .2s !important;
    }
    .stTextInput input:focus,
    .stTextArea textarea:focus {
        border-color: #1a56a0 !important;
        box-shadow: 0 0 0 3px rgba(26,86,160,.1) !important;
    }

    /* ── Steps bar ──────────────────────────────────────── */
    .steps-bar {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 1.5rem;
        padding: 0 0.5rem;
    }
    .s-step {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 5px;
        flex: 1;
        max-width: 120px;
    }
    .s-circle {
        width: 34px; height: 34px;
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-weight: 700; font-size: 0.82rem;
        background: #e2e8f0; color: #9ca3af;
        border: 2px solid #e2e8f0;
        transition: all .3s;
    }
    .s-circle.active {
        background: #1a56a0; color: #fff;
        border-color: #1a56a0;
        box-shadow: 0 0 0 4px rgba(26,86,160,.15);
    }
    .s-circle.done {
        background: #16a34a; color: #fff;
        border-color: #16a34a;
    }
    .s-lbl {
        font-size: 0.63rem; font-weight: 700;
        color: #9ca3af; text-align: center;
        text-transform: uppercase; letter-spacing: .05em;
    }
    .s-lbl.active { color: #1a56a0; }
    .s-lbl.done   { color: #16a34a; }
    .s-line {
        flex: 1; height: 2px;
        background: #e2e8f0;
        margin-bottom: 20px;
    }
    .s-line.done { background: #16a34a; }

    /* ── Drag-and-drop file uploader ────────────────────── */
    [data-testid="stFileUploader"] {
        border: 2.5px dashed #1a56a0 !important;
        border-radius: 14px !important;
        background: linear-gradient(135deg,#f0f6ff,#e8f0fb) !important;
        transition: all .25s !important;
        overflow: hidden !important;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: #2563eb !important;
        background: linear-gradient(135deg,#dbeafe,#eff6ff) !important;
        box-shadow: 0 0 0 4px rgba(37,99,235,.12) !important;
    }
    [data-testid="stFileUploaderDropzone"] {
        background: transparent !important;
        border: none !important;
        padding: 2rem 1.5rem !important;
        text-align: center !important;
    }
    [data-testid="stFileUploaderDropzoneInstructions"] {
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        gap: 4px !important;
    }
    [data-testid="stFileUploaderDropzoneInstructions"]::before {
        content: "📄";
        font-size: 2.8rem;
        display: block;
        margin-bottom: 6px;
    }
    [data-testid="stFileUploaderDropzoneInstructions"] span {
        font-size: 1rem !important;
        font-weight: 700 !important;
        color: #1a56a0 !important;
    }
    [data-testid="stFileUploaderDropzoneInstructions"] small {
        font-size: 0.78rem !important;
        color: #64748b !important;
    }
    [data-testid="stFileUploaderDropzone"] button {
        background: linear-gradient(135deg,#1a56a0,#2563eb) !important;
        color: #fff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: .45rem 1.4rem !important;
        cursor: pointer !important;
        margin-top: 10px !important;
        box-shadow: 0 2px 8px rgba(26,86,160,.3) !important;
    }

    /* ── Primary button ─────────────────────────────────── */
    div[data-testid="stButton"] > button[kind="primary"] {
        background: linear-gradient(135deg,#1a56a0,#2563eb) !important;
        border: none !important;
        border-radius: 10px !important;
        font-size: .97rem !important;
        font-weight: 700 !important;
        padding: .7rem 2rem !important;
        box-shadow: 0 4px 14px rgba(26,86,160,.3) !important;
        letter-spacing: .02em !important;
        transition: all .2s !important;
    }
    div[data-testid="stButton"] > button[kind="primary"]:hover {
        opacity: .92 !important;
        transform: translateY(-1px) !important;
    }
    div[data-testid="stButton"] > button[kind="secondary"] {
        background: #fff !important;
        border: 1.5px solid #1a56a0 !important;
        color: #1a56a0 !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
    }

    /* ── Receipt rows ───────────────────────────────────── */
    .r-row {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        padding: .5rem 0;
        border-bottom: 1px solid #e2e8f0;
        font-size: .88rem;
        gap: 1rem;
    }
    .r-row:last-child { border: none; }
    .r-key { color: #374151; font-weight: 600; white-space: nowrap; }
    .r-val { color: #0f172a; font-weight: 500; text-align: right; }
    </style>
    """, unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════════
    # HEADER
    # ════════════════════════════════════════════════════════════════════════
    st.markdown("""
    <div style="background:linear-gradient(135deg,#0f2557 0%,#1a56a0 55%,#2563eb 100%);
                padding:1.8rem 2rem 1.4rem;border-radius:18px;color:#fff;
                margin-bottom:1.5rem;box-shadow:0 8px 32px rgba(26,86,160,.25);">
        <div style="display:flex;align-items:center;gap:14px;margin-bottom:.4rem;">
            <div style="width:48px;height:48px;background:rgba(255,255,255,.15);
                        border-radius:12px;display:flex;align-items:center;
                        justify-content:center;font-size:1.6rem;">📚</div>
            <div>
                <div style="font-size:.7rem;font-weight:600;letter-spacing:.12em;
                            opacity:.75;text-transform:uppercase;">
                    Université Cadi Ayyad — ENSA Safi</div>
                <h2 style="margin:0;font-size:1.35rem;font-weight:700;">
                    Dépôt du Rapport PFE</h2>
            </div>
        </div>
        <p style="margin:0;opacity:.82;font-size:.84rem;padding-left:62px;">
            Bibliothèque Électronique des Rapports Étudiants</p>
    </div>
    """, unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════════
    # STEPS INDICATOR
    # ════════════════════════════════════════════════════════════════════════
    step = st.session_state.get("form_step", 1)
    c1 = "done"   if step > 1 else ("active" if step == 1 else "")
    c2 = "done"   if step > 2 else ("active" if step == 2 else "")
    c3 = "active" if step == 3 else ""
    l1 = "done"   if step > 1 else ""
    l2 = "done"   if step > 2 else ""

    st.markdown(f"""
    <div class="steps-bar">
      <div class="s-step">
        <div class="s-circle {c1}">{'✓' if step > 1 else '1'}</div>
        <div class="s-lbl {c1}">Identité</div>
      </div>
      <div class="s-line {l1}"></div>
      <div class="s-step">
        <div class="s-circle {c2}">{'✓' if step > 2 else '2'}</div>
        <div class="s-lbl {c2}">Rapport & PDF</div>
      </div>
      <div class="s-line {l2}"></div>
      <div class="s-step">
        <div class="s-circle {c3}">3</div>
        <div class="s-lbl {c3}">Reçu</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════════
    # ÉTAPE 3 — REÇU
    # ════════════════════════════════════════════════════════════════════════
    if step == 3:
        _show_receipt()
        return

    # ════════════════════════════════════════════════════════════════════════
    # ÉTAPE 1 — IDENTITÉ
    # ════════════════════════════════════════════════════════════════════════
    if step == 1:
        st.markdown('<div class="s-card">', unsafe_allow_html=True)
        st.markdown('<div class="s-title">👤 Informations personnelles</div>', unsafe_allow_html=True)

        ca, cb = st.columns(2)
        with ca:
            st.text_input("Nom *", placeholder="AMRANI",
                          key="f_nom",
                          value=st.session_state.get("f_nom", ""))
            st.text_input("Prénom *", placeholder="Mohamed",
                          key="f_prenom",
                          value=st.session_state.get("f_prenom", ""))
        with cb:
            st.text_input("Email institutionnel *", placeholder="m.amrani@uca.ac.ma",
                          key="f_email",
                          value=st.session_state.get("f_email", ""))
            st.markdown("""
            <div style="font-size:.75rem;color:#6b7280;margin-top:-8px;margin-bottom:4px;">
              Format obligatoire : <span style="color:#1a56a0;font-weight:600;">...@uca.ac.ma</span>
            </div>""", unsafe_allow_html=True)

        cc, cd = st.columns(2)
        fil_opts = list(FILIERE_LABELS.values())
        fil_keys = list(FILIERE_LABELS.keys())
        prev_fil = st.session_state.get("f_filiere", fil_keys[0])
        prev_idx = fil_keys.index(prev_fil) if prev_fil in fil_keys else 0
        with cc:
            st.selectbox("Filière *", fil_opts, index=prev_idx, key="f_filiere_sel")
        with cd:
            cur_y = datetime.now().year
            le    = cur_y + 1 if datetime.now().month >= 6 else cur_y
            annees = [f"{y}-{y+1}" for y in range(le - 1, 2019, -1)]
            prev_an = st.session_state.get("f_annee", annees[0])
            pan_idx = annees.index(prev_an) if prev_an in annees else 0
            st.selectbox("Année universitaire *", annees, index=pan_idx, key="f_annee_sel")

        st.markdown('</div>', unsafe_allow_html=True)

        # ── Bouton Continuer ───────────────────────────────────────────────
        _, btn_col, _ = st.columns([1, 2, 1])
        with btn_col:
            if st.button("Continuer →", type="primary",
                         use_container_width=True, key="btn_go2"):
                nom_v    = st.session_state.get("f_nom", "").strip()
                prenom_v = st.session_state.get("f_prenom", "").strip()
                email_v  = st.session_state.get("f_email", "").strip()
                errs = []
                if not nom_v:    errs.append("Le nom est obligatoire.")
                if not prenom_v: errs.append("Le prénom est obligatoire.")
                if not email_v:
                    errs.append("L'email est obligatoire.")
                elif not validate_uca_email(email_v):
                    errs.append("L'email doit se terminer par @uca.ac.ma.")
                if errs:
                    for e in errs:
                        st.error(e)
                else:
                    st.session_state["form_step"] = 2
                    st.rerun()
        return

    # ════════════════════════════════════════════════════════════════════════
    # ÉTAPE 2 — RAPPORT + PDF
    # ════════════════════════════════════════════════════════════════════════
    if step == 2:
        # Info banner
        st.markdown("""
        <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;
                    padding:10px 14px;font-size:.82rem;color:#1e40af;
                    display:flex;align-items:flex-start;gap:8px;margin-bottom:1rem;">
            <span>ℹ️</span>
            <span>Remplissez les informations de votre rapport PFE et
            <b>joignez obligatoirement votre fichier PDF</b> avant de soumettre.</span>
        </div>
        """, unsafe_allow_html=True)

        # ── Infos rapport ──────────────────────────────────────────────────
        st.markdown('<div class="s-card">', unsafe_allow_html=True)
        st.markdown('<div class="s-title">📄 Informations du rapport</div>', unsafe_allow_html=True)

        st.text_area("Intitulé du rapport *",
                     placeholder="Ex : Développement d'une application de gestion des stocks…",
                     key="f_intitule",
                     value=st.session_state.get("f_intitule", ""),
                     height=90)

        ce, cf = st.columns(2)
        with ce:
            st.text_input("Encadrant *", placeholder="Pr. BENALI Ahmed",
                          key="f_encadrant",
                          value=st.session_state.get("f_encadrant", ""))
            st.text_input("Lieu de stage *", placeholder="OCP Group, Marrakech",
                          key="f_lieu",
                          value=st.session_state.get("f_lieu", ""))
        with cf:
            st.text_input("Co-encadrant (optionnel)", placeholder="Optionnel",
                          key="f_co_enc",
                          value=st.session_state.get("f_co_enc", ""))

        st.markdown('</div>', unsafe_allow_html=True)

        # ── Drag & Drop PDF ────────────────────────────────────────────────
        st.markdown("""
        <div style="background:#fff7ed;border:1.5px solid #f97316;border-radius:10px;
                    padding:10px 14px;font-size:.82rem;color:#7c2d12;
                    display:flex;align-items:flex-start;gap:8px;margin-bottom:.8rem;">
            <span style="font-size:1.1rem;flex-shrink:0;">📌</span>
            <span>Le dépôt du rapport PDF est <b>obligatoire</b>.
            Glissez-déposez votre fichier dans la zone ci-dessous,
            ou cliquez pour sélectionner.</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="s-card">', unsafe_allow_html=True)
        st.markdown(
            '<div class="s-title">📎 Rapport PDF'
            '<span style="color:#dc2626;font-size:.72rem;font-weight:700;'
            'margin-left:6px;text-transform:none;letter-spacing:0;">'
            '— OBLIGATOIRE</span></div>',
            unsafe_allow_html=True
        )

        pdf_file = st.file_uploader(
            "Drag and drop file here",
            type=["pdf"],
            help="Format PDF uniquement — taille max 50 Mo",
            key="f_pdf",
        )

        if pdf_file:
            sz = pdf_file.size
            sz_str = f"{sz/1024/1024:.1f} Mo" if sz > 1024*1024 else f"{sz/1024:.0f} Ko"
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:14px;background:#f0fdf4;
                        border:2px solid #16a34a;border-radius:12px;
                        padding:12px 16px;margin-top:8px;">
                <span style="font-size:2.2rem;">✅</span>
                <div>
                    <div style="font-weight:700;color:#15803d;font-size:.93rem;">
                        Fichier chargé — prêt à soumettre</div>
                    <div style="color:#166534;font-size:.8rem;margin-top:2px;">
                        📄 {pdf_file.name}</div>
                    <div style="color:#16a34a;font-size:.74rem;">{sz_str} · PDF valide</div>
                </div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align:center;margin-top:4px;font-size:.76rem;color:#94a3b8;">
                ⚠️ Aucun fichier sélectionné — le PDF est requis pour soumettre
            </div>""", unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        # ── Navigation ─────────────────────────────────────────────────────
        col_back, col_submit = st.columns([1, 2])
        with col_back:
            if st.button("← Retour", key="btn_back",
                         use_container_width=True):
                st.session_state["form_step"] = 1
                st.rerun()
        with col_submit:
            if st.button("✅ Soumettre le formulaire", type="primary",
                         key="btn_submit", use_container_width=True):

                intitule_v  = st.session_state.get("f_intitule", "").strip()
                encadrant_v = st.session_state.get("f_encadrant", "").strip()
                lieu_v      = st.session_state.get("f_lieu", "").strip()
                co_v        = st.session_state.get("f_co_enc", "").strip()

                # Récupérer filière depuis selectbox
                fil_opts_l = list(FILIERE_LABELS.values())
                fil_keys_l = list(FILIERE_LABELS.keys())
                fil_label  = st.session_state.get("f_filiere_sel", fil_opts_l[0])
                filiere_v  = fil_keys_l[fil_opts_l.index(fil_label)] if fil_label in fil_opts_l else fil_keys_l[0]
                annee_v    = st.session_state.get("f_annee_sel", "")

                errs = []
                if not intitule_v:  errs.append("L'intitulé du rapport est obligatoire.")
                if not encadrant_v: errs.append("L'encadrant est obligatoire.")
                if not lieu_v:      errs.append("Le lieu de stage est obligatoire.")
                if pdf_file is None:
                    errs.append("Le rapport PDF est obligatoire — veuillez déposer votre fichier.")

                if errs:
                    for e in errs:
                        st.error(e)
                else:
                    with st.spinner("Enregistrement en cours…"):
                        data = {
                            'nom':                    st.session_state.get("f_nom", "").strip().upper(),
                            'prenom':                 st.session_state.get("f_prenom", "").strip(),
                            'email':                  st.session_state.get("f_email", "").strip().lower(),
                            'filiere':                filiere_v,
                            'annee':                  annee_v,
                            'intitule_rapport':       intitule_v,
                            'encadrant':              encadrant_v,
                            'co_encadrant':           co_v,
                            'lieu_stage':             lieu_v,
                            'date_depot_secretariat': datetime.now().strftime("%Y-%m-%d"),
                            'correction':             'Non',
                            'nb_copies_bibliotheque': 0,
                        }
                        saved = add_student(data, pdf_file)

                    st.session_state["saved_data"] = saved
                    st.session_state["form_step"]  = 3
                    st.balloons()
                    st.rerun()


# ════════════════════════════════════════════════════════════════════════════
# ÉTAPE 3 — REÇU (identique à l'image modèle)
# ════════════════════════════════════════════════════════════════════════════
def _show_receipt():
    saved = st.session_state.get("saved_data", {})

    # Bandeau succès
    st.markdown("""
    <div style="background:linear-gradient(135deg,#dcfce7,#bbf7d0);
                border:2px solid #16a34a;border-radius:14px;
                padding:1.4rem;text-align:center;margin-bottom:1.2rem;">
        <div style="font-size:2rem;margin-bottom:.3rem;">🎉</div>
        <div style="font-size:1.15rem;font-weight:700;color:#15803d;">
            Formulaire soumis avec succès !</div>
        <div style="font-size:.86rem;color:#166534;margin-top:4px;">
            Votre rapport a bien été enregistré dans la bibliothèque
            électronique de l'ENSA Safi.</div>
    </div>
    """, unsafe_allow_html=True)

    num      = saved.get('num_ordre', '—')
    date_str = saved.get('date_soumission',
                         saved.get('date_depot_secretariat',
                                   datetime.now().strftime("%Y-%m-%d %H:%M")))
    co_enc   = saved.get('co_encadrant', '') or 'Aucun'

    # ── Reçu ──────────────────────────────────────────────────────────────
    st.markdown('<div class="s-card" style="border:2px solid #1a56a0;">', unsafe_allow_html=True)

    # En-tête reçu
    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;align-items:center;
                margin-bottom:1rem;flex-wrap:wrap;gap:.5rem;">
        <div>
            <div style="font-size:.7rem;font-weight:700;letter-spacing:.1em;
                        color:#64748b;text-transform:uppercase;">Reçu de dépôt</div>
            <div style="font-size:1.1rem;font-weight:800;color:#0f2557;">
                N° d'ordre : <span style="color:#1a56a0;">#{num}</span></div>
        </div>
        <div style="display:flex;gap:8px;align-items:center;">
            <div style="font-size:.8rem;color:#64748b;">{date_str}</div>
            <div style="background:#16a34a;color:#fff;padding:4px 14px;
                        border-radius:20px;font-size:.76rem;font-weight:700;
                        letter-spacing:.05em;">■ VALIDÉ</div>
        </div>
    </div>
    <hr style="border:none;border-top:2px solid #1a56a0;margin-bottom:1rem;">
    """, unsafe_allow_html=True)

    # Section Étudiant
    st.markdown("""
    <div style="font-size:.72rem;font-weight:700;color:#1a56a0;
                letter-spacing:.08em;text-transform:uppercase;
                margin-bottom:.5rem;">■ Informations de l'étudiant</div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="r-row"><span class="r-key">Nom &amp; Prénom</span>
        <span class="r-val">{saved.get('nom','')} {saved.get('prenom','')}</span></div>
    <div class="r-row"><span class="r-key">Email institutionnel</span>
        <span class="r-val">{saved.get('email','')}</span></div>
    <div class="r-row"><span class="r-key">Filière</span>
        <span class="r-val">{saved.get('filiere','')}</span></div>
    <div class="r-row"><span class="r-key">Année universitaire</span>
        <span class="r-val">{saved.get('annee','')}</span></div>
    """, unsafe_allow_html=True)

    # Section Rapport
    st.markdown("""
    <div style="font-size:.72rem;font-weight:700;color:#1a56a0;
                letter-spacing:.08em;text-transform:uppercase;
                margin-top:1rem;margin-bottom:.5rem;">■ Informations du rapport PFE</div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="r-row"><span class="r-key">Intitulé du rapport</span>
        <span class="r-val">{saved.get('intitule_rapport','')}</span></div>
    <div class="r-row"><span class="r-key">Encadrant</span>
        <span class="r-val">{saved.get('encadrant','')}</span></div>
    <div class="r-row"><span class="r-key">Co-encadrant</span>
        <span class="r-val">{co_enc}</span></div>
    <div class="r-row"><span class="r-key">Lieu de stage</span>
        <span class="r-val">{saved.get('lieu_stage','')}</span></div>
    <div class="r-row"><span class="r-key">Date de dépôt</span>
        <span class="r-val">{saved.get('date_depot_secretariat','')}</span></div>
    <div class="r-row"><span class="r-key">Rapport PDF</span>
        <span class="r-val" style="color:#16a34a;font-weight:700;">
            ■ Déposé dans la bibliothèque électronique</span></div>
    """, unsafe_allow_html=True)

    # Note importante
    st.markdown("""
    <div style="background:#f0fdf4;border:1.5px solid #16a34a;border-radius:10px;
                padding:12px 14px;font-size:.83rem;color:#14532d;margin-top:1rem;">
        <b>■ Ce reçu confirme que le rapport PFE a bien été soumis dans la
        bibliothèque électronique de l'ENSA Safi.<br>
        Veuillez le présenter au secrétariat du département comme
        preuve officielle de dépôt.</b>
    </div>
    """, unsafe_allow_html=True)

    # Zone signatures
    st.markdown("""
    <div style="display:flex;justify-content:space-between;
                margin-top:1.5rem;padding-top:1rem;">
        <div style="text-align:center;flex:1;">
            <div style="font-size:.82rem;font-weight:600;color:#374151;">
                Signature de l'étudiant(e)</div>
            <div style="border-bottom:1.5px solid #374151;
                        margin:1.2rem auto 0;width:160px;"></div>
        </div>
        <div style="text-align:center;flex:1;">
            <div style="font-size:.82rem;font-weight:600;color:#374151;">
                Cachet du département</div>
            <div style="border-bottom:1.5px solid #374151;
                        margin:1.2rem auto 0;width:160px;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Boutons téléchargement ─────────────────────────────────────────────
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    col_dl, col_new = st.columns(2)
    with col_dl:
        try:
            pdf_bytes = generate_recu_pdf(saved)
            st.download_button(
                "📥 Télécharger mon reçu de dépôt (PDF officiel)",
                data=pdf_bytes,
                file_name=f"recu_PFE_{num}_{saved.get('nom','')}_{saved.get('prenom','')}.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )
        except Exception as e:
            st.warning(f"Reçu PDF non disponible : {e}")
    with col_new:
        if st.button("🔄 Nouveau dépôt", use_container_width=True, key="btn_reset"):
            for k in ["form_step", "saved_data"]:
                st.session_state.pop(k, None)
            st.rerun()

    st.markdown("""
    <p style="font-size:.75rem;color:#94a3b8;text-align:center;margin-top:.8rem;">
        📋 Présentez votre <b>reçu PDF</b> au secrétariat du département
        comme preuve officielle de dépôt.
    </p>""", unsafe_allow_html=True)
