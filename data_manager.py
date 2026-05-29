import pandas as pd
import os
from datetime import datetime

DATA_FILE   = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data",    "etudiants.csv")
UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")

COLUMNS = [
    "num_ordre", "nom", "prenom", "email", "filiere", "annee",
    "intitule_rapport", "encadrant", "co_encadrant", "lieu_stage",
    "date_depot_secretariat", "correction", "nb_copies_bibliotheque",
    "pdf_filename", "date_soumission"
]

def ensure_dirs():
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    os.makedirs(UPLOADS_DIR, exist_ok=True)

def load_data():
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

def save_data(df):
    ensure_dirs()
    df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

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

def add_student(data: dict, pdf_file=None) -> dict:
    ensure_dirs()
    df = load_data()
    data['num_ordre']      = get_next_num_ordre(data.get('annee', ''))
    data['date_soumission'] = datetime.now().strftime("%Y-%m-%d %H:%M")
    data['date_depot_secretariat'] = data['date_soumission']
    pdf_filename = ""
    if pdf_file is not None:
        safe = f"{data['num_ordre']}_{data['nom']}_{data['prenom']}_{data['annee']}.pdf"
        safe = safe.replace(" ", "_").replace("/", "-")
        pdf_path = os.path.join(UPLOADS_DIR, safe)
        with open(pdf_path, "wb") as f:
            # Compatible Streamlit UploadedFile (.getbuffer()) et Flask FileStorage (.read())
            if hasattr(pdf_file, "getbuffer"):
                f.write(pdf_file.getbuffer())
            elif hasattr(pdf_file, "read"):
                f.write(pdf_file.read())
            else:
                f.write(bytes(pdf_file))
        pdf_filename = safe
    data['pdf_filename'] = pdf_filename
    new_row = pd.DataFrame([{col: data.get(col, "") for col in COLUMNS}])
    df = pd.concat([df, new_row], ignore_index=True)
    save_data(df)
    return data

def get_pdf_path(filename):
    return os.path.join(UPLOADS_DIR, filename)

def update_student(num_ordre, updates: dict):
    df = load_data()
    mask = df['num_ordre'].astype(str) == str(num_ordre)
    for key, val in updates.items():
        if key in df.columns:
            df.loc[mask, key] = val
    save_data(df)

def delete_student(num_ordre):
    df = load_data()
    row = df[df['num_ordre'].astype(str) == str(num_ordre)]
    if not row.empty:
        pdf_file = row.iloc[0]['pdf_filename']
        # Fix: handle NaN (float) when pdf_filename is empty in CSV
        if isinstance(pdf_file, str) and pdf_file.strip():
            path = get_pdf_path(pdf_file)
            if os.path.exists(path):
                os.remove(path)
    df = df[df['num_ordre'].astype(str) != str(num_ordre)]
    save_data(df)

def clear_all_students():
    """Vide toute la base étudiants et supprime les PDFs associés."""
    ensure_dirs()
    df = load_data()
    for _, row in df.iterrows():
        pdf_file = row.get('pdf_filename', '')
        if isinstance(pdf_file, str) and pdf_file.strip():
            path = get_pdf_path(pdf_file)
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass
    pd.DataFrame(columns=COLUMNS).to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

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
                    new_data['num_ordre']             = get_next_num_ordre(new_data.get('annee', ''))
                    new_data['date_soumission']       = now_str
                    new_data['date_depot_secretariat'] = now_str
                    new_data['pdf_filename']          = ''
                    new_row = pd.DataFrame([new_data])
                    df = pd.concat([df, new_row], ignore_index=True)
                    save_data(df)
                    added += 1
        return added, None
    except Exception as e:
        return 0, str(e)
