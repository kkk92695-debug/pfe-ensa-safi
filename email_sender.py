"""
email_sender.py — Envoi d'emails via SMTP Gmail
Configuration dans data/email_config.json
"""
import smtplib
import json
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "email_config.json")

DEFAULT_CONFIG = {
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "votre.email@gmail.com",
    "sender_password": "votre_app_password",
    "sender_name": "ENSA Safi — Gestion PFE"
}

def load_email_config():
    if not os.path.exists(CONFIG_FILE):
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def send_reset_email(to_email: str, nom: str, code: str) -> tuple[bool, str]:
    """
    Envoie l'email avec le code de réinitialisation.
    Retourne (succès: bool, message: str)
    """
    try:
        cfg = load_email_config()

        # Vérifier config
        if cfg["sender_email"] == "votre.email@gmail.com":
            return False, "EMAIL_NOT_CONFIGURED"

        msg = MIMEMultipart("alternative")
        msg["Subject"] = "🔐 Code de réinitialisation — ENSA Safi PFE"
        msg["From"]    = f"{cfg['sender_name']} <{cfg['sender_email']}>"
        msg["To"]      = to_email

        # Corps HTML
        html = f"""
        <html><body style="font-family:Arial,sans-serif;background:#f0f4f8;padding:20px;">
        <div style="max-width:480px;margin:0 auto;background:white;border-radius:16px;
                    overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.1);">
            <div style="background:linear-gradient(135deg,#0f2557,#1a56a0);padding:24px;text-align:center;">
                <div style="color:white;font-size:18px;font-weight:700;">
                    École Nationale des Sciences Appliquées de Safi
                </div>
                <div style="color:rgba(255,255,255,0.75);font-size:13px;margin-top:4px;">
                    Système de Gestion PFE
                </div>
            </div>
            <div style="padding:28px 24px;">
                <p style="color:#374151;font-size:14px;">Bonjour <b>{nom}</b>,</p>
                <p style="color:#374151;font-size:13px;margin-top:8px;">
                    Vous avez demandé la réinitialisation de votre mot de passe.
                    Voici votre code de confirmation :
                </p>
                <div style="background:#eff6ff;border:2px solid #2563eb;border-radius:12px;
                            padding:20px;text-align:center;margin:20px 0;">
                    <div style="font-size:36px;font-weight:900;letter-spacing:8px;
                                color:#1d4ed8;font-family:monospace;">{code}</div>
                    <div style="color:#6b7280;font-size:12px;margin-top:8px;">
                        ⏱️ Ce code expire dans <b>15 minutes</b>
                    </div>
                </div>
                <div style="background:#fef2f2;border-radius:8px;padding:12px;
                            font-size:12px;color:#7f1d1d;">
                    ⚠️ Si vous n'avez pas demandé ce code, ignorez cet email.
                    Votre mot de passe ne sera pas modifié.
                </div>
            </div>
            <div style="background:#f8fafc;padding:14px;text-align:center;
                        font-size:11px;color:#9ca3af;">
                ENSA Safi — Université Cadi Ayyad | Ce message est automatique, ne pas répondre.
            </div>
        </div>
        </body></html>
        """

        msg.attach(MIMEText(html, "html", "utf-8"))

        with smtplib.SMTP(cfg["smtp_host"], cfg["smtp_port"]) as server:
            server.starttls()
            server.login(cfg["sender_email"], cfg["sender_password"])
            server.sendmail(cfg["sender_email"], to_email, msg.as_string())

        return True, "OK"

    except smtplib.SMTPAuthenticationError:
        return False, "AUTH_ERROR"
    except smtplib.SMTPException as e:
        return False, f"SMTP_ERROR: {e}"
    except Exception as e:
        return False, f"ERROR: {e}"
