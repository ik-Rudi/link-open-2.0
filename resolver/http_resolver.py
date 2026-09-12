"""
Generic HTTP resolver — no browser needed.
Handles simple redirect chains and HTML-embedded links.
"""

import re
import time
import requests
from bs4 import BeautifulSoup
from config import DEFAULT_HEADERS, MAX_RETRIES, RETRY_DELAY

_URL_PATTERNS = [
    r'var\s+url\s*=\s*["\']([^"\']+)["\']',
    r'window\.location(?:\.href)?\s*=\s*["\']([^"\']+)["\']',
    r'location\.replace\(["\']([^"\']+)["\']\)',
    r'data-url=["\']([^"\']+)["\']',
    r'link["\']?\s*:\s*["\']([^"\']+)["\']',
    r'"url"\s*:\s*"([^"]+)"',
    r'<input[^>]+name=["\']?link["\']?[^>]+value=["\']([^"\']+)["\']',
    r'<a[^>]+class=["\'][^"\']*(?:download|final|get)[^"\']*["\'][^>]+href=["\']([^"\']+)["\']',
]

_FILE_EXTENSIONS = (
    '.xml', '.zip', '.rar', '.7z', '.tar', '.gz',
    '.mp4', '.mkv', '.avi', '.mov',
    '.pdf', '.docx', '.xlsx', '.txt',
    '.apk', '.exe', '.iso',
)


def _is_file_url(url: str) -> bool:
    return any(url.lower().split('?')[0].endswith(ext) for ext in _FILE_EXTENSIONS)


def _extract_urls_from_html(html: str) -> list:
    found = []
    for pattern in _URL_PATTERNS:
        matches = re.findall(pattern, html, re.IGNORECASE)
        for m in matches:
            m = m.strip()
            if m.startswith('http') and len(m) > 10:
                found.append(m)
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup.find_all('a', href=True):
        href = tag['href'].strip()
        if href.startswith('http') and _is_file_url(href):
            found.append(href)
    return list(dict.fromkeys(found))


def resolve_via_http(url: str) -> dict:
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    session.max_redirects = 20
    result = {"success": False, "final_url": None, "file_url": None, "html": None, "error": None}

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = session.get(url, timeout=20, allow_redirects=True)
            final_url = resp.url
            html = resp.text
            result["final_url"] = final_url
            result["html"] = html

            if _is_file_url(final_url):
                result["file_url"] = final_url
                result["success"] = True
                return result

            candidates = _extract_urls_from_html(html)
            for candidate in candidates:
                if _is_file_url(candidate):
                    result["file_url"] = candidate
                    result["success"] = True
                    return result
                if candidate != url:
                    result["final_url"] = candidate
                    result["success"] = True

            if result["final_url"]:
                result["success"] = True
            return result

        except requests.TooManyRedirects:
            result["error"] = "Too many redirects"
            return result
        except Exception as exc:
            result["error"] = str(exc)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)

    return result
