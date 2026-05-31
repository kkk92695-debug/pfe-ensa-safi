import streamlit as st

st.set_page_config(
    page_title="Gestion Rapports PFE — ENSA Safi",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

dark = st.session_state.dark_mode

# ── CSS global (thème clair / sombre) ───────────────────────────────────────
if dark:
    theme_css = """
    <style>
    #MainMenu, footer, header { visibility: hidden; }
    .stApp { background: #0f1117 !important; }
    .stApp p, .stApp span, .stApp div, .stApp li,
    .stApp h1, .stApp h2, .stApp h3, .stApp h4 { color: #e2e8f0 !important; }
    .stTabs [data-baseweb="tab-list"] { background: #1e2130 !important; border-radius: 10px; }
    .stTabs [data-baseweb="tab"] { color: #94a3b8 !important; }
    .stTabs [aria-selected="true"] { background: #2d3748 !important; color: #60a5fa !important; border-radius: 8px; }
    .stTextInput input, .stTextArea textarea, div[data-baseweb="select"] > div {
        background: #1e2130 !important; border-color: #374151 !important; color: #e2e8f0 !important;
    }
    .stButton > button { background: #1e2130 !important; border-color: #4b5563 !important; color: #e2e8f0 !important; }
    .stButton > button[kind="primary"] { background: linear-gradient(135deg,#1a56a0,#2563eb) !important; border:none !important; color:white !important; }
    [data-testid="stFileUploader"] { background: #1e2130 !important; border-color: #4b5563 !important; border-radius: 10px !important; }
    label { color: #94a3b8 !important; }
    hr { border-color: #2d3748 !important; }
    </style>
    """
else:
    theme_css = """
    <style>
    #MainMenu, footer, header { visibility: hidden; }
    .stApp { background: #f0f4f8 !important; }

    /* Tout le texte en noir */
    .stApp p, .stApp span, .stApp div,
    .stApp li, .stApp h1, .stApp h2, .stApp h3, .stApp h4 { color: #0f172a !important; }

    /* Labels */
    label, .stTextInput label, .stSelectbox label,
    .stTextArea label, .stNumberInput label,
    .stFileUploader label, [data-testid="stWidgetLabel"] {
        color: #0f172a !important; font-weight: 600 !important;
    }

    /* Inputs texte */
    .stTextInput input, .stTextArea textarea {
        background: #ffffff !important;
        border: 1.5px solid #cbd5e1 !important;
        color: #0f172a !important; font-weight: 500 !important;
    }
    .stTextInput input::placeholder,
    .stTextArea textarea::placeholder { color: #94a3b8 !important; }

    /* Selectbox */
    div[data-baseweb="select"] > div {
        background: #ffffff !important; border-color: #cbd5e1 !important; color: #0f172a !important;
    }
    div[data-baseweb="select"] span,
    div[data-baseweb="select"] div { color: #0f172a !important; }
    [data-baseweb="menu"] { background: #ffffff !important; }
    [data-baseweb="menu"] li { color: #0f172a !important; background: #ffffff !important; }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { background: #e8eef7 !important; border-radius: 10px; }
    .stTabs [data-baseweb="tab"] { color: #374151 !important; font-weight: 600 !important; }
    .stTabs [aria-selected="true"] { background: white !important; color: #1a56a0 !important; border-radius: 8px; }

    /* File uploader */
    [data-testid="stFileUploaderDropzone"] { background: #f8fafc !important; border-color: #cbd5e1 !important; }
    [data-testid="stFileUploaderDropzone"] * { color: #374151 !important; }

    /* Boutons default : fond blanc, texte noir */
    .stButton > button {
        background: #ffffff !important;
        border: 1.5px solid #cbd5e1 !important;
        font-weight: 600 !important;
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
    }
    .stButton > button p,
    .stButton > button span,
    .stButton > button div {
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
        font-weight: 600 !important;
    }
    .stButton > button:hover {
        background: #f8fafc !important;
        border-color: #94a3b8 !important;
    }
    /* Boutons primary : bleu, texte blanc */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg,#1a56a0,#2563eb) !important;
        border: none !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    .stButton > button[kind="primary"] p,
    .stButton > button[kind="primary"] span {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    /* Download buttons : toujours bleu + texte blanc */
    .stDownloadButton > button {
        background: linear-gradient(135deg,#1a56a0,#2563eb) !important;
        border: none !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-weight: 600 !important;
    }
    .stDownloadButton > button p,
    .stDownloadButton > button span,
    .stDownloadButton > button div {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-weight: 600 !important;
    }

    /* Dataframe */
    [data-testid="stDataFrame"], [data-testid="stDataFrame"] * { color: #0f172a !important; }

    /* Texte blanc sur fonds colorés */
    .stApp div[style*="background:linear-gradient"] *,
    .stApp div[style*="background:#0f2557"] *, .stApp div[style*="background:#1a56a0"] *,
    .stApp div[style*="background:#1e2130"] *, .stApp div[style*="background:#1a2744"] *,
    .stApp div[style*="background:#1d4ed8"] *, .stApp div[style*="background:#15803d"] *,
    .stApp div[style*="background:#16a34a"] *, .stApp div[style*="background:#dc2626"] * {
        color: #ffffff !important;
    }

    /* Number input */
    .stNumberInput input { background: #ffffff !important; color: #0f172a !important; border-color: #cbd5e1 !important; }

    /* Checkbox */
    .stCheckbox label span { color: #0f172a !important; }

    /* Expander */
    [data-testid="stExpander"] summary span { color: #0f172a !important; font-weight: 600 !important; }

    /* Form submit buttons (secondary = Annuler) */
    button[kind="secondaryFormSubmit"] {
        color: #0f172a !important;
        background: #ffffff !important;
        border: 1.5px solid #cbd5e1 !important;
        font-weight: 600 !important;
    }
    button[kind="primaryFormSubmit"] {
        background: linear-gradient(135deg,#1a56a0,#2563eb) !important;
        border: none !important; color: #ffffff !important;
        font-weight: 600 !important;
    }

    /* Download button */
    .stDownloadButton > button {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        background: #1a56a0 !important;
        border: none !important;
        font-weight: 600 !important;
    }
    </style>
    """

st.markdown(theme_css, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# ROUTAGE : si ?page=etudiant → formulaire public (sans login)
# ═══════════════════════════════════════════════════════════════════════════
query_params = st.query_params
if query_params.get("page") == "etudiant":
    # Masquer la sidebar complètement
    st.markdown("""
    <style>
    [data-testid="stSidebar"] { display: none !important; }
    .stApp { background: #f0f4f8 !important; }
    </style>
    """, unsafe_allow_html=True)

    # Initialiser le step du formulaire
    if "form_step" not in st.session_state:
        st.session_state.form_step = 1

    from modules.etudiant import show_etudiant_page
    show_etudiant_page()
    st.stop()

# ═══════════════════════════════════════════════════════════════════════════
# SINON : dashboard avec login
# ═══════════════════════════════════════════════════════════════════════════
if not st.session_state.get("logged_in"):
    from modules.login import show_login_page
    show_login_page()
    st.stop()

if "page" not in st.session_state:
    st.session_state.page = "dashboard"

if st.session_state.page == "dashboard":
    from modules.dashboard import show_dashboard_page
    show_dashboard_page()
