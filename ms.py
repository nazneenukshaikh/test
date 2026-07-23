import base64
import csv
import io
import time
from datetime import datetime

import requests
from PIL import ImageGrab

# ============================ Settings ============================
# Paste your two Google links here (see the setup notes):
MAILSLOT_URL = "https://script.google.com/macros/s/AKfycbyk-rnlVZUDbMcaTDCotFsddDO1cJ8cN3IgUqcXvB5R7ZTU3GtisWirs8yrNQI_Lkwt5g/exec"   # where images are sent
CONFIG_URL   = "https://drive.google.com/uc?export=download&id=1T1UzYir3-4WfOsDbSvMNhx9CT9LOGNST"     # the config.csv download link

# Interval (in seconds) used when the config can't be reached, e.g. no network.
DEFAULT_SYNC_SECONDS = 300

# Image size controls (lower = smaller files, lower quality).
JPEG_QUALITY = 40      # 1-95
IMAGE_SCALE  = 1.0     # 1.0 = full size, 0.5 = half in each dimension
# =================================================================


def get_config():
    """Read config.csv from Drive -> (enabled, interval_seconds).
    Any problem (no network, bad data) falls back to the safe default."""
    try:
        resp = requests.get(CONFIG_URL, timeout=15)
        resp.raise_for_status()
        row = next(csv.DictReader(io.StringIO(resp.text)))
        enabled = str(row.get("enabled", "true")).strip().lower() in ("true", "1", "yes", "on")
        interval = max(1, int(float(row["interval_seconds"])))
        return enabled, interval
    except Exception:
        return True, DEFAULT_SYNC_SECONDS


def capture_and_upload():
    """Grab the screen and post it to the mail slot, which saves it to Drive."""
    img = ImageGrab.grab().convert("RGB")
    if IMAGE_SCALE != 1.0:
        w, h = img.size
        img = img.resize((max(1, int(w * IMAGE_SCALE)), max(1, int(h * IMAGE_SCALE))))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=JPEG_QUALITY)
    payload = {
        "name": datetime.now().strftime("%Y-%m-%d_%H-%M-%S.jpg"),
        "data": base64.b64encode(buf.getvalue()).decode("ascii"),
        "mime": "image/jpeg",
    }
    requests.post(MAILSLOT_URL, json=payload, timeout=60)


def main():
    while True:
        enabled, interval = get_config()
        if enabled:
            try:
                capture_and_upload()
            except Exception:
                pass   # skip this shot on any error (e.g. network blip), keep going
        time.sleep(interval)


if __name__ == "__main__":
    main()
