"""
Test Home -> Catalog SPA Navigation with Redux Store State
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

BASE_DIR = Path(__file__).parent
SESSION_FILE = BASE_DIR / "session_state_eu.json"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=100)
        ctx = await browser.new_context(
            storage_state=str(SESSION_FILE),
            viewport={"width": 1440, "height": 900},
            locale="en-GB",
            timezone_id="Europe/Rome",
            geolocation={"latitude": 45.4642, "longitude": 9.1900},
            permissions=["geolocation"]
        )
        page = await ctx.new_page()

        print("[1] Opening /home ...")
        await page.goto("https://www.service.sirman.com/home", wait_until="networkidle")
        await asyncio.sleep(3)

        print(f"Current URL: {page.url}")

        print("[2] Clicking Catalog link...")
        try:
            cat_link = await page.wait_for_selector("text=Catalog", timeout=5000)
            if cat_link:
                await cat_link.click()
                await asyncio.sleep(4)
        except Exception as e:
            print(f"Catalog text click: {e}")

        await page.screenshot(path="real_catalog_loaded.png")
        print(f"[3] Post-nav URL: {page.url}")

        # Inspect cards / text on loaded page
        cards = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll('a, button, div[class*="card"], div[class*="Card"], h1, h2, h3'))
                .map(el => el.textContent.trim())
                .filter(t => t.length > 2 && t.length < 60);
        }""")
        print(f"Found {len(cards)} elements on loaded catalog page:")
        for c in cards[:25]:
            print(f"  --> '{c}'")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
