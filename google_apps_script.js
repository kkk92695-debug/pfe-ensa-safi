// ════════════════════════════════════════════════════════════════
//  SCRIPT GOOGLE APPS SCRIPT — Formulaire PFE ENSA Safi
//  À coller dans : script.google.com → Nouveau projet
// ════════════════════════════════════════════════════════════════
//
//  INSTRUCTIONS D'INSTALLATION :
//  1. Allez sur https://script.google.com
//  2. Créez un nouveau projet (bouton "+ Nouveau projet")
//  3. Supprimez tout le code par défaut
//  4. Collez ce code entier
//  5. Remplacez VOTRE_SHEET_ID ci-dessous par l'ID de votre Google Sheet
//     (l'ID est dans l'URL du Sheet : docs.google.com/spreadsheets/d/[ID ICI]/edit)
//  6. Cliquez sur "Déployer" → "Nouveau déploiement"
//  7. Type : "Application Web"
//  8. Exécuter en tant que : "Moi"
//  9. Qui a accès : "Tout le monde"
//  10. Cliquez "Déployer" et copiez l'URL obtenue
//  11. Collez cette URL dans formulaire_public_online.html (variable APPS_SCRIPT_URL)
//  12. Collez aussi cette URL dans dashboard.py (variable GOOGLE_SHEET_URL)
// ════════════════════════════════════════════════════════════════

const SHEET_ID = "VOTRE_SHEET_ID"; // ← Remplacez ceci !
const SHEET_NAME = "Etudiants";    // Nom de l'onglet (sera créé automatiquement)

const COLUMNS = [
  "num_ordre", "nom", "prenom", "email", "filiere", "annee",
  "intitule_rapport", "encadrant", "co_encadrant", "lieu_stage",
  "date_depot_secretariat", "correction", "nb_copies_bibliotheque",
  "pdf_filename", "date_soumission"
];

// ── Permet les requêtes cross-origin (CORS) ──────────────────────
function doOptions(e) {
  return ContentService.createTextOutput("")
    .setMimeType(ContentService.MimeType.TEXT)
    .setHeaders({
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type"
    });
}

// ── Point d'entrée principal (POST) ─────────────────────────────
function doPost(e) {
  const headers = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type"
  };

  try {
    const data = JSON.parse(e.postData.contents);
    const sheet = getOrCreateSheet();

    // Vérifier doublon (même nom + prénom + année)
    const values = sheet.getDataRange().getValues();
    for (let i = 1; i < values.length; i++) {
      const row = values[i];
      // Indices: 1=nom, 2=prenom, 5=annee
      if (
        String(row[1]).trim().toUpperCase() === String(data.nom || "").trim().toUpperCase() &&
        String(row[2]).trim().toLowerCase() === String(data.prenom || "").trim().toLowerCase() &&
        String(row[5]).trim() === String(data.annee || "").trim()
      ) {
        return respond({ ok: false, errors: ["Un dépôt existe déjà pour cet étudiant pour cette année universitaire."] }, headers);
      }
    }

    // Générer le numéro d'ordre
    const numOrdre = getNextNumOrdre(sheet, data.annee || "");
    const now = Utilities.formatDate(new Date(), "Africa/Casablanca", "yyyy-MM-dd HH:mm");

    // Construire la ligne
    const newRow = [
      numOrdre,
      (data.nom || "").trim().toUpperCase(),
      (data.prenom || "").trim(),
      (data.email || "").trim().toLowerCase(),
      (data.filiere || "").trim(),
      (data.annee || "").trim(),
      (data.intitule_rapport || "").trim(),
      (data.encadrant || "").trim(),
      (data.co_encadrant || "").trim(),
      (data.lieu_stage || "").trim(),
      now,   // date_depot_secretariat
      "Non", // correction
      0,     // nb_copies_bibliotheque
      "",    // pdf_filename
      now    // date_soumission
    ];

    sheet.appendRow(newRow);

    return respond({ ok: true, num_ordre: numOrdre, date_soumission: now, message: "Formulaire soumis avec succès !" }, headers);

  } catch (err) {
    return respond({ ok: false, errors: ["Erreur serveur : " + err.toString()] }, headers);
  }
}

// ── GET : retourner toutes les données (pour Streamlit) ──────────
function doGet(e) {
  const headers = { "Access-Control-Allow-Origin": "*" };
  try {
    const sheet = getOrCreateSheet();
    const values = sheet.getDataRange().getValues();
    if (values.length <= 1) {
      return respond({ ok: true, data: [] }, headers);
    }
    const rows = values.slice(1).map(row => {
      const obj = {};
      COLUMNS.forEach((col, i) => { obj[col] = row[i] !== undefined ? String(row[i]) : ""; });
      return obj;
    });
    return respond({ ok: true, data: rows }, headers);
  } catch (err) {
    return respond({ ok: false, errors: [err.toString()] }, headers);
  }
}

// ── Helpers ──────────────────────────────────────────────────────
function getOrCreateSheet() {
  const ss = SpreadsheetApp.openById(SHEET_ID);
  let sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) {
    sheet = ss.insertSheet(SHEET_NAME);
    sheet.appendRow(COLUMNS); // En-têtes
    // Formater la ligne d'en-têtes
    const headerRange = sheet.getRange(1, 1, 1, COLUMNS.length);
    headerRange.setFontWeight("bold");
    headerRange.setBackground("#1a56a0");
    headerRange.setFontColor("#ffffff");
  }
  return sheet;
}

function getNextNumOrdre(sheet, annee) {
  let yearSuffix;
  if (annee && annee.includes("-")) {
    yearSuffix = annee.split("-").pop().slice(-2);
  } else {
    yearSuffix = String(new Date().getFullYear()).slice(-2);
  }
  const prefix = yearSuffix + "-";
  const values = sheet.getDataRange().getValues();
  let maxSeq = 0;
  for (let i = 1; i < values.length; i++) {
    const numOrdre = String(values[i][0]);
    if (numOrdre.startsWith(prefix)) {
      const seq = parseInt(numOrdre.replace(prefix, ""), 10);
      if (!isNaN(seq) && seq > maxSeq) maxSeq = seq;
    }
  }
  return prefix + String(maxSeq + 1).padStart(3, "0");
}

function respond(obj, headers) {
  const output = ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
  // Note: setHeaders n'est pas disponible sur ContentService directement,
  // mais Google Apps Script gère CORS automatiquement pour les Web Apps publiques.
  return output;
}
