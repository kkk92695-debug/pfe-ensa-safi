#!/bin/bash
echo "======================================================"
echo "  ENSA Safi — Gestion Rapports PFE"
echo "======================================================"
echo ""
echo "  Installation des dependances..."
pip install -r requirements.txt -q
echo "  OK !"
echo ""
echo "  Demarrage en cours..."

# Une seule application Streamlit — tout est integre
streamlit run app.py --server.port 8501 --server.address 0.0.0.0 &

sleep 3

echo ""
echo "======================================================"
echo ""
echo "  APPLICATION PROFS / ADMIN :"
echo "  http://localhost:8501"
echo ""
echo "  FORMULAIRE ETUDIANTS (a partager) :"
echo "  http://localhost:8501/?page=etudiant"
echo ""
echo "  Sur le reseau WiFi, remplacez localhost par"
echo "  votre adresse IP (tapez: hostname -I)"
echo "  Ex: http://192.168.1.10:8501/?page=etudiant"
echo ""
echo "======================================================"
echo ""
wait
