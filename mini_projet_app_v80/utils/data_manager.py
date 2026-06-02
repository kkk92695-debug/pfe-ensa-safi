import pandas as pd
import os
import requests
import base64
from datetime import datetime

# ── Supabase config ────────────────────────────────────────────────────────────
import streamlit as st

def _get_supabase_url():
    try:
        return st.secrets["SUPABASE_URL"]
    except Exception:
        return os.environ.get("SUPABASE_URL", "")

def _get_supabase_key():
    try:
        return st.secrets["SUPABASE_KEY"]
    except Exception:
        return os.environ.get("SUPABASE_KEY", "")

TABLE = "etudiants"
STORAGE_BUCKET = "pdfs"

COLUMNS = [
    "num_ordre", "nom", "prenom", "email", "filiere", "annee",
    "intitule_rapport", "encadrant", "co_encadrant", "lieu_stage",
    "date_depot_secretariat", "correction", "nb_copies_bibliotheque",
    "pdf_filename", "date_soumission"
]

# ── Fallback local (si Supabase non configuré) ─────────────────────────────────
DATA_FILE   = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "etudiants.csv")
UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")

def _use_supabase():
    return bool(_get_supabase_url() and _get_supabase_key())

def _headers():
    return {
        "apikey": _get_supabase_key(),
        "Authorization": f"Bearer {_get_supabase_key()}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

def ensure_dirs():
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    os.makedirs(UPLOADS_DIR, exist_ok=True)

# ── LOAD ───────────────────────────────────────────────────────────────────────
def load_data():
    if _use_supabase():
        try:
            url = f"{_get_supabase_url()}/rest/v1/{TABLE}?select=*&order=num_ordre.asc"
            r = requests.get(url, headers=_headers(), timeout=10)
            if r.status_code == 200:
                data = r.json()
                if not data:
                    return pd.DataFrame(columns=COLUMNS)
                df = pd.DataFrame(data)
                for col in COLUMNS:
                    if col not in df.columns:
                        df[col] = ""
                return df[COLUMNS]
            else:
                return pd.DataFrame(columns=COLUMNS)
        except Exception:
            return pd.DataFrame(columns=COLUMNS)
    else:
        ensure_dirs()
        if os.path.exists(DATA_FILE):
            try:
                df = pd.read_csv(DATA_FILE, encoding='utf-8-sig')
                for col in COLUMNS:
                    if col not in df.columns:
                        df[col] = ""
                return df
            except Exception:
                return pd.DataFrame(columns=COLUMNS)
        return pd.DataFrame(columns=COLUMNS)

# ── SAVE (local fallback) ──────────────────────────────────────────────────────
def save_data(df):
    ensure_dirs()
    df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

# ── NUM ORDRE ──────────────────────────────────────────────────────────────────
def get_next_num_ordre(annee: str = None) -> str:
    df = load_data()
    if annee and "-" in str(annee):
        year_suffix = str(annee).split("-")[-1][-2:]
    else:
        year_suffix = str(datetime.now().year)[-2:]
    prefix = f"{year_suffix}-"
    if df.empty:
        return f"{prefix}001"
    same_year = df[df['num_ordre'].astype(str).str.startswith(prefix)]['num_ordre'].astype(str)
    if same_year.empty:
        return f"{prefix}001"
    try:
        max_seq = same_year.str.replace(prefix, "", regex=False).astype(int).max()
        return f"{prefix}{max_seq + 1:03d}"
    except Exception:
        return f"{prefix}{len(same_year) + 1:03d}"

# ── UPLOAD PDF vers Supabase Storage ──────────────────────────────────────────
def _upload_pdf_supabase(pdf_bytes: bytes, filename: str) -> bool:
    try:
        # Essayer upsert (remplace si existe)
        url = f"{_get_supabase_url()}/storage/v1/object/{STORAGE_BUCKET}/{filename}"
        headers = {
            "apikey": _get_supabase_key(),
            "Authorization": f"Bearer {_get_supabase_key()}",
            "Content-Type": "application/pdf",
            "x-upsert": "true",
        }
        r = requests.post(url, headers=headers, data=pdf_bytes, timeout=30)
        return r.status_code in (200, 201)
    except Exception:
        return False

def get_pdf_url(filename: str) -> str:
    if _use_supabase() and filename:
        return f"{_get_supabase_url()}/storage/v1/object/public/{STORAGE_BUCKET}/{filename}"
    return ""

# ── ADD STUDENT ────────────────────────────────────────────────────────────────
def add_student(data: dict, pdf_file=None) -> dict:
    data['num_ordre']              = get_next_num_ordre(data.get('annee', ''))
    data['date_soumission']        = datetime.now().strftime("%Y-%m-%d %H:%M")
    data['date_depot_secretariat'] = data['date_soumission']

    pdf_filename = ""
    if pdf_file is not None:
        safe = f"{data['num_ordre']}_{data['nom']}_{data['prenom']}_{data['annee']}.pdf"
        safe = safe.replace(" ", "_").replace("/", "-")
        if hasattr(pdf_file, "getbuffer"):
            pdf_bytes = bytes(pdf_file.getbuffer())
        elif hasattr(pdf_file, "read"):
            pdf_bytes = pdf_file.read()
        else:
            pdf_bytes = bytes(pdf_file)

        if _use_supabase():
            _upload_pdf_supabase(pdf_bytes, safe)
        else:
            ensure_dirs()
            with open(os.path.join(UPLOADS_DIR, safe), "wb") as f:
                f.write(pdf_bytes)
        pdf_filename = safe

    data['pdf_filename'] = pdf_filename

    if _use_supabase():
        try:
            row = {col: data.get(col, "") for col in COLUMNS}
            url = f"{_get_supabase_url()}/rest/v1/{TABLE}"
            r = requests.post(url, headers=_headers(), json=row, timeout=10)
        except Exception:
            pass
    else:
        ensure_dirs()
        df = load_data()
        new_row = pd.DataFrame([{col: data.get(col, "") for col in COLUMNS}])
        df = pd.concat([df, new_row], ignore_index=True)
        save_data(df)

    return data

# ── GET PDF PATH (local) ───────────────────────────────────────────────────────
def get_pdf_path(filename):
    return os.path.join(UPLOADS_DIR, filename)

# ── UPDATE STUDENT ─────────────────────────────────────────────────────────────
def update_student(num_ordre, updates: dict):
    if _use_supabase():
        try:
            url = f"{_get_supabase_url()}/rest/v1/{TABLE}?num_ordre=eq.{num_ordre}"
            r = requests.patch(url, headers=_headers(), json=updates, timeout=10)
        except Exception:
            pass
    else:
        df = load_data()
        mask = df['num_ordre'].astype(str) == str(num_ordre)
        for key, val in updates.items():
            if key in df.columns:
                df.loc[mask, key] = val
        save_data(df)

# ── DELETE STUDENT ─────────────────────────────────────────────────────────────
def delete_student(num_ordre):
    if _use_supabase():
        try:
            df = load_data()
            row = df[df['num_ordre'].astype(str) == str(num_ordre)]
            if not row.empty:
                pdf_file = row.iloc[0].get('pdf_filename', '')
                if isinstance(pdf_file, str) and pdf_file.strip():
                    del_url = f"{_get_supabase_url()}/storage/v1/object/{STORAGE_BUCKET}/{pdf_file}"
                    requests.delete(del_url, headers=_headers(), timeout=10)
            url = f"{_get_supabase_url()}/rest/v1/{TABLE}?num_ordre=eq.{num_ordre}"
            requests.delete(url, headers=_headers(), timeout=10)
        except Exception:
            pass
    else:
        df = load_data()
        row = df[df['num_ordre'].astype(str) == str(num_ordre)]
        if not row.empty:
            pdf_file = row.iloc[0]['pdf_filename']
            if isinstance(pdf_file, str) and pdf_file.strip():
                path = get_pdf_path(pdf_file)
                if os.path.exists(path):
                    os.remove(path)
        df = df[df['num_ordre'].astype(str) != str(num_ordre)]
        save_data(df)

# ── CLEAR ALL ──────────────────────────────────────────────────────────────────
def clear_all_students():
    if _use_supabase():
        try:
            url = f"{_get_supabase_url()}/rest/v1/{TABLE}?num_ordre=neq.null"
            requests.delete(url, headers=_headers(), timeout=10)
        except Exception:
            pass
    else:
        ensure_dirs()
        pd.DataFrame(columns=COLUMNS).to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

# ── IMPORT EXCEL ───────────────────────────────────────────────────────────────
def import_from_excel(excel_file):
    try:
        xl_df = pd.read_excel(excel_file, engine='openpyxl')
        col_map = {
            'Nom':'nom','NOM':'nom','nom':'nom',
            'Prénom':'prenom','PRENOM':'prenom','prenom':'prenom','Prenom':'prenom',
            'Email':'email','email':'email','EMAIL':'email',
            'Filière':'filiere','Filiere':'filiere','FILIERE':'filiere','filiere':'filiere',
            'Année':'annee','Annee':'annee','ANNEE':'annee','annee':'annee',
            'Intitulé':'intitule_rapport','Intitule':'intitule_rapport','intitule_rapport':'intitule_rapport',
            'Encadrant':'encadrant','encadrant':'encadrant',
            'Co-encadrant':'co_encadrant','Co_encadrant':'co_encadrant',
            'Lieu de stage':'lieu_stage','lieu_stage':'lieu_stage',
            'Date dépôt':'date_depot_secretariat','date_depot_secretariat':'date_depot_secretariat',
            'Correction':'correction','correction':'correction',
            'Copies bibliothèque':'nb_copies_bibliotheque','nb_copies_bibliotheque':'nb_copies_bibliotheque',
        }
        xl_df = xl_df.rename(columns=col_map)
        df = load_data()
        added = 0
        for _, row in xl_df.iterrows():
            nom    = str(row.get('nom',    '')).strip()
            prenom = str(row.get('prenom', '')).strip()
            if nom and prenom:
                exists = not df[
                    (df['nom'].astype(str).str.strip()    == nom) &
                    (df['prenom'].astype(str).str.strip() == prenom)
                ].empty
                if not exists:
                    new_data = {col: row.get(col, '') for col in COLUMNS}
                    now_str  = datetime.now().strftime("%Y-%m-%d %H:%M")
                    new_data['num_ordre']              = get_next_num_ordre(new_data.get('annee', ''))
                    new_data['date_soumission']        = now_str
                    new_data['date_depot_secretariat'] = now_str
                    new_data['pdf_filename']           = ''
                    add_student(new_data)
                    added += 1
        return added, None
    except Exception as e:
        return 0, str(e)
