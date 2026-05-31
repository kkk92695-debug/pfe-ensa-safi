import streamlit as st
import hashlib, json, os, base64, random, string, time
import pandas as pd

_BASE        = os.path.dirname(os.path.dirname(__file__))
ACCOUNTS_FILE= os.path.join(_BASE, "data", "accounts.json")
ALLOWED_FILE = os.path.join(_BASE, "data", "utilisateurs_autorises.xlsx")
TOKENS_FILE  = os.path.join(_BASE, "data", "reset_tokens.json")
ASSETS_DIR   = os.path.join(_BASE, "assets")

SUPER_ADMIN  = "admin@uca.ac.ma"
MAX_ATTEMPTS = 5
TOKEN_EXPIRY  = 15 * 60  # 15 minutes en secondes

DEFAULT_ACCOUNTS = {
    "admin@uca.ac.ma": {
        "hash": hashlib.sha256("Admin@ENSA2025".encode()).hexdigest(),
        "role": "Administration", "nom": "Administrateur"
    },
}

# ── Helpers comptes ─────────────────────────────────────────────────────────
def _ensure_data():
    os.makedirs(os.path.join(_BASE, "data"), exist_ok=True)
    if not os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_ACCOUNTS, f, ensure_ascii=False, indent=2)

def load_accounts():
    _ensure_data()
    with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_accounts(accounts):
    _ensure_data()
    with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
        json.dump(accounts, f, ensure_ascii=False, indent=2)

def add_account(email, password, role, nom):
    accounts = load_accounts()
    accounts[email.lower().strip()] = {
        "hash": hashlib.sha256(password.encode()).hexdigest(),
        "role": role, "nom": nom
    }
    save_accounts(accounts)

def delete_account(email):
    accounts = load_accounts()
    accounts.pop(email.lower().strip(), None)
    save_accounts(accounts)

def account_exists(email):
    return email.lower().strip() in load_accounts()

def check_password(email, password):
    accounts = load_accounts()
    h = hashlib.sha256(password.encode()).hexdigest()
    return email in accounts and accounts[email]["hash"] == h

# ── Helpers liste autorisée ─────────────────────────────────────────────────
def load_allowed_emails():
    if not os.path.exists(ALLOWED_FILE):
        return {SUPER_ADMIN: {"nom": "Administrateur", "role": "Administration"}}
    try:
        df = pd.read_excel(ALLOWED_FILE, engine="openpyxl")
        df.columns = [c.strip() for c in df.columns]
        col_map = {
            "Email":"email","email":"email","EMAIL":"email",
            "Nom":"nom","NOM":"nom","nom":"nom",
            "Rôle":"role","Role":"role","ROLE":"role","role":"role",
        }
        df = df.rename(columns=col_map)
        result = {}
        for _, row in df.iterrows():
            email = str(row.get("email","")).strip().lower()
            if email and "@uca.ac.ma" in email:
                result[email] = {
                    "nom":  str(row.get("nom","")).strip(),
                    "role": str(row.get("role","Professeur")).strip(),
                }
        if SUPER_ADMIN not in result:
            result[SUPER_ADMIN] = {"nom": "Administrateur", "role": "Administration"}
        return result
    except Exception:
        return {SUPER_ADMIN: {"nom": "Administrateur", "role": "Administration"}}

def save_allowed_excel(df_allowed):
    os.makedirs(os.path.join(_BASE, "data"), exist_ok=True)
    df_allowed.to_excel(ALLOWED_FILE, index=False, engine="openpyxl")

def is_email_allowed(email):
    return email.lower().strip() in load_allowed_emails()

def get_allowed_info(email):
    return load_allowed_emails().get(email.lower().strip(), {})

# ── Helpers tokens reset ────────────────────────────────────────────────────
def _load_tokens():
    if not os.path.exists(TOKENS_FILE):
        return {}
    with open(TOKENS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def _save_tokens(tokens):
    os.makedirs(os.path.join(_BASE, "data"), exist_ok=True)
    with open(TOKENS_FILE, "w", encoding="utf-8") as f:
        json.dump(tokens, f)

def generate_reset_token(email):
    """Génère un code 6 chiffres + l'enregistre avec expiration 15 min."""
    code = "".join(random.choices(string.digits, k=6))
    tokens = _load_tokens()
    tokens[email.lower()] = {
        "code":    code,
        "expires": time.time() + TOKEN_EXPIRY,
        "used":    False
    }
    _save_tokens(tokens)
    return code

def verify_reset_token(email, code):
    """Vérifie le code. Retourne True si valide et non expiré."""
    tokens = _load_tokens()
    entry  = tokens.get(email.lower())
    if not entry:
        return False, "Code introuvable."
    if entry["used"]:
        return False, "Ce code a déjà été utilisé."
    if time.time() > entry["expires"]:
        return False, "Code expiré (15 min). Demandez-en un nouveau."
    if entry["code"] != code.strip():
        return False, "Code incorrect."
    return True, "OK"

def invalidate_token(email):
    """Invalide le token après usage."""
    tokens = _load_tokens()
    if email.lower() in tokens:
        tokens[email.lower()]["used"] = True
        _save_tokens(tokens)

def apply_new_password(email, new_password):
    """Change le mot de passe dans accounts.json."""
    accounts = load_accounts()
    if email in accounts:
        accounts[email]["hash"] = hashlib.sha256(new_password.encode()).hexdigest()
        save_accounts(accounts)
        return True
    return False

# ── Image helper ────────────────────────────────────────────────────────────
def _img_b64(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return None

# ── CSS commun login ─────────────────────────────────────────────────────────
def _inject_css(bg_b64):
    bg_css = (
        f'.stApp{{background-image:url("data:image/png;base64,{bg_b64}");'
        'background-size:cover;background-position:center;background-attachment:fixed;}}'
        '.stApp::before{content:"";position:fixed;inset:0;background:rgba(10,25,60,0.72);z-index:0;}'
        '.stApp > *{position:relative;z-index:1;}'
    ) if bg_b64 else ".stApp{background:linear-gradient(135deg,#0f2557,#1a3a6b);}"

    st.markdown(f"""
    <style>
    {bg_css}
    #MainMenu,footer,header{{visibility:hidden;}}
    .login-card .stTextInput input{{
        background:#ffffff!important;
        border:1.5px solid #cbd5e1!important;
        border-radius:10px!important;color:#0f172a!important;font-size:0.92rem!important;
    }}
    .stTextInput input{{
        background:#ffffff!important;
        border:1.5px solid #cbd5e1!important;
        border-radius:10px!important;color:#0f172a!important;font-size:0.92rem!important;
    }}
    .stTextInput input:focus{{border-color:#2563eb!important;background:#ffffff!important;box-shadow:0 0 0 3px rgba(37,99,235,0.12)!important;}}
    .stTextInput input::placeholder{{color:#94a3b8!important;}}
    .stTextInput label{{color:#1e293b!important;font-size:0.85rem!important;font-weight:700!important;}}
    .stSelectbox label{{color:#1e293b!important;font-size:0.85rem!important;font-weight:700!important;}}
    .stButton>button[kind="primary"]{{
        background:linear-gradient(135deg,#2563eb,#1d4ed8)!important;border:none!important;
        border-radius:10px!important;font-weight:700!important;padding:0.68rem!important;
        box-shadow:0 4px 18px rgba(37,99,235,0.45)!important;letter-spacing:0.03em!important;
        color:white!important;
    }}
    .stButton>button[kind="secondary"]{{
        background:rgba(255,255,255,0.95)!important;
        border:1.5px solid #cbd5e1!important;
        border-radius:10px!important;
        color:#1e293b!important;
        font-size:0.85rem!important;
        font-weight:600!important;
        box-shadow:0 2px 8px rgba(0,0,0,0.08)!important;
    }}
    .stButton>button[kind="secondary"]:hover{{
        background:#ffffff!important;
        border-color:#2563eb!important;
        color:#2563eb!important;
        transform:translateY(-1px)!important;
    }}
    </style>""", unsafe_allow_html=True)

def _card_header(logo_html, subtitle="Espace Encadrants &amp; Administration"):
    html = (
        '<div style="background:#ffffff;border-radius:20px;'
        'padding:2rem 2rem 1.6rem;margin-top:3vh;'
        'box-shadow:0 24px 64px rgba(0,0,0,0.35);border:1px solid rgba(255,255,255,0.6);">'
        '<div style="text-align:center;margin-bottom:1.4rem;">'
        + logo_html +
        '<div style="color:#0f2557;font-size:1.05rem;font-weight:700;line-height:1.3;margin-top:8px;">'
        'École Nationale des Sciences Appliquées<br>'
        '<span style="color:#64748b;font-size:0.82rem;font-weight:400;">'
        'Safi — Université Cadi Ayyad</span></div>'
        '<div style="width:40px;height:3px;background:linear-gradient(90deg,#2563eb,#60a5fa);'
        'border-radius:2px;margin:10px auto;"></div>'
        f'<div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;'
        f'padding:6px 14px;display:inline-block;color:#1d4ed8;font-size:0.85rem;font-weight:700;">'
        f'🔐 {subtitle}</div>'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE PRINCIPALE — dispatch selon auth_mode
# ══════════════════════════════════════════════════════════════════════════════
def show_login_page():
    bg_b64   = _img_b64(os.path.join(ASSETS_DIR, "ensas_bg.png"))
    logo_b64 = _img_b64(os.path.join(ASSETS_DIR, "logo_ensa.jpg"))
    logo_html = (
        f'<img src="data:image/jpeg;base64,{logo_b64}" '
        'style="height:55px;margin-bottom:10px;border-radius:8px;" />'
    ) if logo_b64 else '<div style="font-size:2.5rem;margin-bottom:10px;">🎓</div>'

    _inject_css(bg_b64)

    if "login_attempts" not in st.session_state:
        st.session_state.login_attempts = 0
    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "login"
    if "reset_email" not in st.session_state:
        st.session_state.reset_email = ""
    if "reset_step" not in st.session_state:
        st.session_state.reset_step = 1  # 1=email, 2=code, 3=nouveau mdp

    mode = st.session_state.auth_mode
    _, mid, _ = st.columns([1, 1.4, 1])
    with mid:
        if mode == "login":
            _page_login(logo_html)
        elif mode == "register":
            _page_register(logo_html)
        elif mode == "forgot":
            _page_forgot(logo_html)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : CONNEXION
# ══════════════════════════════════════════════════════════════════════════════
def _page_login(logo_html):
    _card_header(logo_html, "Connexion — Espace Encadrants")

    # Blocage tentatives
    if st.session_state.login_attempts >= MAX_ATTEMPTS:
        st.markdown("""
        <div style="background:rgba(239,68,68,0.18);border:1px solid rgba(239,68,68,0.4);
                    border-radius:10px;padding:10px 14px;color:#fca5a5;text-align:center;margin-bottom:1rem;">
            🔒 Accès bloqué. Contactez l'administrateur.
        </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        return

    # Indicateur tentatives
    if st.session_state.login_attempts > 0:
        dots = "".join([
            f'<div style="width:10px;height:10px;border-radius:50%;'
            f'background:{"#ef4444" if i < st.session_state.login_attempts else "rgba(255,255,255,0.2)"};"></div>'
            for i in range(MAX_ATTEMPTS)
        ])
        remaining = MAX_ATTEMPTS - st.session_state.login_attempts
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">'
            f'<div style="display:flex;gap:5px;">{dots}</div>'
            f'<span style="color:rgba(255,255,255,0.5);font-size:11px;">{remaining} tentative(s) restante(s)</span>'
            f'</div>', unsafe_allow_html=True)

    with st.form("form_login", clear_on_submit=False):
        email_inp = st.text_input("📧 Email institutionnel", placeholder="votre.nom@uca.ac.ma")
        pwd_inp   = st.text_input("🔑 Mot de passe", type="password", placeholder="••••••••")
        st.markdown("<br>", unsafe_allow_html=True)
        submit = st.form_submit_button("Se connecter →", use_container_width=True, type="primary")

    if submit:
        email = email_inp.strip().lower()
        if not email.endswith("@uca.ac.ma"):
            st.error("❌ Utilisez votre email @uca.ac.ma")
            st.session_state.login_attempts += 1
        elif not is_email_allowed(email):
            st.error("❌ Votre email ne figure pas dans la liste des utilisateurs autorisés.")
            st.session_state.login_attempts += 1
        elif not account_exists(email):
            # Email autorisé mais pas encore de compte
            st.warning("⚠️ Aucun compte trouvé pour cet email. Créez votre compte.")
            if st.button("→ Créer mon compte", key="goto_register_from_login"):
                st.session_state.auth_mode = "register"
                st.session_state.prefill_email = email
                st.rerun()
        elif not check_password(email, pwd_inp):
            st.session_state.login_attempts += 1
            remaining = MAX_ATTEMPTS - st.session_state.login_attempts
            st.error(f"❌ Mot de passe incorrect. ({remaining} tentative(s) restante(s))")
            if remaining <= 0:
                st.rerun()
        else:
            # ✅ Connexion réussie
            accounts = load_accounts()
            st.session_state.login_attempts = 0
            st.session_state.logged_in  = True
            st.session_state.username   = email
            st.session_state.role       = accounts[email]["role"]
            st.session_state.nom_user   = accounts[email]["nom"]
            st.session_state.page       = "dashboard"
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Boutons navigation
    c1, c2 = st.columns(2)
    with c1:
        if st.button("✨  Créer un compte", use_container_width=True,
                     key="goto_register", type="secondary"):
            st.session_state.auth_mode = "register"
            st.rerun()
    with c2:
        if st.button("🔑  Mot de passe oublié", use_container_width=True,
                     key="goto_forgot", type="secondary"):
            st.session_state.auth_mode = "forgot"
            st.session_state.reset_step = 1
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : CRÉER UN COMPTE
# ══════════════════════════════════════════════════════════════════════════════
def _page_register(logo_html):
    _card_header(logo_html, "Créer mon compte")

    st.markdown("""
    <div style="background:rgba(16,163,74,0.15);border:1px solid rgba(16,163,74,0.4);
                border-radius:8px;padding:9px 12px;font-size:0.8rem;color:#bbf7d0;margin-bottom:0.8rem;">
        ✅ Votre email doit être dans la liste des utilisateurs autorisés par l'administration.
    </div>""", unsafe_allow_html=True)

    prefill = st.session_state.get("prefill_email", "")

    with st.form("form_register", clear_on_submit=False):
        reg_email = st.text_input("📧 Email institutionnel", value=prefill, placeholder="votre.nom@uca.ac.ma")
        reg_pwd   = st.text_input("🔑 Mot de passe", type="password", placeholder="Min. 8 caractères")
        reg_conf  = st.text_input("🔑 Confirmer le mot de passe", type="password", placeholder="Répétez le mot de passe")
        st.markdown("<br>", unsafe_allow_html=True)
        submit = st.form_submit_button("✨ Créer mon compte", use_container_width=True, type="primary")

    if submit:
        email = reg_email.strip().lower()
        errors = []
        if not email.endswith("@uca.ac.ma"):
            errors.append("Email doit se terminer par @uca.ac.ma")
        if not is_email_allowed(email):
            errors.append("Cet email n'est pas dans la liste des utilisateurs autorisés.")
        if account_exists(email):
            errors.append("Un compte existe déjà pour cet email. Connectez-vous.")
        if len(reg_pwd) < 8:
            errors.append("Mot de passe : minimum 8 caractères.")
        if reg_pwd != reg_conf:
            errors.append("Les mots de passe ne correspondent pas.")

        if errors:
            for e in errors:
                st.error(f"❌ {e}")
        else:
            info = get_allowed_info(email)
            nom  = info.get("nom", email.split("@")[0])
            role = info.get("role", "Professeur")
            add_account(email, reg_pwd, role, nom)
            st.success(f"✅ Compte créé avec succès ! Bienvenue **{nom}**.")
            st.info("Vous pouvez maintenant vous connecter.")
            st.session_state.auth_mode = "login"
            st.session_state.prefill_email = ""
            st.rerun()

    if st.button("← Retour à la connexion", key="back_to_login_reg"):
        st.session_state.auth_mode = "login"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : MOT DE PASSE OUBLIÉ (3 étapes)
# ══════════════════════════════════════════════════════════════════════════════
def _page_forgot(logo_html):
    step = st.session_state.get("reset_step", 1)

    subtitles = {1:"Mot de passe oublié", 2:"Vérification du code", 3:"Nouveau mot de passe"}
    _card_header(logo_html, subtitles.get(step, "Réinitialisation"))

    # Barre de progression
    steps_html = ""
    for i in range(1, 4):
        if i < step:
            bg, tc = "#16a34a", "white"
            label = "✓"
        elif i == step:
            bg, tc = "#2563eb", "white"
            label = str(i)
        else:
            bg, tc = "rgba(255,255,255,0.15)", "rgba(255,255,255,0.4)"
            label = str(i)
        names = {1:"Email", 2:"Code", 3:"Nouveau MDP"}
        line_c = "#16a34a" if i < step else "rgba(255,255,255,0.2)"
        steps_html += (
            f'<div style="display:flex;flex-direction:column;align-items:center;flex:1;">'
            f'<div style="width:28px;height:28px;border-radius:50%;background:{bg};color:{tc};'
            f'display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;">{label}</div>'
            f'<div style="font-size:9px;color:rgba(255,255,255,0.5);margin-top:4px;">{names[i]}</div></div>'
        )
        if i < 3:
            steps_html += f'<div style="flex:1;height:2px;background:{line_c};margin-bottom:14px;align-self:center;"></div>'

    st.markdown(
        f'<div style="display:flex;align-items:center;margin-bottom:1.2rem;">{steps_html}</div>',
        unsafe_allow_html=True)

    # ── ÉTAPE 1 : Saisir l'email ───────────────────────────────────────────
    if step == 1:
        st.markdown("""
        <div style="color:rgba(255,255,255,0.7);font-size:0.82rem;margin-bottom:0.8rem;">
            Entrez votre email institutionnel. Un code à 6 chiffres vous sera envoyé.
        </div>""", unsafe_allow_html=True)

        with st.form("form_forgot_email"):
            forgot_email = st.text_input("📧 Email institutionnel", placeholder="votre.nom@uca.ac.ma")
            submit = st.form_submit_button("📨 Envoyer le code", use_container_width=True, type="primary")

        if submit:
            email = forgot_email.strip().lower()
            # Message générique volontairement — évite d'indiquer si le compte existe
            if not email.endswith("@uca.ac.ma") or not is_email_allowed(email):
                st.error("❌ Cet email n'est pas reconnu dans notre système.")
            elif not account_exists(email):
                st.error("❌ Aucun compte trouvé pour cet email. Créez votre compte d'abord.")
            else:
                # Générer le code
                code = generate_reset_token(email)
                # Envoyer l'email
                from utils.email_sender import send_reset_email
                accounts = load_accounts()
                nom = accounts[email]["nom"]
                ok, msg = send_reset_email(email, nom, code)

                if ok:
                    st.session_state.reset_email = email
                    st.session_state.reset_step  = 2
                    st.success("✅ Code envoyé ! Vérifiez votre boîte email.")
                    st.rerun()
                elif msg == "EMAIL_NOT_CONFIGURED":
                    # Mode démo : afficher le code directement
                    st.session_state.reset_email = email
                    st.session_state.reset_step  = 2
                    st.warning(f"⚠️ Email non configuré — Mode DÉMO. Votre code : **`{code}`**")
                    st.info("Pour activer l'envoi réel, configurez `data/email_config.json`")
                    st.rerun()
                else:
                    st.error(f"❌ Erreur envoi email : {msg}")

    # ── ÉTAPE 2 : Vérifier le code ─────────────────────────────────────────
    elif step == 2:
        email = st.session_state.reset_email
        st.markdown(f"""
        <div style="color:rgba(255,255,255,0.7);font-size:0.82rem;margin-bottom:0.8rem;">
            Un code à 6 chiffres a été envoyé à <b style="color:white;">{email}</b><br>
            <span style="color:rgba(255,255,255,0.5);">Le code expire dans 15 minutes.</span>
        </div>""", unsafe_allow_html=True)

        with st.form("form_verify_code"):
            code_inp = st.text_input("🔢 Code à 6 chiffres", placeholder="123456", max_chars=6)
            submit   = st.form_submit_button("✅ Vérifier le code", use_container_width=True, type="primary")

        if submit:
            valid, msg = verify_reset_token(email, code_inp)
            if valid:
                st.session_state.reset_step = 3
                st.success("✅ Code correct ! Choisissez votre nouveau mot de passe.")
                st.rerun()
            else:
                st.error(f"❌ {msg}")

        col_r, col_b = st.columns(2)
        with col_r:
            if st.button("🔄 Renvoyer le code", key="resend_code"):
                email = st.session_state.reset_email
                code  = generate_reset_token(email)
                from utils.email_sender import send_reset_email
                accounts = load_accounts()
                nom = accounts[email]["nom"]
                ok, msg = send_reset_email(email, nom, code)
                if ok:
                    st.success("✅ Nouveau code envoyé !")
                elif msg == "EMAIL_NOT_CONFIGURED":
                    st.warning(f"⚠️ Mode DÉMO — Nouveau code : **`{code}`**")
                else:
                    st.error(f"Erreur : {msg}")
        with col_b:
            if st.button("← Retour", key="back_step1"):
                st.session_state.reset_step = 1
                st.rerun()

    # ── ÉTAPE 3 : Nouveau mot de passe ─────────────────────────────────────
    elif step == 3:
        email = st.session_state.reset_email
        st.markdown("""
        <div style="color:rgba(255,255,255,0.7);font-size:0.82rem;margin-bottom:0.8rem;">
            Choisissez un nouveau mot de passe sécurisé (minimum 8 caractères).
        </div>""", unsafe_allow_html=True)

        with st.form("form_new_password"):
            new_pwd  = st.text_input("🔑 Nouveau mot de passe", type="password", placeholder="Min. 8 caractères")
            conf_pwd = st.text_input("🔑 Confirmer le mot de passe", type="password", placeholder="Répétez")
            submit   = st.form_submit_button("💾 Enregistrer le nouveau mot de passe", use_container_width=True, type="primary")

        if submit:
            errors = []
            if len(new_pwd) < 8:
                errors.append("Minimum 8 caractères.")
            if new_pwd != conf_pwd:
                errors.append("Les mots de passe ne correspondent pas.")
            if errors:
                for e in errors:
                    st.error(f"❌ {e}")
            else:
                # Invalider le token + changer le mot de passe
                invalidate_token(email)
                apply_new_password(email, new_pwd)
                # Reset état
                st.session_state.reset_step  = 1
                st.session_state.reset_email = ""
                st.session_state.auth_mode   = "login"
                st.success("✅ Mot de passe modifié avec succès ! Connectez-vous.")
                st.rerun()

    if step != 3:
        st.markdown("<br>", unsafe_allow_html=True)
    if step == 1:
        if st.button("← Retour à la connexion", key="back_to_login_forgot"):
            st.session_state.auth_mode = "login"
            st.session_state.reset_step = 1
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
