import streamlit as st
import pandas as pd
import os
try:
    from streamlit_autorefresh import st_autorefresh
    HAS_AUTOREFRESH = True
except ImportError:
    HAS_AUTOREFRESH = False
import hashlib
from utils.data_manager import (
  load_data, save_data, get_pdf_path,
  update_student, delete_student, import_from_excel, clear_all_students
)

# ── URL Google Apps Script (à configurer après déploiement) ──────
# Collez ici l'URL obtenue après déploiement du script Google Apps Script
# Exemple : "https://script.google.com/macros/s/AKfycbx.../exec"
GOOGLE_SHEET_URL = "VOTRE_URL_APPS_SCRIPT_ICI"

# ── URL du formulaire hébergé en ligne ───────────────────────────
# Collez ici l'URL du formulaire HTML hébergé (GitHub Pages, Netlify, etc.)
FORMULAIRE_ONLINE_URL = "VOTRE_URL_FORMULAIRE_ICI"

# ── Configuration API locale ────────────────────────────────────
API_LOCAL_PORT = 5050
API_LOCAL_URL = f"http://localhost:{API_LOCAL_PORT}"
FORMULAIRE_LOCAL_URL = f"{API_LOCAL_URL}/"

def load_data_from_sheets():
  """Charge les données depuis Google Sheets via Apps Script."""
  if GOOGLE_SHEET_URL == "VOTRE_URL_APPS_SCRIPT_ICI":
    return None # Pas encore configuré, utiliser CSV local
  try:
    import urllib.request, json as _json
    req = urllib.request.urlopen(GOOGLE_SHEET_URL, timeout=5)
    data = _json.loads(req.read().decode())
    if data.get("ok") and data.get("data"):
      return pd.DataFrame(data["data"])
    return None
  except Exception:
    return None

def load_data_combined():
  """Charge les données depuis Google Sheets si configuré, sinon depuis le CSV local."""
  if GOOGLE_SHEET_URL != "VOTRE_URL_APPS_SCRIPT_ICI":
    df_sheets = load_data_from_sheets()
    if df_sheets is not None and not df_sheets.empty:
      return df_sheets
  return load_data()


def check_api_status():
  """Vérifie si l'API locale est accessible."""
  try:
    import urllib.request
    req = urllib.request.urlopen(f"{API_LOCAL_URL}/api/stats", timeout=2)
    return req.getcode() == 200
  except:
    return False # Fallback CSV local


def _card(content, bg="#ffffff", border="#e2e8f0"):
  dark = st.session_state.get("dark_mode", False)
  if dark:
    bg = "#1e2130"
    border = "#2d3748"
  st.markdown(
    f'<div style="background:{bg};border:1px solid {border};border-radius:12px;'
    f'padding:1.2rem 1.4rem;margin-bottom:1rem;box-shadow:0 1px 4px rgba(0,0,0,0.06);">'
    f'{content}</div>', unsafe_allow_html=True)


def show_dashboard_page():
  if not st.session_state.get("logged_in"):
    st.session_state.page = "login"
    st.rerun()

  # ── Auto-refresh toutes les 30 secondes sans déconnexion ──────────────
  import time as _time
  if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = _time.time()
  if _time.time() - st.session_state.last_refresh > 30:
    st.session_state.last_refresh = _time.time()
    st.rerun()

  dark   = st.session_state.get("dark_mode", False)
  role   = st.session_state.get("role", "Professeur")
  username = st.session_state.get("username", "")
  nom_user = st.session_state.get("nom_user", username)
  is_admin  = (role == "Administration")
  is_prof   = (role == "Professeur")
  is_secret = (role == "Secrétaire")
  is_biblio = (role == "Responsable Bibliothèque")

  # ── Permissions par rôle (selon tableau BF-D05 à BF-D13) ────────────────
  # BF-D05 : Remplacement PDF → tous les rôles
  can_replace_pdf     = True
  # BF-D06 : Modification étudiant → Admin, Prof, Sec, Biblio (tous)
  can_edit_student    = True
  # BF-D07 : Ajout étudiant → Admin, Prof, Sec, Biblio (tous)
  can_add_student     = True
  # BF-D08 : Suppression étudiant → Admin uniquement
  can_delete_student  = is_admin
  # BF-D09 : Modification "Correction" → Admin, Prof (pas Secrétaire)
  can_edit_correction = is_admin or is_prof
  # BF-D10 : Modification "Copies Biblio" → Admin, Biblio (pas Secrétaire)
  can_edit_copies     = is_admin or is_biblio
  # Secrétaire peut modifier les autres champs étudiant
  can_edit_student_fields = True
  # BF-D11/D12/D13 : Import/Export → tous
  can_import          = True
  can_export          = True

  # ── Colors ──────────────────────────────────────────────────────────────
  bg_page  = "#0f1117" if dark else "#f0f4f8"
  bg_card  = "#1e2130" if dark else "#ffffff"
  border_c  = "#2d3748" if dark else "#e2e8f0"
  text_main = "#e2e8f0" if dark else "#0f2557"
  text_sub  = "#94a3b8" if dark else "#6b7280"

  # ── HEADER ──────────────────────────────────────────────────────────────
  import base64, os as _os
  _logo_path = _os.path.join(_os.path.dirname(_os.path.dirname(__file__)), "assets", "logo_ensa.jpg")
  _logo_html = ""
  if _os.path.exists(_logo_path):
    with open(_logo_path, "rb") as _f:
      _b64 = base64.b64encode(_f.read()).decode()
    _logo_html = f'<img src="data:image/jpeg;base64,{_b64}" style="height:44px;border-radius:8px;margin-right:14px;" />'

  col_h1, col_h2 = st.columns([5, 1])
  with col_h1:
    st.markdown(
      f'<div style="background:linear-gradient(135deg,#0f2557,#1a56a0 55%,#2563eb);'
      f'padding:1rem 1.4rem;border-radius:14px;color:white;'
      f'display:flex;align-items:center;box-shadow:0 4px 20px rgba(26,86,160,0.3);">'
      f'{_logo_html}'
      f'<div style="color:white;">'
      f'<div style="font-size:0.68rem;font-weight:600;opacity:0.75;letter-spacing:0.12em;text-transform:uppercase;color:#ffffff;-webkit-text-fill-color:#ffffff;">ENSA Safi — Université Cadi Ayyad</div>'
      f'<div style="font-size:1.05rem;font-weight:700;margin:2px 0;color:white;">Tableau de Bord — {role}</div>'
      f'<div style="font-size:0.78rem;opacity:0.9;color:#ffffff;-webkit-text-fill-color:#ffffff;">Connecté : <b style="color:#ffffff;-webkit-text-fill-color:#ffffff;">{nom_user}</b> &nbsp;·&nbsp; {username}</div>'
      f'</div></div>', unsafe_allow_html=True)

  with col_h2:
    st.markdown("<br>", unsafe_allow_html=True)
    # Dark/Light toggle
    mode_label = "Mode clair" if dark else "Mode sombre"
    if st.button(mode_label, use_container_width=True, key="btn_toggle_theme"):
      st.session_state.dark_mode = not dark
      st.rerun()
    if st.button("Déconnexion", type="secondary", use_container_width=True, key="btn_deconnexion"):
      for k in ["logged_in", "username", "role", "nom_user", "page"]:
        st.session_state.pop(k, None)
      st.rerun()

  st.markdown("")

  # ── Load data ────────────────────────────────────────────────────────────
  # Rafraîchissement auto
  if HAS_AUTOREFRESH:
    _replacing = st.session_state.get("chk_replace_pdf", False)
    # Si remplacement PDF coché → refresh très lent (120s) pour laisser le temps d'upload
    # Sinon → refresh normal 5s
    _interval = 120000 if _replacing else 5000
    st_autorefresh(interval=_interval, key="data_refresh")
  df = load_data()

  # ── KPI METRICS ─────────────────────────────────────────────────────────
  total_etudiants = len(df)
  nb_filieres   = df['filiere'].nunique() if not df.empty else 0
  nb_rapports_pdf = (
    int(df['pdf_filename'].apply(
      lambda x: bool(isinstance(x, str) and x.strip() not in ('', 'nan', 'None', 'NaN'))
    ).sum()) if not df.empty else 0
  )
  nb_corriges = len(df[df['correction'] == 'Oui']) if not df.empty else 0
  nb_non_corr = len(df[df['correction'] == 'Non']) if not df.empty else 0

  m_bg = "#1e2130" if dark else "#ffffff"
  m_border = "#2d3748" if dark else "#e2e8f0"
  m_val_color = "#60a5fa" if dark else "#1a56a0"
  m_lbl_color = "#94a3b8" if dark else "#6b7280"

  def metric_card(label, value, col):
    col.markdown(
      f'<div style="background:{m_bg};border:1px solid {m_border};border-radius:12px;'
      f'padding:1rem 1.2rem;text-align:center;box-shadow:0 1px 6px rgba(0,0,0,0.07);">'
      f'<div style="font-size:1.8rem;font-weight:800;color:{m_val_color};">{value}</div>'
      f'<div style="font-size:0.75rem;font-weight:600;color:{m_lbl_color};text-transform:uppercase;letter-spacing:0.06em;margin-top:2px;">{label}</div>'
      f'</div>', unsafe_allow_html=True)

  c1,c2,c3,c4,c5 = st.columns(5)
  metric_card("Étudiants", total_etudiants, c1)
  metric_card("Filières", nb_filieres, c2)
  metric_card("Rapports PDF", nb_rapports_pdf, c3)
  metric_card("Corrigés", nb_corriges, c4)
  metric_card("Non corrigés", nb_non_corr, c5)

  st.markdown("")

  # ── LIEN FORMULAIRE ÉTUDIANT ─────────────────────────────────────────────
  # Le formulaire étudiant est intégré dans la même app Streamlit,
  # accessible via le paramètre URL ?page=etudiant (même port, même serveur)
  try:
    _base_url = st.context.headers.get("host", "localhost:8501")
    _proto  = "https" if "ngrok" in _base_url or ".streamlit.app" in _base_url else "http"
    _formulaire_url = f"{_proto}://{_base_url}/?page=etudiant"
  except Exception:
    _formulaire_url = "http://localhost:8501/?page=etudiant"

  _lien_bg = "#1a2744" if dark else "#eff6ff"
  _lien_brd = "#2d3748" if dark else "#bfdbfe"
  _lien_txt = "#e2e8f0" if dark else "#1e40af"
  _lien_sub = "#94a3b8" if dark else "#3b82f6"
  _inp_bg  = "#0f1117" if dark else "#ffffff"
  _inp_brd = "#374151" if dark else "#bfdbfe"
  _inp_col = "#e2e8f0" if dark else "#1e40af"

  st.markdown(
    f'<div style="background:{_lien_bg};border:1.5px solid {_lien_brd};border-radius:14px;'
    f'padding:1rem 1.4rem;margin-bottom:1rem;">'
    f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">'
    f''
    f'<div>'
    f'<div style="font-size:0.88rem;font-weight:700;color:{_lien_txt};">'
    f'Lien du formulaire étudiant</div>'
    f'<div style="font-size:0.74rem;color:{_lien_sub};">'
    f'Partagez ce lien aux étudiants — ils déposent leur rapport sans compte</div>'
    f'</div>'
    f'<span style="margin-left:auto;font-size:0.72rem;font-weight:700;color:#16a34a;">🟢 Toujours actif</span>'
    f'</div>'
    f'<div style="display:flex;gap:8px;align-items:center;">'
    f'<input type="text" value="{_formulaire_url}" readonly '
    f'style="flex:1;padding:8px 12px;border:1.5px solid {_inp_brd};border-radius:8px;'
    f'background:{_inp_bg};color:{_inp_col};font-size:0.85rem;font-family:monospace;outline:none;" />'
    f'<a href="{_formulaire_url}" target="_blank" '
    f'style="padding:8px 16px;background:#1d4ed8;border-radius:8px;'
    f'color:white;font-size:0.82rem;font-weight:600;text-decoration:none;white-space:nowrap;">'
    f'🔗 Ouvrir</a>'
    f'</div>'

    f'</div>',
    unsafe_allow_html=True
  )

  st.markdown("---")

  # ── TABS ────────────────────────────────────────────────────────────────
  tabs_labels = ["Liste des Étudiants", "Import / Export", "Gestion"]
  if is_admin:
    tabs_labels.append("Comptes Accès")
  all_tabs = st.tabs(tabs_labels)
  tab1 = all_tabs[0]
  tab2 = all_tabs[1]
  tab3 = all_tabs[2]
  tab4 = all_tabs[3] if is_admin else None

  # =====================================================================
  # TAB 1 : LISTE
  # =====================================================================
  with tab1:
    if df.empty:
      st.info("Aucun rapport soumis pour le moment.")
    else:
      st.markdown(f'<div style="font-size:0.82rem;font-weight:600;color:{text_sub};margin-bottom:0.5rem;letter-spacing:0.04em;text-transform:uppercase;">Filtres de recherche</div>', unsafe_allow_html=True)
      col_f1, col_f2, col_f3, col_f4 = st.columns(4)
      with col_f1:
        filieres_list = ["Toutes"] + sorted(df['filiere'].dropna().unique().tolist())
        filiere_filter = st.selectbox("Filière", filieres_list, key="t1_filiere")
      with col_f2:
        _now = pd.Timestamp.now()
        _le = _now.year + 1 if _now.month >= 6 else _now.year
        _all_y = [f"{y}-{y+1}" for y in range(_le - 1, 2019, -1)]
        _ex_y = df['annee'].dropna().unique().tolist()
        _comb = sorted(set(_ex_y + _all_y), reverse=True)
        annee_filter = st.selectbox("Année", ["Toutes"] + _comb, key="t1_annee")
      with col_f3:
        correction_filter = st.selectbox("Correction", ["Tous", "Oui", "Non"], key="t1_corr")
      with col_f4:
        search = st.text_input("🔎 Recherche libre", placeholder="Nom, encadrant, intitulé…", key="t1_search")

      filtered = df.copy()
      if filiere_filter != "Toutes":
        filtered = filtered[filtered['filiere'] == filiere_filter]
      if annee_filter != "Toutes":
        filtered = filtered[filtered['annee'].astype(str) == annee_filter]
      if correction_filter != "Tous":
        filtered = filtered[filtered['correction'] == correction_filter]
      if search:
        mask = filtered.apply(lambda row: row.astype(str).str.contains(search, case=False, na=False).any(), axis=1)
        filtered = filtered[mask]

      st.markdown(f'<div style="font-size:0.82rem;color:{text_sub};margin-bottom:0.5rem;"><b>{len(filtered)}</b> résultat(s) sur <b>{len(df)}</b> étudiants</div>', unsafe_allow_html=True)

      display_cols = ['num_ordre','nom','prenom','filiere','annee','intitule_rapport','encadrant','lieu_stage','date_depot_secretariat','correction','nb_copies_bibliotheque']
      display_df = filtered[[c for c in display_cols if c in filtered.columns]].copy()
      display_df.rename(columns={
        'num_ordre':'N° Ordre','nom':'Nom','prenom':'Prénom','filiere':'Filière',
        'annee':'Année','intitule_rapport':'Intitulé','encadrant':'Encadrant',
        'lieu_stage':'Lieu Stage','date_depot_secretariat':"Date dépôt",
        'correction':'Correction','nb_copies_bibliotheque':'Copies Bib.'
      }, inplace=True)

      # Tableau HTML propre
      _hdr_bg  = "#1a2744" if dark else "#0f2557"
      _row_even = "#161b2e" if dark else "#f8fafc"
      _row_odd  = "#1e2130" if dark else "#ffffff"
      _txt      = "#e2e8f0" if dark else "#0f172a"
      _txt_sub  = "#94a3b8" if dark else "#374151"
      _brd      = "#2d3748" if dark else "#e2e8f0"

      cols_order = list(display_df.columns)
      header_html = "".join(
        f'<th style="padding:10px 12px;text-align:left;font-size:0.74rem;font-weight:700;'
        f'color:#ffffff;letter-spacing:0.05em;white-space:nowrap;">{c}</th>'
        for c in cols_order
      )
      rows_html = ""
      for idx, (_, row) in enumerate(display_df.iterrows()):
        bg = _row_even if idx % 2 == 0 else _row_odd
        cells = "".join(
          f'<td style="padding:9px 12px;font-size:0.84rem;color:{_txt};'
          f'border-bottom:1px solid {_brd};white-space:nowrap;max-width:200px;'
          f'overflow:hidden;text-overflow:ellipsis;">{str(v) if str(v) not in ("nan","None","") else "—"}</td>'
          for v in row.values
        )
        rows_html += f'<tr style="background:{bg};">{cells}</tr>'

      st.markdown(
        f'<div style="overflow-x:auto;border-radius:12px;border:1px solid {_brd};'
        f'box-shadow:0 2px 8px rgba(0,0,0,0.07);margin-bottom:1rem;">'
        f'<table style="width:100%;border-collapse:collapse;">'
        f'<thead><tr style="background:{_hdr_bg};">{header_html}</tr></thead>'
        f'<tbody>{rows_html}</tbody>'
        f'</table></div>',
        unsafe_allow_html=True
      )

      # ── PDF Access ───────────────────────────────────────────────
      st.markdown("---")
      st.markdown(
        f'<div style="background:linear-gradient(135deg,#0f2557,#1a56a0);padding:0.7rem 1rem;'
        f'border-radius:10px;color:white;margin-bottom:0.8rem;">'
        f'<span style="font-weight:600;color:white;">Accès aux Rapports PDF</span>'
        f'<span style="font-size:0.78rem;opacity:0.8;margin-left:8px;color:white;">Télécharger les rapports déposés</span>'
        f'</div>', unsafe_allow_html=True)

      pdf_all = filtered[filtered['pdf_filename'].apply(
        lambda x: bool(isinstance(x, str) and x.strip() not in ('','nan','None','NaN'))
      )].copy()

      if pdf_all.empty:
        st.warning("Aucun PDF disponible pour les étudiants filtrés.")
      else:
        pc1, pc2, pc3 = st.columns(3)
        with pc1: pdf_search = st.text_input("Recherche", placeholder="Nom, intitulé…", key="pdf_search")
        with pc2: pdf_filiere = st.selectbox("Filière", ["Toutes"]+sorted(pdf_all['filiere'].dropna().unique().tolist()), key="pdf_filiere")
        with pc3: pdf_annee  = st.selectbox("Année", ["Toutes"]+sorted(pdf_all['annee'].dropna().unique().tolist(), reverse=True), key="pdf_annee")

        pdf_rows = pdf_all.copy()
        if pdf_search:
          mask = (pdf_rows['nom'].astype(str).str.contains(pdf_search, case=False, na=False) |
              pdf_rows['prenom'].astype(str).str.contains(pdf_search, case=False, na=False) |
              pdf_rows['intitule_rapport'].astype(str).str.contains(pdf_search, case=False, na=False))
          pdf_rows = pdf_rows[mask]
        if pdf_filiere != "Toutes": pdf_rows = pdf_rows[pdf_rows['filiere'] == pdf_filiere]
        if pdf_annee  != "Toutes": pdf_rows = pdf_rows[pdf_rows['annee'].astype(str) == pdf_annee]

        st.markdown(f'<div style="font-size:0.82rem;color:{text_sub};margin-bottom:6px;">📄 <b>{len(pdf_rows)}</b> rapport(s) PDF trouvé(s)</div>', unsafe_allow_html=True)

        if not pdf_rows.empty:
          header_bg = "#1a2744" if dark else "#1a56a0"
          st.markdown(
            f'<div style="display:grid;grid-template-columns:2fr 2fr 1fr 1fr 1.2fr;gap:6px;'
            f'padding:7px 12px;background:{header_bg};border-radius:8px 8px 0 0;'
            f'font-size:0.75rem;font-weight:700;color:#ffffff!important;">'
            f'<div style="color:#ffffff!important;">Étudiant</div>'
            f'<div style="color:#ffffff!important;">Intitulé</div>'
            f'<div style="color:#ffffff!important;">Filière</div>'
            f'<div style="color:#ffffff!important;">Année</div>'
            f'<div style="text-align:center;color:#ffffff!important;">PDF</div>'
            f'</div>', unsafe_allow_html=True)

          for i, (_, row) in enumerate(pdf_rows.iterrows()):
            row_bg = ("#161b2e" if i%2==0 else "#1e2130") if dark else ("#f8fafc" if i%2==0 else "#ffffff")
            intitule_short = str(row['intitule_rapport'])[:50] + ("…" if len(str(row['intitule_rapport']))>50 else "")
            pdf_path = get_pdf_path(str(row['pdf_filename']))
            num_ordre_key = str(row['num_ordre'])
            c1,c2,c3,c4,c5 = st.columns([2,2,1,1,1.5])
            row_style = f"background:{row_bg};padding:8px 10px;border-bottom:0.5px solid {border_c};"
            with c1: st.markdown(f'<div style="{row_style}font-size:0.84rem;font-weight:600;color:{text_main};">#{row["num_ordre"]} — {row["nom"]} {row["prenom"]}</div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div style="{row_style}font-size:0.78rem;color:{text_sub};">{intitule_short}</div>', unsafe_allow_html=True)
            with c3: st.markdown(f'<div style="{row_style}text-align:center;"><span style="background:#1d4ed8;color:#ffffff;padding:2px 8px;border-radius:12px;font-size:0.72rem;font-weight:700;">{row["filiere"]}</span></div>', unsafe_allow_html=True)
            with c4: st.markdown(f'<div style="{row_style}font-size:0.78rem;color:{text_sub};text-align:center;">{row["annee"]}</div>', unsafe_allow_html=True)
            with c5:
              from utils.data_manager import get_pdf_url, _use_supabase
              pdf_filename = str(row.get('pdf_filename', ''))
              pdf_available = False
              pdf_url = None
              if _use_supabase() and pdf_filename and pdf_filename.strip():
                pdf_url = get_pdf_url(pdf_filename)
                pdf_available = True
              elif os.path.exists(pdf_path):
                pdf_available = True
              if pdf_available:
                cb1, cb2 = st.columns(2)
                with cb1:
                  preview_key = f"show_preview_{num_ordre_key}"
                  label_preview = "Fermer" if st.session_state.get(preview_key) else "Lire"
                  if st.button(label_preview, key=f"prev_btn_{num_ordre_key}", use_container_width=True):
                    st.session_state[preview_key] = not st.session_state.get(preview_key, False)
                    st.rerun()
                with cb2:
                  if pdf_url:
                    st.markdown(f'<a href="{pdf_url}" target="_blank" download style="display:block;text-align:center;background:#1d4ed8;color:white;padding:6px;border-radius:6px;font-size:0.78rem;text-decoration:none;">⬇ PDF</a>', unsafe_allow_html=True)
                  elif os.path.exists(pdf_path):
                    with open(pdf_path, "rb") as _pf:
                      st.download_button("PDF", data=_pf.read(), file_name=str(row['pdf_filename']),
                                mime="application/pdf", key=f"dl_{num_ordre_key}", use_container_width=True)
              else:
                st.markdown('<div style="text-align:center;font-size:0.75rem;color:#9ca3af;padding:8px 0;">Non trouvé</div>', unsafe_allow_html=True)

            # ── Prévisualisation inline (sous la ligne) ──────────────────
            show_prev = st.session_state.get(f"show_preview_{num_ordre_key}")
            if show_prev:
              from utils.data_manager import get_pdf_url, _use_supabase
              import base64 as _b64
              nom_etud = f"{row['nom']} {row['prenom']}"
              pdf_filename = str(row.get('pdf_filename', ''))
              pdf_src = None

              if _use_supabase() and pdf_filename:
                pdf_src = get_pdf_url(pdf_filename)
              elif os.path.exists(pdf_path):
                with open(pdf_path, "rb") as _pf2:
                  pdf_b64 = _b64.b64encode(_pf2.read()).decode()
                pdf_src = f"data:application/pdf;base64,{pdf_b64}"

              if pdf_src:
                st.markdown(
                  f'''<div style="background:{row_bg};padding:10px 14px;border-bottom:2px solid #2563eb;margin-bottom:4px;">
                  <div style="font-size:0.78rem;font-weight:600;color:#2563eb;margin-bottom:6px;">
                    Rapport de {nom_etud} — {row["filiere"]} {row["annee"]}
                  </div>
                  <iframe src="https://mozilla.github.io/pdf.js/web/viewer.html?file={pdf_src}"
                    width="100%" height="650px"
                    style="border:1.5px solid #cbd5e1;border-radius:8px;background:#fff;">
                  </iframe>
                  <p style="font-size:0.75rem;color:#64748b;margin-top:6px;">
                    Si le PDF ne s'affiche pas, utilisez le bouton ⬇ PDF pour le télécharger.
                  </p>
                  </div>''',
                  unsafe_allow_html=True
                )
              else:
                st.info("PDF non disponible pour cet étudiant.")

  # =====================================================================
  # TAB 2 : IMPORT / EXPORT
  # =====================================================================
  with tab2:
    col_imp, col_exp = st.columns(2)

    with col_imp:
      st.markdown(f'<div style="font-size:1.05rem;font-weight:700;color:{text_main};margin-bottom:0.6rem;border-left:4px solid #2563eb;padding-left:10px;">Import depuis Excel</div>', unsafe_allow_html=True)
      st.info("Colonnes : Nom, Prénom, Email, Filière, Année, Intitulé, Encadrant, Co-encadrant, Lieu de stage, Correction, Copies bibliothèque.")
      excel_file = st.file_uploader("Choisir un fichier Excel (.xlsx)", type=["xlsx","xls"], key="excel_upload")
      if excel_file:
        c1, c2 = st.columns(2)
        with c1:
          if st.button("Aperçu", use_container_width=True, key="btn_apercu"):
            try:
              preview = pd.read_excel(excel_file, engine='openpyxl')
              st.dataframe(preview.head(5), use_container_width=True)
            except Exception as e:
              st.error(f"Erreur: {e}")
        with c2:
          if st.button("Importer", type="primary", use_container_width=True, key="btn_importer"):
            added, err = import_from_excel(excel_file)
            if err: st.error(f"Erreur: {err}")
            else:
              st.success(f"{added} étudiant(s) importé(s) !")
              st.rerun()

    with col_exp:
      st.markdown(f'<div style="font-size:1.05rem;font-weight:700;color:{text_main};margin-bottom:0.6rem;border-left:4px solid #2563eb;padding-left:10px;">Export des données</div>', unsafe_allow_html=True)
      if not df.empty:
        csv_data = df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button("Exporter en CSV", data=csv_data, file_name="rapports_PFE.csv",
                  mime="text/csv", use_container_width=True, key="btn_export_csv")
        try:
          import io
          buf = io.BytesIO()
          with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Rapports PFE')
          st.download_button("Exporter en Excel (.xlsx)", data=buf.getvalue(),
                    file_name="rapports_PFE.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True, key="btn_export_xlsx")
        except ImportError:
          st.caption("(openpyxl requis pour l'export Excel)")
      else:
        st.info("Aucune donnée à exporter.")

    # ── Reset / Vider la base ─────────────────────────────────────────
    if is_admin:
      st.markdown("---")
      st.markdown(f'<div style="font-size:1.05rem;font-weight:700;color:#dc2626;margin-bottom:0.6rem;border-left:4px solid #dc2626;padding-left:10px;">Réinitialisation de la base</div>', unsafe_allow_html=True)
      st.markdown(
        f'<div style="background:{"#2d1515" if dark else "#fef2f2"};border:2px solid #fca5a5;'
        f'border-radius:10px;padding:12px 16px;margin-bottom:1rem;">'
        f'<b style="color:#dc2626;">Zone dangereuse</b> — Cette action supprime <b>tous</b> les étudiants et leurs PDFs de façon irréversible.</div>',
        unsafe_allow_html=True)

      if not st.session_state.get("confirm_reset_all"):
        if st.button("Vider toute la base étudiants", type="secondary", key="btn_ask_reset"):
          st.session_state.confirm_reset_all = True
          st.rerun()
      else:
        st.warning("Êtes-vous sûr ? Cette action est **irréversible**.")
        rc1, rc2 = st.columns(2)
        with rc1:
          if st.button("Confirmer la suppression", type="primary", key="btn_confirm_reset"):
            clear_all_students()
            st.session_state.confirm_reset_all = False
            st.success("Base étudiants réinitialisée avec succès.")
            st.rerun()
        with rc2:
          if st.button("Annuler", key="btn_cancel_reset"):
            st.session_state.confirm_reset_all = False
            st.rerun()

  # =====================================================================
  # TAB 3 : GESTION
  # =====================================================================
  with tab3:
    st.markdown(f'<div style="font-size:1.05rem;font-weight:700;color:{text_main};margin-bottom:0.8rem;border-left:4px solid #2563eb;padding-left:10px;">Modifier / Mettre à jour un étudiant</div>', unsafe_allow_html=True)

    if df.empty:
      st.info("Aucun étudiant enregistré.")
    else:
      fg1, fg2, fg3 = st.columns(3)
      with fg1: gest_search = st.text_input("Nom / Prénom", placeholder="Tapez pour filtrer…", key="gest_search")
      with fg2: gest_filiere = st.selectbox("Filière", ["Toutes"]+sorted(df['filiere'].dropna().unique().tolist()), key="gest_filiere")
      with fg3:
        _cy = pd.Timestamp.now().year; _cm = pd.Timestamp.now().month
        _le2 = _cy+1 if _cm>=6 else _cy
        _all_y2 = [f"{y}-{y+1}" for y in range(_le2-1, 2019, -1)]
        _comb_y2 = sorted(set(df['annee'].dropna().unique().tolist() + _all_y2), reverse=True)
        gest_annee = st.selectbox("Année", ["Toutes"]+_comb_y2, key="gest_annee")

      df_gest = df.copy()
      if gest_search:
        _m = (df_gest['nom'].astype(str).str.contains(gest_search, case=False, na=False) |
           df_gest['prenom'].astype(str).str.contains(gest_search, case=False, na=False))
        df_gest = df_gest[_m]
      if gest_filiere != "Toutes": df_gest = df_gest[df_gest['filiere'] == gest_filiere]
      if gest_annee  != "Toutes": df_gest = df_gest[df_gest['annee'].astype(str) == gest_annee]

      st.markdown(f'<div style="font-size:0.82rem;color:{text_sub};margin-bottom:8px;"><b>{len(df_gest)}</b> étudiant(s) trouvé(s) sur <b>{len(df)}</b></div>', unsafe_allow_html=True)

      if df_gest.empty:
        st.info("Aucun étudiant correspondant.")
      else:
        options_labels = [
          f"#{row['num_ordre']} — {row['nom']} {row['prenom']} ({row['filiere']}, {row['annee']})"
          for _, row in df_gest.iterrows()
        ]
        options_nums = [row['num_ordre'] for _, row in df_gest.iterrows()]

        selected_label = st.selectbox("Choisir un étudiant", options_labels, key="gest_select_etudiant")
        selected_num  = options_nums[options_labels.index(selected_label)]

        student_rows = df[df['num_ordre'].astype(str) == str(selected_num)]
        if student_rows.empty:
          st.warning("Étudiant introuvable. Rafraîchissez la page.")
          st.stop()
        student = student_rows.iloc[0]

        st.markdown("---")
        col_e1, col_e2 = st.columns(2)
        with col_e1:
          # BF-D09 : Modification Correction → Admin, Prof uniquement
          if can_edit_correction:
            new_correction = st.selectbox("Correction", ["Non","Oui"],
              index=0 if str(student.get('correction','Non')) == 'Non' else 1, key="gest_corr")
          else:
            new_correction = str(student.get('correction','Non'))
            _corr_val = "✅ Oui" if new_correction == "Oui" else "❌ Non"
            st.text_input("Correction", value=_corr_val, disabled=True, key="gest_corr_ro",
                          help="Modification réservée aux Administrateurs et Professeurs")
          # BF-D10 : Modification Copies Biblio → Admin, Biblio uniquement
          if can_edit_copies:
            new_copies = st.number_input("Nb copies transmises à la bibliothèque",
              min_value=0, value=int(student.get('nb_copies_bibliotheque', 0) or 0), key="gest_copies")
          else:
            new_copies = int(student.get('nb_copies_bibliotheque', 0) or 0)
            st.text_input("Nb copies transmises à la bibliothèque",
                          value=str(new_copies), disabled=True, key="gest_copies_ro",
                          help="Modification réservée aux Administrateurs et Responsables Bibliothèque")
          reg_date = str(student.get('date_depot_secretariat','') or student.get('date_soumission',''))
          st.text_input("📅 Date d'enregistrement", value=reg_date, disabled=True)
          new_nom = st.text_input("Nom", value=str(student.get('nom','')), key="gest_nom")
          new_prenom = st.text_input("Prénom", value=str(student.get('prenom','')), key="gest_prenom")
          new_email = st.text_input("Email", value=str(student.get('email','')), key="gest_email")
        with col_e2:
          new_encadrant = st.text_input("Encadrant", value=str(student.get('encadrant','')), key="gest_enc")
          new_co_enc = st.text_input("Co-encadrant", value=str(student.get('co_encadrant','')), key="gest_co_enc")
          new_lieu = st.text_input("Lieu de stage", value=str(student.get('lieu_stage','')), key="gest_lieu")
          new_intitule = st.text_area("Intitulé rapport", value=str(student.get('intitule_rapport','')), key="gest_intitule", height=100)
          # Filière
          _fil_opts = ["GIIA","GTR","GATE","GPMA","GINDUS","GMSI"]
          _cur_fil = str(student.get('filiere','GIIA'))
          _fil_idx = _fil_opts.index(_cur_fil) if _cur_fil in _fil_opts else 0
          new_filiere = st.selectbox("Filière", _fil_opts, index=_fil_idx, key="gest_filiere_edit")

        # ── Section PDF ───────────────────────────────────────────────────────
        st.markdown("---")
        current_pdf = str(student.get('pdf_filename', '')).strip()
        pdf_valid = isinstance(student.get('pdf_filename'), str) and current_pdf not in ('','nan','None','NaN')
        from utils.data_manager import get_pdf_url, _use_supabase, _upload_pdf_supabase
        pdf_exists = (pdf_valid and _use_supabase()) or (pdf_valid and os.path.exists(get_pdf_path(current_pdf)))

        # Afficher statut PDF
        if pdf_exists:
          st.markdown(
            f'<div style="background:{"#0d2b1a" if dark else "#f0fdf4"};border:1px solid #86efac;'
            f'border-radius:8px;padding:10px 14px;display:flex;align-items:center;gap:10px;margin-bottom:10px;">'
            f'<span style="font-size:1.3rem;">✅</span>'
            f'<div><div style="font-weight:600;color:#15803d;font-size:0.88rem;">PDF déjà présent : {current_pdf}</div></div></div>',
            unsafe_allow_html=True)
          replace_pdf = st.checkbox("Remplacer le PDF existant par un nouveau", key="chk_replace_pdf")
        else:
          st.markdown(
            f'<div style="background:{"#2b2300" if dark else "#fef9c3"};border:1px solid #fde047;'
            f'border-radius:8px;padding:10px 14px;margin-bottom:10px;">'
            f'<b style="color:#92400e;">⚠️ Aucun PDF pour cet étudiant</b></div>',
            unsafe_allow_html=True)
          replace_pdf = True

        uploaded_pdf = None
        if replace_pdf:
          uploaded_pdf = st.file_uploader(
            f"📎 Nouveau rapport PDF de {student['nom']} {student['prenom']}",
            type=["pdf"], key=f"pdf_upload_{selected_num}")
          if uploaded_pdf:
            st.session_state[f"pdf_bytes_{selected_num}"] = bytes(uploaded_pdf.getbuffer())

        # ── Bouton unique Mettre à jour ────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        col_upd, col_del = st.columns(2)
        with col_upd:
          if st.button("Mettre à jour", type="primary", use_container_width=True, key="btn_update_student"):
            updates = {
              'correction': new_correction,
              'nb_copies_bibliotheque': new_copies,
              'encadrant': new_encadrant,
              'co_encadrant': new_co_enc,
              'lieu_stage': new_lieu,
              'intitule_rapport': new_intitule,
              'nom': new_nom.strip().upper(),
              'prenom': new_prenom.strip(),
              'email': new_email.strip(),
              'filiere': new_filiere,
            }
            # Traiter le PDF si uploadé
            if uploaded_pdf or f"pdf_bytes_{selected_num}" in st.session_state:
              pdf_bytes = st.session_state.get(f"pdf_bytes_{selected_num}")
              if pdf_bytes is None and uploaded_pdf:
                pdf_bytes = bytes(uploaded_pdf.getbuffer())
              if pdf_bytes:
                safe = f"{selected_num}_{new_nom.strip().upper()}_{new_prenom.strip()}_{student['annee']}.pdf"
                safe = safe.replace(" ","_").replace("/","-")
                # Supprimer ancien PDF si différent
                if _use_supabase() and pdf_valid and current_pdf != safe:
                  try:
                    import requests as _req
                    from utils.data_manager import _get_supabase_url, _get_supabase_key, STORAGE_BUCKET
                    _req.delete(
                      f"{_get_supabase_url()}/storage/v1/object/{STORAGE_BUCKET}/{current_pdf}",
                      headers={"apikey": _get_supabase_key(), "Authorization": f"Bearer {_get_supabase_key()}"},
                      timeout=10)
                  except Exception:
                    pass
                if _use_supabase():
                  ok = _upload_pdf_supabase(pdf_bytes, safe)
                  if ok:
                    updates['pdf_filename'] = safe
                    st.session_state.pop(f"pdf_bytes_{selected_num}", None)
                  else:
                    st.error("❌ Erreur upload PDF — les autres infos ont été sauvegardées")
                else:
                  from utils.data_manager import UPLOADS_DIR
                  os.makedirs(UPLOADS_DIR, exist_ok=True)
                  with open(get_pdf_path(safe), "wb") as _f:
                    _f.write(pdf_bytes)
                  updates['pdf_filename'] = safe
                  st.session_state.pop(f"pdf_bytes_{selected_num}", None)
            update_student(selected_num, updates)
            st.success("✅ Étudiant mis à jour ! Visible chez tous dans 5 secondes.")
            st.rerun()
        with col_del:
          if can_delete_student:
            if st.button("Supprimer cet étudiant", type="secondary", use_container_width=True, key="btn_delete_student"):
              delete_student(selected_num)
              if "gest_select_etudiant" in st.session_state:
                del st.session_state["gest_select_etudiant"]
              st.warning("Étudiant supprimé.")
              st.rerun()
          else:
            st.caption("(Suppression réservée à l'Administration)")

    # Ajout manuel
    st.markdown("---")
    st.markdown(f'<div style="font-size:1rem;font-weight:700;color:{text_main};margin-bottom:0.5rem;border-left:4px solid #2563eb;padding-left:10px;">Ajouter manuellement un étudiant</div>', unsafe_allow_html=True)
    with st.expander("Formulaire d'ajout manuel"):
      from utils.data_manager import add_student
      from datetime import datetime as _dt

      # Clé dynamique pour vider les champs après ajout
      if "form_version" not in st.session_state:
        st.session_state.form_version = 0
      _fv = st.session_state.form_version

      _cy2 = pd.Timestamp.now().year; _cm2 = pd.Timestamp.now().month
      _le3 = _cy2+1 if _cm2>=6 else _cy2
      _ay3 = [f"{y}-{y+1}" for y in range(_le3-1, 2019, -1)]

      # Afficher message succès
      if st.session_state.pop("add_success", False):
        st.success("Etudiant ajouté avec succès !")

      m_col1, m_col2 = st.columns(2)
      with m_col1:
        m_nom      = st.text_input("Nom *",                    key=f"m_nom_{_fv}")
        m_email    = st.text_input("Email *",                  key=f"m_email_{_fv}")
        m_filiere  = st.selectbox("Filière *", ["GIIA","GTR","GATE","GPMA","GINDUS","GMSI"], key=f"m_filiere_{_fv}")
        m_intitule = st.text_input("Intitulé rapport *",       key=f"m_intitule_{_fv}")
        m_lieu     = st.text_input("Lieu de stage *",          key=f"m_lieu_{_fv}")
      with m_col2:
        m_prenom    = st.text_input("Prénom *",                key=f"m_prenom_{_fv}")
        m_annee     = st.selectbox("Année *", _ay3,            key=f"m_annee_{_fv}")
        m_encadrant = st.text_input("Encadrant *",             key=f"m_encadrant_{_fv}")
        m_co_enc    = st.text_input("Co-encadrant (optionnel)", key=f"m_co_enc_{_fv}")

      m_pdf = st.file_uploader("Rapport PDF (optionnel)", type=["pdf"], key=f"m_pdf_upload_{_fv}")

      if st.button("Ajouter l'étudiant", type="primary", key="btn_add_student_manual"):
        _errs_add = []
        if not m_nom.strip(): _errs_add.append("Le nom est obligatoire.")
        if not m_prenom.strip(): _errs_add.append("Le prénom est obligatoire.")
        if not m_email.strip(): _errs_add.append("L'email est obligatoire.")
        if not m_intitule.strip(): _errs_add.append("L'intitulé du rapport est obligatoire.")
        if not m_encadrant.strip(): _errs_add.append("L'encadrant est obligatoire.")
        if not m_lieu.strip(): _errs_add.append("Le lieu de stage est obligatoire.")
        if _errs_add:
          for _e in _errs_add:
            st.error(_e)
        else:
          st.session_state["adding_student"] = True
          add_student({
            'nom': m_nom.strip().upper(), 'prenom': m_prenom.strip(),
            'email': m_email.strip(), 'filiere': m_filiere, 'annee': m_annee,
            'intitule_rapport': m_intitule.strip(), 'encadrant': m_encadrant.strip(),
            'co_encadrant': m_co_enc.strip(), 'lieu_stage': m_lieu.strip(),
            'date_depot_secretariat': _dt.now().strftime("%Y-%m-%d %H:%M"),
            'correction': 'Non', 'nb_copies_bibliotheque': 0
          }, m_pdf)
          st.success("Étudiant ajouté avec succès !")
          # Vider les champs du formulaire
          for _k in ["m_nom", "m_prenom", "m_email", "m_intitule", "m_encadrant", "m_co_enc", "m_lieu", "m_pdf_upload"]:
            if _k in st.session_state:
              del st.session_state[_k]
          st.session_state["add_success"] = True
          st.session_state.form_version += 1
          st.rerun()

  # =====================================================================
  # TAB 4 : COMPTES (Admin only)
  # =====================================================================
  if is_admin and tab4 is not None:
    with tab4:
      from modules.login import load_accounts, add_account, delete_account, SUPER_ADMIN, save_allowed_excel, load_allowed_emails, is_email_allowed
      import io as _io

      accounts     = load_accounts()
      allowed_accounts = load_allowed_emails()
      current_user   = st.session_state.get("username", "")
      is_superadmin  = (current_user == SUPER_ADMIN)

      header_color = "linear-gradient(135deg,#0f2557,#1a56a0)" if is_superadmin else "linear-gradient(135deg,#374151,#4b5563)"
      header_desc = ("Vous êtes <b>Super Administrateur</b> — accès complet." if is_superadmin
              else "Accès <b>lecture seule</b> — seul le Super Admin peut modifier.")

      st.markdown(
        f'<div style="background:{header_color};padding:1rem 1.2rem;border-radius:12px;color:white;margin-bottom:1rem;">'
        f'<div style="font-size:0.95rem;font-weight:600;color:#ffffff;-webkit-text-fill-color:#ffffff;">Comptes d\'Accès — ENSA Safi</div>'
        f'<div style="font-size:0.78rem;opacity:0.85;margin-top:4px;color:#ffffff;-webkit-text-fill-color:#ffffff;">{header_desc}</div>'
        f'</div>', unsafe_allow_html=True)

      total_acc = len(accounts)
      nb_admin = sum(1 for v in accounts.values() if v['role'] == 'Administration')
      nb_prof  = sum(1 for v in accounts.values() if v['role'] == 'Professeur')
      nb_secret = sum(1 for v in accounts.values() if v['role'] == 'Secrétaire')
      nb_biblio = sum(1 for v in accounts.values() if v['role'] == 'Responsable Bibliothèque')
      kc1,kc2,kc3,kc4,kc5 = st.columns(5)
      kc1.metric("👥 Total comptes", total_acc)
      kc2.metric("🔴 Admins",    nb_admin)
      kc3.metric("🔵 Professeurs",  nb_prof)
      kc4.metric("🟢 Secrétaires",  nb_secret)
      kc5.metric("🟠 Biblio",    nb_biblio)
      st.markdown("---")

      st.markdown('<div style="font-size:0.95rem;font-weight:700;margin-bottom:0.6rem;">Liste des comptes autorisés</div>', unsafe_allow_html=True)
      col_a, col_b = st.columns([2,1])
      with col_a:
        allowed_file = st.file_uploader("Importer un fichier Excel (.xlsx) des comptes autorisés", type=["xlsx","xls"], key="allowed_upload")
      with col_b:
        if allowed_accounts:
          allowed_df = pd.DataFrame([{"Email": e, "Nom": v["nom"], "Rôle": v["role"]} for e, v in allowed_accounts.items()])
          buf_allowed = _io.BytesIO()
          with pd.ExcelWriter(buf_allowed, engine='openpyxl') as writer:
            allowed_df.to_excel(writer, index=False, sheet_name='Autorises')
          st.download_button("Télécharger la liste actuelle", data=buf_allowed.getvalue(),
                    file_name="utilisateurs_autorises.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_allowed_list", use_container_width=True)
        else:
          st.write("Aucun fichier autorisé n'est chargé.")

      if allowed_file:
        try:
          bytes_data = allowed_file.getvalue()
          preview_df = pd.read_excel(_io.BytesIO(bytes_data), engine="openpyxl")
          st.markdown(f"**Fichier chargé : {len(preview_df)} ligne(s)**")
          st.markdown("Ce fichier n'est pas encore enregistré. Cliquez sur \"Enregistrer cette liste autorisée\" pour le sauvegarder.")
          st.dataframe(preview_df.head(15), use_container_width=True)
          if st.button("Enregistrer cette liste autorisée", type="primary", key="save_allowed_list"):
            df_to_save = pd.read_excel(_io.BytesIO(bytes_data), engine="openpyxl")
            save_allowed_excel(df_to_save)
            st.success("Liste autorisée enregistrée.")
            st.rerun()
        except Exception as exc:
          st.error(f"Erreur lors de la lecture du fichier Excel. Vérifiez le format et les colonnes. ({exc})")

      sub1, sub2 = st.tabs(["Liste des comptes", "Ajouter un compte"])

      with sub1:
        fc1, fc2 = st.columns(2)
        with fc1: acc_search = st.text_input("🔎 Rechercher (nom / email)", key="acc_search")
        with fc2: acc_role_filter = st.selectbox("Filtrer par rôle", ["Tous","Administration","Professeur","Secrétaire","Responsable Bibliothèque"], key="acc_role_filter")

        filtered_acc = {
          e: i for e, i in accounts.items()
          if (acc_search.lower() in e.lower() or acc_search.lower() in i['nom'].lower() if acc_search else True)
          and (i['role'] == acc_role_filter if acc_role_filter != "Tous" else True)
        }
        st.markdown(f'<div style="font-size:0.82rem;color:{text_sub};margin-bottom:8px;"><b>{len(filtered_acc)}</b> compte(s) sur <b>{total_acc}</b></div>', unsafe_allow_html=True)

        # Inject CSS to force button visibility regardless of row background
        # Force all buttons visible - inject scoped CSS
        if dark:
            st.markdown("""
            <style>
            .stButton > button {
                color: #e2e8f0 !important;
                background: #2d3748 !important;
                border: 1.5px solid #4b5563 !important;
                font-weight: 600 !important;
            }
            .stButton > button[kind="primary"] {
                background: linear-gradient(135deg,#1a56a0,#2563eb) !important;
                color: #ffffff !important; border: none !important;
            }
            </style>""", unsafe_allow_html=True)
        else:
            st.markdown("""
            <style>
            /* Default buttons : fond blanc, texte NOIR visible */
            [data-testid="baseButton-secondary"],
            [data-testid="baseButton-secondaryFormSubmit"],
            .stButton > button {
                background-color: #ffffff !important;
                background: #ffffff !important;
                border: 1.5px solid #1a56a0 !important;
                font-weight: 600 !important;
                color: #1a56a0 !important;
                fill: #1a56a0 !important;
            }
            [data-testid="baseButton-secondary"] *,
            [data-testid="baseButton-secondaryFormSubmit"] *,
            .stButton > button * {
                color: #1a56a0 !important;
                fill: #1a56a0 !important;
                -webkit-text-fill-color: #1a56a0 !important;
            }
            [data-testid="baseButton-secondary"]:hover,
            .stButton > button:hover {
                background: #eff6ff !important;
                border-color: #2563eb !important;
            }
            /* Primary : bleu + texte blanc */
            [data-testid="baseButton-primary"],
            [data-testid="baseButton-primaryFormSubmit"],
            .stButton > button[kind="primary"] {
                background: linear-gradient(135deg,#1a56a0,#2563eb) !important;
                background-color: #1a56a0 !important;
                border: none !important;
                color: #ffffff !important;
            }
            [data-testid="baseButton-primary"] *,
            [data-testid="baseButton-primaryFormSubmit"] *,
            .stButton > button[kind="primary"] * {
                color: #ffffff !important;
                fill: #ffffff !important;
                -webkit-text-fill-color: #ffffff !important;
            }
            /* Download buttons : bleu + texte blanc */
            [data-testid="stDownloadButton"] button,
            .stDownloadButton > button {
                background: linear-gradient(135deg,#1a56a0,#2563eb) !important;
                background-color: #1a56a0 !important;
                border: none !important;
                color: #ffffff !important;
            }
            [data-testid="stDownloadButton"] button *,
            .stDownloadButton > button * {
                color: #ffffff !important;
                fill: #ffffff !important;
                -webkit-text-fill-color: #ffffff !important;
            }
            </style>""", unsafe_allow_html=True)

        header_bg2 = "#1a2744" if dark else "#0f2557"
        st.markdown(
          f'<div style="display:grid;grid-template-columns:2.5fr 1.5fr 1.5fr 1fr 1fr;gap:6px;'
          f'padding:7px 12px;background:{header_bg2};border-radius:8px 8px 0 0;'
          f'font-size:0.75rem;font-weight:700;">'
          f'<div style="color:#ffffff;-webkit-text-fill-color:#ffffff;">Nom &amp; Email</div>'
          f'<div style="color:#ffffff;-webkit-text-fill-color:#ffffff;">Rôle</div>'
          f'<div style="color:#ffffff;-webkit-text-fill-color:#ffffff;">Statut</div>'
          f'<div style="text-align:center;color:#ffffff;-webkit-text-fill-color:#ffffff;">Modifier MDP</div>'
          f'<div style="text-align:center;color:#ffffff;-webkit-text-fill-color:#ffffff;">Supprimer</div>'
          f'</div>', unsafe_allow_html=True)

        role_colors = {
          "Administration": ("#dc2626","#ffffff","🔴"),
          "Professeur":   ("#1d4ed8","#ffffff","🔵"),
          "Secrétaire":   ("#15803d","#ffffff","🟢"),
          "Responsable Bibliothèque": ("#7c3aed","#ffffff","📚"),
        }

        for i, (email, info) in enumerate(filtered_acc.items()):
          row_bg2 = ("#161b2e" if i%2==0 else "#1e2130") if dark else ("#f8fafc" if i%2==0 else "#ffffff")
          is_me  = (email == current_user)
          rb, rc, ri = role_colors.get(info['role'], ("#f9fafb","#374151","⚪"))

          ca,cb,cc,cd,ce = st.columns([2.5,1.5,1.5,1,1])
          row_s = f"background:{row_bg2};padding:8px 10px;border-bottom:0.5px solid {border_c};"
          with ca:
            me_badge = ' <span style="background:#fde047;color:#713f12;font-size:10px;padding:1px 6px;border-radius:10px;">VOUS</span>' if is_me else ''
            st.markdown(f'<div style="{row_s}"><div style="font-weight:600;font-size:0.85rem;color:{text_main};">{info["nom"]}{me_badge}</div><div style="font-size:0.75rem;color:{text_sub};font-family:monospace;">{email}</div></div>', unsafe_allow_html=True)
          with cb:
            st.markdown(f'<div style="{row_s}"><span style="background:{rb};color:{rc};padding:3px 10px;border-radius:12px;font-size:0.75rem;font-weight:700;">{ri} {info["role"]}</span></div>', unsafe_allow_html=True)
          with cc:
            status = "🟡 Connecté" if is_me else "🟢 Actif"
            st.markdown(f'<div style="{row_s}font-size:0.82rem;color:{text_sub};">{status}</div>', unsafe_allow_html=True)
          with cd:
            if is_superadmin:
              btn_css = "" if dark else """<style>
              div[data-testid^="stButton"] button,
              section button[kind="secondary"],
              .element-container button {
                  background-color: #1a56a0 !important;
                  background: #1a56a0 !important;
                  color: #ffffff !important;
                  fill: #ffffff !important;
                  border: none !important;
                  font-weight: 600 !important;
              }
              div[data-testid^="stButton"] button *,
              .element-container button * {
                  color: #ffffff !important;
                  fill: #ffffff !important;
                  -webkit-text-fill-color: #ffffff !important;
              }
              </style>"""
              st.markdown(btn_css, unsafe_allow_html=True)
              if st.button("Modifier MDP", key=f"chpwd_{email}", help=f"Changer MDP de {email}"):
                st.session_state[f"show_chpwd_{email}"] = True
            else:
              st.markdown(f'<div style="text-align:center;color:{text_sub};padding:8px 0;font-size:0.8rem;">🔒</div>', unsafe_allow_html=True)
          with ce:
            if is_me:
              st.markdown(f'<div style="text-align:center;color:{text_sub};padding:8px 0;">—</div>', unsafe_allow_html=True)
            elif is_superadmin:
              if st.button("Supprimer", key=f"del_btn_{email}", help=f"Supprimer {email}"):
                st.session_state[f"confirm_del_{email}"] = True
            else:
              st.markdown(f'<div style="text-align:center;color:{text_sub};padding:8px 0;font-size:0.8rem;">🔒</div>', unsafe_allow_html=True)

          if st.session_state.get(f"confirm_del_{email}"):
            st.markdown(f'<div style="background:{"#2d1515" if dark else "#fef2f2"};border:2px solid #fca5a5;border-radius:8px;padding:10px 14px;margin:4px 0 8px;">⚠️ <b style="color:#dc2626;">Confirmer la suppression de <code>{email}</code> ?</b></div>', unsafe_allow_html=True)
            cc1, cc2 = st.columns(2)
            with cc1:
              if st.button("Confirmer", key=f"confirm_yes_{email}", type="primary"):
                delete_account(email)
                st.session_state.pop(f"confirm_del_{email}", None)
                st.success(f"Compte {email} supprimé.")
                st.rerun()
            with cc2:
              if st.button("Annuler", key=f"confirm_no_{email}"):
                st.session_state.pop(f"confirm_del_{email}", None)
                st.rerun()

          if st.session_state.get(f"show_chpwd_{email}"):
            with st.form(key=f"form_chpwd_{email}"):
              st.markdown(f"**Changer le mot de passe de {info['nom']}**")
              old_p = st.text_input("Ancien mot de passe", type="password", key=f"op_{email}")
              new_p = st.text_input("Nouveau mot de passe", type="password", key=f"np_{email}")
              conf_p = st.text_input("Confirmer le nouveau mot de passe", type="password", key=f"cp_{email}")
              s1, s2 = st.columns(2)
              save_p  = s1.form_submit_button("Enregistrer", type="primary")
              cancel_p = s2.form_submit_button("Annuler", type="secondary")
            if save_p:
              from modules.login import load_accounts as _la, save_accounts as _sa, check_password as _chk
              if not _chk(email, old_p):
                st.error("❌ Ancien mot de passe incorrect.")
              elif len(new_p) < 8:
                st.error("❌ Minimum 8 caractères.")
              elif new_p != conf_p:
                st.error("❌ Les mots de passe ne correspondent pas.")
              else:
                _acc = _la()
                _acc[email]["hash"] = hashlib.sha256(new_p.encode()).hexdigest()
                _sa(_acc)
                st.session_state.pop(f"show_chpwd_{email}", None)
                st.success(f"Mot de passe de {info['nom']} modifié.")
                st.rerun()
            if cancel_p:
              st.session_state.pop(f"show_chpwd_{email}", None)
              st.rerun()

        st.markdown("---")
        import pandas as _pd
        acc_df = _pd.DataFrame([{"Nom": v['nom'], "Email": e, "Rôle": v['role']} for e, v in accounts.items()])
        _buf = _io.BytesIO()
        with _pd.ExcelWriter(_buf, engine='openpyxl') as _w:
          acc_df.to_excel(_w, index=False, sheet_name='Comptes')
        ec1, ec2 = st.columns(2)
        with ec1:
          st.download_button("Exporter en Excel", data=_buf.getvalue(),
                    file_name="comptes_acces_ENSA.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="btn_export_accounts_xlsx", use_container_width=True)
        with ec2:
          _csv = acc_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
          st.download_button("Exporter en CSV", data=_csv,
                    file_name="comptes_acces_ENSA.csv", mime="text/csv",
                    key="btn_export_accounts_csv", use_container_width=True)

      with sub2:
        if not is_superadmin:
          st.markdown('<div style="background:#fef2f2;border:2px solid #fca5a5;border-radius:10px;padding:14px 16px;text-align:center;"><div style="font-size:1.5rem;">🔒</div><b style="color:#dc2626;">Accès refusé</b><div style="color:#7f1d1d;font-size:0.82rem;margin-top:4px;">Seul le Super Administrateur peut créer des comptes.</div></div>', unsafe_allow_html=True)
        else:
          with st.form("add_account_form"):
            col_n1, col_n2 = st.columns(2)
            with col_n1:
              new_nom  = st.text_input("Nom complet *",   placeholder="Pr. ALAMI Youssef")
              new_email = st.text_input("Email @uca.ac.ma *", placeholder="y.alami@uca.ac.ma")
            with col_n2:
              new_role = st.selectbox("Rôle *", ["Professeur","Secrétaire","Administration","Responsable Bibliothèque"])
              new_pwd = st.text_input("Mot de passe *", type="password")
              conf_pwd = st.text_input("Confirmer *",  type="password")
            add_btn = st.form_submit_button("Créer le compte", type="primary")

          if add_btn:
            errs = []
            email_lower = new_email.strip().lower()
            if not new_nom.strip():                  errs.append("Nom obligatoire.")
            if not email_lower.endswith("@uca.ac.ma"):       errs.append("Email doit se terminer par @uca.ac.ma.")
            if email_lower in accounts:               errs.append("Ce compte existe déjà.")
            if not is_email_allowed(email_lower):          errs.append("Cet email n'est pas autorisé par la liste des utilisateurs autorisés.")
            if len(new_pwd) < 8:                   errs.append("Minimum 8 caractères.")
            if new_pwd != conf_pwd:                  errs.append("Mots de passe différents.")
            if errs:
              for e in errs: st.error(f"❌ {e}")
            else:
              add_account(email_lower, new_pwd, new_role, new_nom.strip())
              st.success(f"Compte créé — {new_nom} ({new_email}) — {new_role}")
              st.rerun()
