"""
formulaire_etudiant.py — Application séparée pour les étudiants UNIQUEMENT
Lancer : streamlit run formulaire_etudiant.py --server.port 8502
"""
import streamlit as st

st.set_page_config(
    page_title="Dépôt Rapport PFE — ENSA Safi",
    page_icon="📚",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
[data-testid="stSidebar"] {display: none !important;}
</style>
""", unsafe_allow_html=True)

# Initialiser form_step si absent
if "form_step" not in st.session_state:
    st.session_state.form_step = 1

from modules.etudiant import show_etudiant_page
show_etudiant_page()
