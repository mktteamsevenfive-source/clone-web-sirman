"""
Test Clicking GO on Geolocation Banner
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

        print("[1] Opening Sirman...")
        await page.goto("https://www.service.sirman.com/home", wait_until="domcontentloaded")
        await asyncio.sleep(2)

        # Click GO button
        print("[2] Clicking GO button on geolocation prompt...")
        go_btn = await page.query_selector("button:has-text('GO'), a:has-text('GO'), input[value='GO']")
        if go_btn:
            await go_btn.click()
            print("  --> Clicked GO button!")
            await asyncio.sleep(4)

        print(f"[3] New Page URL: {page.url}")
        await page.screenshot(path="after_go_clicked.png")

        # Check links now
        links = await page.query_selector_all("a, button, [role='button']")
        print(f"Found {len(links)} links post-GO:")
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
