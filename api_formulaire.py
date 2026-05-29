"""
api_formulaire.py — Serveur API Flask pour le formulaire étudiant public
Lancer : python api_formulaire.py
Port   : 5050

Nouveautés v2 :
  - POST /api/soumettre  accepte JSON (sans PDF) ou multipart/form-data (avec PDF)
  - POST /api/recu-pdf   génère et retourne le reçu PDF officiel
  - Vérification doublon par EMAIL (un email = un seul dépôt)
"""

from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import os, sys

sys.path.insert(0, os.path.dirname(__file__))
from utils.data_manager import add_student, load_data, get_pdf_path, UPLOADS_DIR

app = Flask(__name__, static_folder=".")
CORS(app)

app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024

FILIERES = ["GINDUS", "GPMA", "GIIA", "GTR", "GATE", "GMSI"]


def _get_field(source, key, default=""):
    val = source.get(key, default)
    return str(val).strip() if val is not None else default


def _validate_common(nom, prenom, email, filiere, annee, intitule, encadrant, lieu_stage):
    errors = []
    if not nom:       errors.append("Le nom est obligatoire.")
    if not prenom:    errors.append("Le prénom est obligatoire.")
    if not email or not email.endswith("@uca.ac.ma"):
        errors.append("L'email doit se terminer par @uca.ac.ma.")
    if not filiere or filiere not in FILIERES:
        errors.append("Filière invalide.")
    if not annee:     errors.append("L'année universitaire est obligatoire.")
    if not intitule:  errors.append("L'intitulé du rapport est obligatoire.")
    if not encadrant: errors.append("L'encadrant est obligatoire.")
    if not lieu_stage: errors.append("Le lieu de stage est obligatoire.")
    return errors


@app.route("/")
def index():
    return send_from_directory(".", "formulaire_public.html")


@app.route("/api/soumettre", methods=["POST"])
def soumettre():
    try:
        is_multipart = request.content_type and 'multipart/form-data' in request.content_type
        src = request.form if is_multipart else (request.get_json(force=True) or {})

        nom          = _get_field(src, "nom").upper()
        prenom       = _get_field(src, "prenom")
        email        = _get_field(src, "email").lower()
        filiere      = _get_field(src, "filiere")
        annee        = _get_field(src, "annee")
        intitule     = _get_field(src, "intitule_rapport")
        encadrant    = _get_field(src, "encadrant")
        co_encadrant = _get_field(src, "co_encadrant")
        lieu_stage   = _get_field(src, "lieu_stage")

        errors = _validate_common(nom, prenom, email, filiere, annee, intitule, encadrant, lieu_stage)
        if errors:
            return jsonify({"ok": False, "errors": errors}), 400

        df = load_data()

        # ── Doublon par email (prioritaire) ──────────────────────────────
        doublon_email = df[df["email"].astype(str).str.strip().str.lower() == email]
        if not doublon_email.empty:
            ex = doublon_email.iloc[0]
            return jsonify({
                "ok": False,
                "type": "doublon_email",
                "errors": [
                    f"Un dépôt a déjà été enregistré avec l'adresse email {email}. "
                    f"(N° d'ordre : {ex.get('num_ordre','?')}, Année : {ex.get('annee','?')}) "
                    f"Chaque étudiant ne peut soumettre qu'une seule fois. "
                    f"Contactez le secrétariat si vous pensez qu'il s'agit d'une erreur."
                ]
            }), 409

        # ── Doublon par nom+prénom+année ─────────────────────────────────
        doublon_nom = df[
            (df["nom"].astype(str).str.strip().str.upper() == nom) &
            (df["prenom"].astype(str).str.strip().str.lower() == prenom.lower()) &
            (df["annee"].astype(str).str.strip() == annee)
        ]
        if not doublon_nom.empty:
            return jsonify({
                "ok": False,
                "type": "doublon_nom",
                "errors": [
                    f"Un dépôt existe déjà pour {nom} {prenom} pour l'année {annee}. "
                    f"Contactez le secrétariat si vous pensez qu'il s'agit d'une erreur."
                ]
            }), 409

        # ── PDF joint ────────────────────────────────────────────────────
        pdf_file_obj = None
        if is_multipart and 'pdf' in request.files:
            f = request.files['pdf']
            if f and f.filename and f.filename.lower().endswith('.pdf'):
                pdf_file_obj = f

        # ── Enregistrement ───────────────────────────────────────────────
        saved = add_student({
            "nom": nom, "prenom": prenom, "email": email,
            "filiere": filiere, "annee": annee,
            "intitule_rapport": intitule, "encadrant": encadrant,
            "co_encadrant": co_encadrant, "lieu_stage": lieu_stage,
            "correction": "Non", "nb_copies_bibliotheque": 0,
        }, pdf_file=pdf_file_obj)

        return jsonify({
            "ok": True,
            "num_ordre": saved.get("num_ordre", ""),
            "date_soumission": saved.get("date_soumission", ""),
            "pdf_uploaded": pdf_file_obj is not None,
            "message": "Votre formulaire a été soumis avec succès !"
        }), 200

    except Exception as e:
        return jsonify({"ok": False, "errors": [f"Erreur serveur : {str(e)}"]}), 500


@app.route("/api/recu-pdf", methods=["POST"])
def recu_pdf():
    try:
        data = request.get_json(force=True) or {}
        from utils.pdf_generator import generate_recu_pdf
        pdf_bytes = generate_recu_pdf(data)
        num = data.get("num_ordre", "depot")
        return Response(
            pdf_bytes,
            mimetype="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="recu_PFE_{num}.pdf"',
                "Content-Length": str(len(pdf_bytes))
            }
        )
    except Exception as e:
        return jsonify({"ok": False, "errors": [f"Erreur génération PDF : {str(e)}"]}), 500


@app.route("/api/stats", methods=["GET"])
def stats():
    try:
        df = load_data()
        return jsonify({"total": len(df), "filieres": FILIERES})
    except Exception:
        return jsonify({"total": 0, "filieres": FILIERES})


if __name__ == "__main__":
    print("=" * 60)
    print("  🎓 Formulaire PFE — Serveur API démarré")
    print("  📋 Formulaire  : http://localhost:5050")
    print("  🔗 Soumettre   : http://localhost:5050/api/soumettre")
    print("  📄 Reçu PDF    : http://localhost:5050/api/recu-pdf")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5050, debug=False)
