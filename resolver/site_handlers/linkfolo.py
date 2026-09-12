"""Linkfolo shortener bypass."""
import asyncio, re
from playwright.async_api import Page

LINKFOLO_DOMAINS = ("linkfolo", "lkfolo", "folo")

def is_linkfolo(url: str) -> bool:
    return any(d in url.lower() for d in LINKFOLO_DOMAINS)

async def bypass_linkfolo(page: Page, url: str, timeout: int = 30_000) -> str | None:
    await page.goto(url, timeout=timeout, wait_until="domcontentloaded")

    # Wait for countdown if present
    try:
        await page.wait_for_selector(".countdown, #countdown, .timer, #timer", timeout=5_000)
        # Wait countdown to finish (max 15s)
        for _ in range(15):
            text = await page.locator(".countdown, #countdown, .timer, #timer").first.inner_text()
            if text.strip() in ("0", "00", ""):
                break
            await asyncio.sleep(1)
    except Exception:
        pass

    btn_selectors = [
        "a#get-link", ".get-link", "a.btn-primary", "button.btn-primary",
        "a:has-text('Get Link')", "a:has-text('Continue')", "a:has-text('Skip')",
        "#btn-main", ".btn-main", "a.skip-btn",
    ]
    for sel in btn_selectors:
        try:
            btn = page.locator(sel).first
            await btn.wait_for(state="visible", timeout=8_000)
            href = await btn.get_attribute("href")
            if href and href.startswith("http"):
                return href
            await btn.click()
            await page.wait_for_load_state("networkidle", timeout=10_000)
            return page.url
        except Exception:
            continue

    content = await page.content()
    matches = re.findall(r'(?:redirect|url|link)["\']?\s*[:=]\s*["\']([^"\']{10,})["\']', content, re.I)
    for m in matches:
        if m.startswith("http"):
            return m
    return page.url if page.url != url else None
