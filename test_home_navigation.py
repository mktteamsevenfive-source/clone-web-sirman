"""
Test Sirman /home Navigation & Catalog Discovery
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

        print("[1] Opening https://www.service.sirman.com/home ...")
        await page.goto("https://www.service.sirman.com/home", wait_until="networkidle")
        await asyncio.sleep(3)

        await page.screenshot(path="home_page_preview.png")
        print(f"Current URL: {page.url}")

        # List all buttons and links on /home
        links = await page.query_selector_all("a, button, [role='button']")
        print(f"Found {len(links)} links/buttons on /home:")
        for l in links[:20]:
            try:
                txt = (await l.inner_text()).strip()
                if txt:
                    print(f"  - '{txt}'")
            except:
                pass

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
