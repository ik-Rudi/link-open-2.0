"""TN Link (tn.cx / tnlinks) shortener bypass."""
import asyncio, re
from playwright.async_api import Page

TN_DOMAINS = ("tn.cx", "tnlinks", "tnlink", "tinylink", "tnshort")

def is_tn(url: str) -> bool:
    return any(d in url.lower() for d in TN_DOMAINS)

async def bypass_tn(page: Page, url: str, timeout: int = 30_000) -> str | None:
    await page.goto(url, timeout=timeout, wait_until="domcontentloaded")

    # Wait for any countdown
    try:
        await page.wait_for_selector(".countdown, #countdown, #timer", timeout=4_000)
        for _ in range(12):
            try:
                val = await page.locator(".countdown, #countdown, #timer").first.inner_text()
                if val.strip() in ("0", "00", ""):
                    break
            except Exception:
                break
            await asyncio.sleep(1)
    except Exception:
        pass

    btn_selectors = [
        "a#get-link", "#get-link", ".get-link",
        "a:has-text('Get Link')", "a:has-text('Continue')",
        "a.btn", "button.btn", "a.btn-success",
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
    matches = re.findall(r'(?:url|link|href)["\']?\s*[:=]\s*["\']([^"\']{10,})["\']', content, re.I)
    for m in matches:
        if m.startswith("http"):
            return m
    return page.url if page.url != url else None
