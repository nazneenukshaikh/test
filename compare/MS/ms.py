import base64
import io
import logging
import os
import sys
import time
from datetime import datetime

import openpyxl
import requests
from PIL import ImageGrab

MAILSLOT_URL = "https://script.google.com/macros/s/AKfycbyk-rnlVZUDbMcaTDCotFsddDO1cJ8cN3IgUqcXvB5R7ZTU3GtisWirs8yrNQI_Lkwt5g/exec"
# NOTE: this must point to the xlsx config's download link (see INSTALL.md, "the config file").
CONFIG_URL   = "https://docs.google.com/spreadsheets/d/1y6RYO6jUXRIk4Zd3D57H0KajMyFC-3H2-pbpqdB06r4/export?format=xlsx"

# Interval (seconds) used ONLY when the config can't be reached at all, e.g. no network.
DEFAULT_SYNC_SECONDS = 300

# Fallbacks used if the config is unreadable, or if a single cell is blank/invalid.
DEFAULTS = {
    "enabled": True,
    "interval_seconds": 60,
    "jpeg_quality": 40,     # 1-95
    "image_scale": 1.0,     # 1.0 = full size, 0.5 = half
}

# --- ms.log lives next to this program (works for both the .py and the .exe) ---
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

logging.basicConfig(
    filename=os.path.join(BASE_DIR, "ms.log"),
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def _as_bool(v, default):
    if isinstance(v, bool):
        return v
    if v is None:
        return default
    return str(v).strip().lower() in ("true", "1", "yes", "on")


def _as_int(v, default):
    try:
        return max(1, int(float(v)))
    except Exception:
        return default


def _as_float(v, default):
    try:
        return float(v)
    except Exception:
        return default


def get_config():
    values = dict(DEFAULTS)
    where = "config: pre-fetch"
    try:
        resp = requests.get(CONFIG_URL, timeout=15)
        resp.raise_for_status()
        where = "config: pre-parse"
        wb = openpyxl.load_workbook(io.BytesIO(resp.content), read_only=True, data_only=True)
        ws = wb.active
        raw = {}
        for row in ws.iter_rows(min_row=2, values_only=True):
            if row and row[0] is not None:
                raw[str(row[0]).strip().lower()] = row[1] if len(row) > 1 else None
        wb.close()
        values["enabled"]          = _as_bool(raw.get("enabled"), DEFAULTS["enabled"])
        values["interval_seconds"] = _as_int(raw.get("interval_seconds"), DEFAULTS["interval_seconds"])
        values["jpeg_quality"]     = _as_int(raw.get("jpeg_quality"), DEFAULTS["jpeg_quality"])
        values["image_scale"]      = _as_float(raw.get("image_scale"), DEFAULTS["image_scale"])
        return values
    except Exception as err:
        logging.warning("fallback | %s | %s", where, err)
        values["interval_seconds"] = DEFAULT_SYNC_SECONDS
        return values


def capture_and_upload(cfg):
    where = "task: start"
    try:
        where = "task: pre-acquire"
        img = ImageGrab.grab().convert("RGB")
        scale = cfg["image_scale"]
        if scale > 0 and scale != 1.0:
            w, h = img.size
            img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))))
        where = "task: pre-buffer"
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=cfg["jpeg_quality"])
        where = "task: pre-payload"      # before payload dict assignment
        payload = {
            "name": datetime.now().strftime("%Y-%m-%d_%H-%M-%S.jpg"),
            "data": base64.b64encode(buf.getvalue()).decode("ascii"),
            "mime": "image/jpeg",
        }
        where = "task: pre-request"
        resp = requests.post(MAILSLOT_URL, json=payload, timeout=60)
        where = "task: post-request"
        body = resp.text.strip()[:150]
        if resp.status_code == 200 and body == "OK":
            logging.info("ok | status=%s", resp.status_code)
        else:
            logging.error("bad-response | %s | status=%s | body=%r", where, resp.status_code, body)
    except Exception as err:
        logging.error("failure | %s | %s", where, err)


def main():
    logging.info("boot")
    while True:
        cfg = get_config()
        if cfg["enabled"]:
            capture_and_upload(cfg)
        time.sleep(cfg["interval_seconds"])


if __name__ == "__main__":
    main()
