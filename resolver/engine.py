"""
Main resolver engine.
Tries methods in order:
  1. Fast HTTP (no browser) 
  2. Site-specific Playwright bypass
  3. Generic Playwright bypass (fallback)
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


async def resolve_link(url: str) -> dict:
    """
    Resolve any shortener URL.
    Returns:
        {
            success: bool,
            final_url: str | None,
            file_url: str | None,
            method: str,
            error: str | None
        }
    """
    result = {"success": False, "final_url": None, "file_url": None, "method": None, "error": None}

    # ── Method 1: Pure HTTP (fastest) ────────────────────────────────────────
    http_result = resolve_via_http(url)
    if http_result["success"] and http_result["file_url"]:
        result.update(http_result)
        result["method"] = "HTTP (fast)"
        return result

    # ── Method 2: Playwright browser ─────────────────────────────────────────
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
            # Block ads/trackers to speed up loading
            await context.route(
                "**/*.{png,jpg,jpeg,gif,svg,woff,woff2,ttf}",
                lambda route: route.abort()
            )
            page = await context.new_page()

            try:
                # Site-specific handler
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
                    # Check if it's a direct file
                    _file_exts = (
                        '.xml', '.zip', '.rar', '.7z', '.mp4',
                        '.mkv', '.pdf', '.apk', '.exe', '.txt'
                    )
                    if any(final.lower().split('?')[0].endswith(e) for e in _file_exts):
                        result["file_url"] = final
                else:
                    result["error"] = "Could not extract final link"

            finally:
                await browser.close()

    except Exception as exc:
        result["error"] = f"Browser error: {exc}"
        # Fallback: return HTTP result even if no file found
        if http_result.get("final_url"):
            result["final_url"] = http_result["final_url"]
            result["success"] = True
            result["method"] = "HTTP (fallback)"

    return result
