@echo off
chcp 65001 >nul
title ENSA Safi — Gestion Rapports PFE

cd /d "%~dp0"

echo ======================================================
echo   ENSA Safi — Gestion Rapports PFE
echo ======================================================
echo.
echo   Installation des dependances...
pip install -r requirements.txt -q
echo   OK !
echo.
echo   Demarrage en cours...

REM Une seule application Streamlit — tout est integre
start "Application ENSA PFE :8501" cmd /k "streamlit run app.py --server.port 8501 --server.address 0.0.0.0"

timeout /t 4 /nobreak >nul

echo.
echo ======================================================
echo.
echo   APPLICATION PROFS / ADMIN :
echo   http://localhost:8501
echo.
echo   FORMULAIRE ETUDIANTS (a partager) :
echo   http://localhost:8501/?page=etudiant
echo.
echo   Sur le reseau WiFi de l'ENSA, remplacez "localhost"
echo   par votre adresse IP (tapez "ipconfig" pour la voir)
echo   Ex: http://192.168.1.10:8501/?page=etudiant
echo.
echo   Fermez la fenetre noire pour arreter l'application.
echo ======================================================
echo.
pause
