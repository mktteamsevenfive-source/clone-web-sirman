"""
Test Dismiss Geolocation Overlay & Reveal Catalog UI
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

BASE_DIR = Path(__file__).parent
SESSION_FILE = BASE_DIR / "session_state.json"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=100)
        ctx = await browser.new_context(
            storage_state=str(SESSION_FILE),
            viewport={"width": 1440, "height": 900}
        )
        page = await ctx.new_page()

        print("[1] Opening Sirman catalog page...")
        await page.goto("https://www.service.sirman.com/catalog", wait_until="networkidle")
        await asyncio.sleep(2)

        print("[2] Removing geolocation banner overlay via JS...")
        await page.evaluate("""() => {
            const elements = document.querySelectorAll('div, section, footer');
            for (const el of elements) {
                if (el.textContent && el.textContent.includes('browsing from the United States')) {
                    el.remove();
                    console.log('Removed banner');
                }
            }
        }""")

        await asyncio.sleep(3)
        await page.screenshot(path="catalog_banner_removed.png")
        print(f"[3] Current page URL: {page.url}")

        # List all clickable text and cards
        text_list = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll('a, button, h1, h2, h3, h4, span, div'))
                .map(el => el.textContent.trim())
                .filter(t => t.length > 2 && t.length < 80);
        }""")
        print(f"Captured {len(text_list)} text nodes:")
        for t in text_list[:30]:
            print(f"  - '{t}'")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
