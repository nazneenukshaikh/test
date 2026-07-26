# MS — Install Guide

The tool ships as **compiled Python bytecode (`ms.pyc`)** and runs with python.org's
**`pythonw.exe`** — which is digitally signed (so Smart App Control trusts it) and runs
**with no window**. Two phases:

- **Phase 1 — Compile `ms.py` → `ms.pyc` once, on your machine.**
- **Phase 2 — Install on each client:** install Python + the libraries, drop `ms.pyc`, and
  create the scheduled task by hand.

Replace `XXXXXX` with the Windows username throughout.

> **Use the same Python version everywhere.** Bytecode is tied to the Python version, so
> compile with the same version you install on the clients. This guide uses **Python 3.13**.

---

## Before you build — the config file

The two links live inside the code, so set them **before** compiling. `MAILSLOT_URL` is
already your mail slot. The machine reads the config **straight from a link every cycle** —
nothing is downloaded or kept locally. Keep it as a **Google Sheet**:

1. Put the settings into a Google Sheet named `msconfig` (easiest: upload `msconfig.xlsx`,
   then right-click ▸ **Open with ▸ Google Sheets**; delete the uploaded `.xlsx` after).
2. Share it **Anyone with the link ▸ Viewer**.
3. From `https://docs.google.com/spreadsheets/d/SHEET_ID/edit`, take `SHEET_ID` and build:
   ```
   https://docs.google.com/spreadsheets/d/SHEET_ID/export?format=xlsx
   ```
4. Set `CONFIG_URL` in `ms.py` to that link.

**Editing later:** change the `value` column in the browser — auto-saves, nothing lands
locally, picked up within a few minutes. Settings: `enabled`, `interval_seconds`,
`jpeg_quality`, `image_scale`. (The 300s network-outage fallback stays in the code.)

---

## Phase 1 — Compile `ms.pyc` (your machine, once)

1. Install **Python 3.13** from python.org — tick **Add python.exe to PATH**. Confirm in a
   new Command Prompt: `python --version`.
2. In `ms.py`, confirm `MAILSLOT_URL` and set `CONFIG_URL` (see above).
3. In the folder with `ms.py`, double-click **`compile.bat`** (or run
   `python -c "import py_compile; py_compile.compile('ms.py','ms.pyc')"`). It produces
   **`ms.pyc`**.
4. Ship **`ms.pyc`** to the clients. **Keep `ms.py` private** — `ms.pyc` is the compiled
   form that hides the source.

> Bytecode can still be decompiled by a determined person — it's a strong speed bump, not a
> vault. It clears the casual-snooping bar without needing a code-signing certificate.

---

## Phase 2 — Install on a client machine (manual)

1. Install **Python 3.13** from python.org (same version as Phase 1) — tick **Add to PATH**.
   This signed Python is what lets the tool run under Smart App Control.
2. Install the libraries:
   ```
   python -m pip install requests pillow openpyxl
   ```
3. Put `ms.pyc` in a folder, e.g. `C:\Users\XXXXXX\MS\ms.pyc`.
4. Find `pythonw.exe`: in Command Prompt run `where pythonw` and copy the path (e.g.
   `C:\Users\XXXXXX\AppData\Local\Programs\Python\Python313\pythonw.exe`).
5. **Test first:** in that folder run `pythonw ms.pyc`. No window appears (correct). Wait a
   minute, then check `ms.log` next to `ms.pyc` for `ok | status=200`, and an image in Drive.
   Stop it via Task Manager ▸ **Details** ▸ `pythonw.exe` ▸ End task.
6. **Create the scheduled task:** Win+R ▸ `taskschd.msc` ▸ **Create Task…** (not "Create Basic Task").
   - **General:** name `MS`; **Run only when user is logged on**; leave "highest privileges" unchecked.
   - **Triggers ▸ New:** At log on ▸ **Specific user** ▸ Delay task 30 seconds ▸ tick
     **Repeat task every 5 minutes** for a duration of **Indefinitely** (this is the auto-restart).
   - **Actions ▸ New:** Start a program ▸ Program/script = the `pythonw.exe` path from step 4
     ▸ Add arguments = `ms.pyc` ▸ Start in = the folder, e.g. `C:\Users\XXXXXX\MS` (no quotes).
   - **Conditions:** laptop? **Uncheck** "Start the task only if the computer is on AC power".
   - **Settings:** **uncheck** "Stop the task if it runs longer than…"; "If already running"
     → **Do not start a new instance**; optionally tick "restart every 1 minute" up to 3 times.
   - OK; enter the Windows password if prompted.
7. **Test:** right-click **MS** ▸ **Run**. Confirm a fresh `boot` line in `ms.log`,
   `pythonw.exe` in Task Manager ▸ Details, and a new image in Drive.
8. **Reboot** and confirm it starts on its own.

---

## Reading `ms.log`

Lines are `timestamp | TYPE | message`. Vague on the client by design; your private key:

| Log line | Meaning |
|---|---|
| `INFO \| boot` | Program started |
| `INFO \| ok \| status=200` | One successful cycle |
| `WARNING \| fallback \| config: pre-fetch \| …` | Couldn't load the config link → using the 300s default |
| `WARNING \| fallback \| config: pre-parse \| …` | Config loaded but couldn't be read as a spreadsheet |
| `ERROR \| failure \| task: pre-acquire \| …` | Failed grabbing the frame |
| `ERROR \| failure \| task: pre-request \| …` | Couldn't reach the server (usually network) |
| `ERROR \| bad-response \| task: post-request \| status=… body=…` | Server rejected it — `body` is the reason |

---

## Notes

- **Why this runs under Smart App Control:** `pythonw.exe` is python.org's *signed* binary,
  which SAC trusts, so it runs your bytecode without the block that hit the unsigned exe.
- **Verify on your first client:** the `pillow` library includes a compiled component. It
  almost always loads fine under a trusted Python, but confirm the step-5 test actually
  captures. If SAC blocks that piece, tell me — the screenshot can be switched to a
  pure-Windows method with nothing unsigned to load.
- **Same Python 3.13** on the build machine and every client, or `ms.pyc` won't load.
- The task runs **only while the user is logged in**; the 5-minute repeat brings it back
  if it crashes or is killed.
