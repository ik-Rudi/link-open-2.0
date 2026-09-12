"""Bindass shortener bypass."""
import re
from playwright.async_api import Page

BINDASS_DOMAINS = ("bindass", "bdlink", "bnd")

def is_bindass(url: str) -> bool:
    return any(d in url.lower() for d in BINDASS_DOMAINS)

async def bypass_bindass(page: Page, url: str, timeout: int = 30_000) -> str | None:
    await page.goto(url, timeout=timeout, wait_until="domcontentloaded")
    btn_selectors = [
        "a#get-link", "a.get-link", "button#get-link",
        "a:has-text('Get Link')", "a:has-text('Continue')",
        "a:has-text('Proceed')", "button:has-text('Get Link')",
        "a.btn-success", ".download-btn", "#download-btn",
        "a[href]:has-text('Download')",
    ]
    for sel in btn_selectors:
        try:
            btn = page.locator(sel).first
            await btn.wait_for(state="visible", timeout=20_000)
            href = await btn.get_attribute("href")
            if href and href.startswith("http"):
                return href
            await btn.click()
            await page.wait_for_load_state("networkidle", timeout=10_000)
            return page.url
        except Exception:
            continue

    content = await page.content()
    matches = re.findall(r'(?:final|download|link)["\']?\s*:\s*["\']([^"\']+)["\']', content, re.I)
    for m in matches:
        if m.startswith("http"):
            return m
    return page.url if page.url != url else None
