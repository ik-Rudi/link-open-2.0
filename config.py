import os

# ─── Telegram ───────────────────────────────────────────────
# Railway.app-এ Environment Variable হিসেবে BOT_TOKEN set করো
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# ─── Browser ────────────────────────────────────────────────
HEADLESS = True
BROWSER_TIMEOUT = 30_000

# ─── Retry Settings ─────────────────────────────────────────
MAX_RETRIES = 3
RETRY_DELAY = 2

# ─── Download ───────────────────────────────────────────────
# Cloud-এ /tmp ব্যবহার হবে, local-এ D:\link_bot\downloads
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "/tmp/downloads")
MAX_FILE_SIZE_MB = 50

# ─── Headers ────────────────────────────────────────────────
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}
