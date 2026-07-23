// ── The "mail slot" ────────────────────────────────────────────────
// Paste this into script.google.com, set FOLDER_ID below, then deploy:
//   Deploy ▸ New deployment ▸ Web app
//   Execute as: Me       Who has access: Anyone
// Copy the Web app URL it gives you — that's MAILSLOT_URL in ms.py.
// No password: if the URL ever leaks, just delete the deployment and
// create a new one (which changes the URL), then paste the new one in.

var FOLDER_ID = "PASTE_YOUR_DRIVE_IMAGES_FOLDER_ID_HERE";

function doPost(e) {
  try {
    var body  = JSON.parse(e.postData.contents);
    var bytes = Utilities.base64Decode(body.data);
    var blob  = Utilities.newBlob(bytes, body.mime || "image/jpeg", body.name);
    DriveApp.getFolderById(FOLDER_ID).createFile(blob);
    return ContentService.createTextOutput("OK");
  } catch (err) {
    return ContentService.createTextOutput("ERROR: " + err);
  }
}
