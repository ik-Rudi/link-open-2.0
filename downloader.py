"""File downloader — downloads final URL and saves to D:\link_bot\downloads"""

import os
import re
import time
import requests
from config import DEFAULT_HEADERS, DOWNLOAD_DIR, MAX_FILE_SIZE_MB

os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def _sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "_", name)


def download_file(url: str) -> dict:
    """
    Download file from URL.
    Returns: {success, filepath, filename, size_mb, error}
    """
    result = {"success": False, "filepath": None, "filename": None, "size_mb": 0, "error": None}
    try:
        session = requests.Session()
        session.headers.update(DEFAULT_HEADERS)

        # HEAD request to check file size
        try:
            head = session.head(url, timeout=10, allow_redirects=True)
            content_length = int(head.headers.get("Content-Length", 0))
            size_mb = content_length / (1024 * 1024)
            if size_mb > MAX_FILE_SIZE_MB:
                result["error"] = f"File too large ({size_mb:.1f} MB) — Telegram limit is {MAX_FILE_SIZE_MB} MB"
                result["size_mb"] = size_mb
                return result
        except Exception:
            pass

        # Try to get filename from URL or Content-Disposition
        resp = session.get(url, timeout=60, stream=True)
        resp.raise_for_status()

        filename = None
        cd = resp.headers.get("Content-Disposition", "")
        if cd:
            m = re.search(r'filename=["\']?([^"\';\n]+)', cd)
            if m:
                filename = m.group(1).strip()

        if not filename:
            filename = url.split('?')[0].split('/')[-1]
            if not filename:
                filename = f"file_{int(time.time())}"

        filename = _sanitize_filename(filename)
        filepath = os.path.join(DOWNLOAD_DIR, filename)

        # Avoid overwriting
        base, ext = os.path.splitext(filepath)
        counter = 1
        while os.path.exists(filepath):
            filepath = f"{base}_{counter}{ext}"
            counter += 1

        total = 0
        with open(filepath, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    total += len(chunk)

        size_mb = total / (1024 * 1024)
        result.update({
            "success": True,
            "filepath": filepath,
            "filename": filename,
            "size_mb": round(size_mb, 2),
        })

    except Exception as exc:
        result["error"] = str(exc)

    return result
