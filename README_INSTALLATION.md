# 📋 Guide d'installation — Formulaire PFE en ligne
## Système : Google Sheets + Google Apps Script (100% gratuit)

---

## 🎯 Objectif
Permettre aux étudiants de remplir le formulaire depuis n'importe où sur internet,
et que les données apparaissent automatiquement dans votre application Streamlit.

**Architecture :**
```
Étudiant (partout dans le monde)
        ↓  remplit le formulaire HTML hébergé en ligne
Google Apps Script  ←→  Google Sheets
        ↑  lit les données
Application Streamlit (votre PC)
```

---

## ÉTAPE 1 — Créer le Google Sheet

1. Allez sur **https://sheets.google.com**
2. Créez un nouveau classeur, nommez-le `PFE ENSA Safi`
3. Copiez l'**ID** depuis l'URL :
   ```
   https://docs.google.com/spreadsheets/d/[COPIEZ_CECI]/edit
   ```
4. Gardez cet ID de côté

---

## ÉTAPE 2 — Déployer le Google Apps Script

1. Allez sur **https://script.google.com**
2. Cliquez **"+ Nouveau projet"**
3. Nommez le projet : `PFE Formulaire API`
4. Supprimez tout le code existant
5. Collez le contenu du fichier **`google_apps_script.js`**
6. À la ligne 26, remplacez :
   ```javascript
   const SHEET_ID = "VOTRE_SHEET_ID";
   ```
   par votre vrai ID du Sheet :
   ```javascript
   const SHEET_ID = "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms";  // exemple
   ```
7. Cliquez **💾 Enregistrer** (Ctrl+S)

### Déployer comme Web App :
8. Cliquez **"Déployer"** → **"Nouveau déploiement"**
9. Type → cliquez l'engrenage ⚙️ → choisir **"Application Web"**
10. Remplissez :
    - Description : `API Formulaire PFE`
    - Exécuter en tant que : **Moi**
    - Qui a accès : **Tout le monde**
11. Cliquez **"Déployer"**
12. Autorisez les permissions demandées (cliquez "Autoriser")
13. **Copiez l'URL** qui s'affiche — elle ressemble à :
    ```
    https://script.google.com/macros/s/AKfycbxXXXXXXXXXXXXX/exec
    ```
    ⚠️ Gardez cette URL précieusement !

---

## ÉTAPE 3 — Héberger le formulaire HTML en ligne

### Option A : GitHub Pages (recommandé, gratuit)

1. Créez un compte sur **https://github.com** (si vous n'en avez pas)
2. Créez un nouveau dépôt public, nommez-le `pfe-ensa-safi`
3. Uploadez le fichier **`formulaire_public_online.html`**
4. Dans le fichier, avant d'uploader, remplacez :
   ```javascript
   const APPS_SCRIPT_URL = "VOTRE_URL_APPS_SCRIPT_ICI";
   ```
   par l'URL copiée à l'étape 2 :
   ```javascript
   const APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbx.../exec";
   ```
5. Renommez le fichier en **`index.html`** avant de l'uploader
6. Dans les paramètres du dépôt : **Settings → Pages → Source → main → / (root)**
7. Votre formulaire sera accessible à :
   ```
   https://[votre-username].github.io/pfe-ensa-safi/
   ```

### Option B : Netlify (encore plus simple)

1. Allez sur **https://netlify.com** → créez un compte gratuit
2. Glissez-déposez le fichier `formulaire_public_online.html` sur la page d'accueil
3. Netlify génère une URL immédiatement (ex: `https://amazing-pfe-123.netlify.app`)
4. ⚠️ Assurez-vous d'avoir mis à jour `APPS_SCRIPT_URL` dans le fichier avant de l'uploader

---

## ÉTAPE 4 — Configurer l'application Streamlit

Ouvrez le fichier **`modules/dashboard.py`** et modifiez les deux lignes en haut :

```python
# Ligne ~9 : URL Google Apps Script (pour lire les données)
GOOGLE_SHEET_URL = "https://script.google.com/macros/s/AKfycbx.../exec"

# Ligne ~13 : URL du formulaire en ligne (pour afficher le lien)
FORMULAIRE_ONLINE_URL = "https://votre-username.github.io/pfe-ensa-safi/"
```

---

## ÉTAPE 5 — Tester

1. Lancez votre app Streamlit normalement
2. Le tableau de bord affichera maintenant l'URL en ligne (copiable + WhatsApp)
3. Envoyez ce lien à un étudiant pour tester
4. Après soumission, rafraîchissez l'app Streamlit → la nouvelle entrée apparaît !

---

## ✅ Récapitulatif des fichiers modifiés/créés

| Fichier | Action |
|---------|--------|
| `google_apps_script.js` | À coller dans Google Apps Script |
| `formulaire_public_online.html` | À héberger sur GitHub Pages ou Netlify |
| `modules/dashboard.py` | Remplacer l'ancien (nouvelles lignes de config en haut) |

---

## ❓ Questions fréquentes

**Q : Les données anciennes (CSV local) seront-elles perdues ?**
R : Non. L'app lit d'abord Google Sheets, et si non configuré, continue à lire le CSV local.

**Q : Peut-on importer les anciennes données dans Google Sheets ?**
R : Oui. Ouvrez votre Google Sheet et importez le fichier `data/etudiants.csv` via
Fichier → Importer → Uploader.

**Q : Le formulaire fonctionne-t-il sur mobile ?**
R : Oui, le design est responsive (adapté mobile).

**Q : Les données sont-elles sécurisées ?**
R : Les données sont stockées dans votre Google Drive personnel. Seul vous avez accès
au Google Sheet. Le formulaire ne peut qu'ajouter des données, pas les modifier.
