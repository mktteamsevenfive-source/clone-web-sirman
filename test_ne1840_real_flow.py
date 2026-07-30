"""
Test Real Flow for NE1840 Exploded View & Image Discovery
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

BASE_DIR = Path(__file__).parent
SESSION_FILE = BASE_DIR / "session_state_eu.json"
IMG_DIR = BASE_DIR / "diagram_images"

captured_media = {}

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

        async def on_resp(resp):
            u = resp.url
            ct = resp.headers.get("content-type", "")
            if resp.status == 200 and any(k in ct.lower() for k in ["image", "pdf", "octet"]):
                if not any(ign in u for ign in ["google", "hubspot", "lucide", "font", "logo"]):
                    try:
                        b = await resp.body()
                        if len(b) > 4000:
                            captured_media[u] = (ct, b)
                            print(f"  [MEDIA NET] {ct[:25]} | {len(b)/1024:.1f} KB | {u}")
                    except:
                        pass

        page.on("response", on_resp)

        print("[1] Opening /home -> Catalog ...")
        await page.goto("https://www.service.sirman.com/home", wait_until="networkidle")
        await asyncio.sleep(2)

        cat_btn = await page.wait_for_selector("text=Catalog")
        if cat_btn:
            await cat_btn.click()
            await asyncio.sleep(3)

        print("[2] Searching for NE1840...")
        search_bar = await page.wait_for_selector("input[placeholder*='Search'], input[placeholder*='search']")
        if search_bar:
            await search_bar.fill("NE1840")
            await search_bar.press("Enter")
            await asyncio.sleep(4)

        await page.screenshot(path="ne1840_search_result.png")

        # Click NE1840 product row/card
        print("[3] Clicking NE1840 product item...")
        item = await page.query_selector("text='NE1840', text='NE 1840'")
        if item:
            await item.click()
            await asyncio.sleep(5)

        await page.screenshot(path="ne1840_exploded_view_real.png")
        print(f"[4] Exploded View Page URL: {page.url}")

        print(f"[5] Captured {len(captured_media)} media files during page load:")
        for u, (ct, b) in captured_media.items():
            print(f"  --> {ct} ({len(b)/1024:.1f} KB) | {u}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
