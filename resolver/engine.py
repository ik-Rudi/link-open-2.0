"""
Main resolver engine.
Tries methods in order:
  1. Fast HTTP (no browser)
  2. Site-specific Playwright bypass
  3. Generic Playwright bypass (fallback)
  4. Recursive resolution — follows intermediate pages too
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from resolver.http_resolver import resolve_via_http
from resolver.site_handlers.bindass import is_bindass, bypass_bindass
from resolver.site_handlers.linkfolo import is_linkfolo, bypass_linkfolo
from resolver.site_handlers.tn_link import is_tn, bypass_tn
from resolver.site_handlers.generic_browser import bypass_generic
from config import HEADLESS, BROWSER_TIMEOUT

_FILE_EXTS = (
    '.xml', '.zip', '.rar', '.7z', '.mp4',
    '.mkv', '.pdf', '.apk', '.exe', '.txt',
    '.iso', '.tar', '.gz', '.docx', '.xlsx'
)

# Known shortener / intermediate domains — if final URL is on these, resolve again
_SHORTENER_HINTS = (
    "arolinks", "linkfolo", "bindass", "tn.cx", "tnlinks",
    "shrinkme", "shorte.st", "adf.ly", "bc.vc", "sh.st",
    "ouo.io", "cutt.ly", "bit.ly", "tinyurl", "rb.gy",
    "hittracks", "insurancetracks", "gplinks", "earnlinks",
    "linkshrink", "link1s", "za.gl", "exe.io", "fc.lc"
)


def _is_file_url(url: str) -> bool:
    return any(url.lower().split('?')[0].endswith(e) for e in _FILE_EXTS)


def _needs_further_resolution(url: str, original_url: str) -> bool:
    """Check if the resolved URL is itself another shortener/intermediate page."""
    if url == original_url:
        return False
    if _is_file_url(url):
        return False
    return any(hint in url.lower() for hint in _SHORTENER_HINTS)


async def _resolve_single(url: str) -> dict:
    """Resolve one URL — no recursion."""
    result = {"success": False, "final_url": None, "file_url": None, "method": None, "error": None}

    # Method 1: Pure HTTP
    http_result = resolve_via_http(url)
    if http_result["success"] and http_result["file_url"]:
        result.update(http_result)
        result["method"] = "HTTP (fast)"
        return result

    # Method 2: Playwright browser
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=HEADLESS,
                args=[
                    "--no-sandbox",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-infobars",
                ],
            )
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 800},
            )
            await context.route(
                "**/*.{png,jpg,jpeg,gif,svg,woff,woff2,ttf}",
                lambda route: route.abort()
            )
            page = await context.new_page()
            try:
                if is_bindass(url):
                    final = await bypass_bindass(page, url, BROWSER_TIMEOUT)
                    result["method"] = "Bindass-specific"
                elif is_linkfolo(url):
                    final = await bypass_linkfolo(page, url, BROWSER_TIMEOUT)
                    result["method"] = "Linkfolo-specific"
                elif is_tn(url):
                    final = await bypass_tn(page, url, BROWSER_TIMEOUT)
                    result["method"] = "TN-Link-specific"
                else:
                    final = await bypass_generic(page, url, BROWSER_TIMEOUT)
                    result["method"] = "Generic-browser"

                if final:
                    result["final_url"] = final
                    result["success"] = True
                    if _is_file_url(final):
                        result["file_url"] = final
                else:
                    result["error"] = "Could not extract final link"
            finally:
                await browser.close()

    except Exception as exc:
        result["error"] = f"Browser error: {exc}"
        if http_result.get("final_url"):
            result["final_url"] = http_result["final_url"]
            result["success"] = True
            result["method"] = "HTTP (fallback)"

    return result


async def resolve_link(url: str, max_depth: int = 4) -> dict:
    """
    Resolve URL recursively — follows intermediate pages up to max_depth times.
    Returns final result with all resolved steps.
    """
    current_url = url
    all_steps = []
    combined_method = []

    for depth in range(max_depth):
        result = await _resolve_single(current_url)
        all_steps.append(result)

        if result.get("method"):
            combined_method.append(result["method"])

        # Got a direct file — done!
        if result.get("file_url"):
            result["method"] = " → ".join(combined_method)
            result["steps"] = len(all_steps)
            return result

        # Got a final URL
        next_url = result.get("final_url")

        if not next_url or not result["success"]:
            break

        # If the next URL needs further resolution, keep going
        if _needs_further_resolution(next_url, current_url):
            current_url = next_url
            continue
        else:
            # We've reached a stable final URL
            result["method"] = " → ".join(combined_method)
            result["steps"] = len(all_steps)
            return result

    # Return last result
    last = all_steps[-1] if all_steps else {"success": False, "error": "No result"}
    last["method"] = " → ".join(combined_method) if combined_method else "Unknown"
    last["steps"] = len(all_steps)
    return last
