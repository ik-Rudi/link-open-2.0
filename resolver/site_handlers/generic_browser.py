"""
Generic Playwright bypass — works for any unknown shortener.
Uses smart waiting + multiple button patterns.
"""
import asyncio, re
from playwright.async_api import Page

_BUTTON_SELECTORS = [
    "a#get-link", "#get-link", ".get-link",
    "a:has-text('Get Link')", "a:has-text('Continue')",
    "a:has-text('Proceed')", "a:has-text('Skip')",
    "a:has-text('Download')", "button:has-text('Get Link')",
    "button:has-text('Continue')", "button:has-text('Download')",
    "a.btn-success", "a.btn-primary", ".download-btn",
    "#btn-main", ".btn-main", "a.skip-btn",
    "a[href*='drive.google']", "a[href*='mediafire']",
    "a[href*='mega.nz']", "a[href*='dropbox']",
]

_COUNTDOWN_SELECTORS = [
    ".countdown", "#countdown", ".timer", "#timer",
    "[class*='count']", "[id*='count']", "[class*='timer']",
]

async def bypass_generic(page: Page, url: str, timeout: int = 30_000) -> str | None:
    try:
        await page.goto(url, timeout=timeout, wait_until="domcontentloaded")
    except Exception:
        try:
            await page.goto(url, timeout=timeout, wait_until="load")
        except Exception:
            return None

    # Detect and wait through any countdown
    for sel in _COUNTDOWN_SELECTORS:
        try:
            el = page.locator(sel).first
            await el.wait_for(state="visible", timeout=3_000)
            for _ in range(20):
                try:
                    text = await el.inner_text()
                    digits = re.findall(r'\d+', text)
                    if not digits or int(digits[0]) == 0:
                        break
                except Exception:
                    break
                await asyncio.sleep(1)
            break
        except Exception:
            continue

    # Try every known button pattern
    for sel in _BUTTON_SELECTORS:
        try:
            btn = page.locator(sel).first
            await btn.wait_for(state="visible", timeout=5_000)
            href = await btn.get_attribute("href")
            if href and href.startswith("http"):
                return href
            await btn.click()
            await page.wait_for_load_state("networkidle", timeout=8_000)
            if page.url != url:
                return page.url
        except Exception:
            continue

    # Last resort: scan all links in page for anything useful
    try:
        links = await page.eval_on_selector_all(
            "a[href]",
            "els => els.map(e => e.href)"
        )
        for link in links:
            if link and link.startswith("http") and link != url:
                # Prefer cloud storage / known hosts
                if any(h in link for h in ("drive.google", "mega.nz", "mediafire", "dropbox", "onedrive")):
                    return link
        # Return first external link
        for link in links:
            if link and link.startswith("http") and link != url:
                return link
    except Exception:
        pass

    return page.url if page.url != url else None
