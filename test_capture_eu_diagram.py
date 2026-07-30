"""
Capture Real Diagram for NE1840 and AGATA 250 (EU Session)
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

BASE_DIR = Path(__file__).parent
SESSION_FILE = BASE_DIR / "session_state_eu.json"
IMG_DIR = BASE_DIR / "diagram_images"

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

        captured_media = {}

        async def on_resp(resp):
            u = resp.url
            ct = resp.headers.get("content-type", "")
            if resp.status == 200 and any(k in ct.lower() for k in ["image", "pdf", "octet"]):
                if not any(ign in u for ign in ["google", "hubspot", "lucide", "font", "logo"]):
                    try:
                        b = await resp.body()
                        if len(b) > 4000:
                            captured_media[u] = (ct, b)
                            print(f"  [MEDIA] {resp.status} | {ct[:25]} | {len(b)/1024:.1f} KB | {u[:70]}")
                    except:
                        pass

        page.on("response", on_resp)

        print("[1] Opening Catalog page...")
        await page.goto("https://www.service.sirman.com/catalog", wait_until="networkidle")
        await asyncio.sleep(3)

        print(f"[2] Catalog URL: {page.url}")

        # Click on Slicers or Microwave ovens
        cat_card = await page.query_selector("text='Slicers', text='Microwave ovens', text='Microwave'")
        if cat_card:
            print("Clicking Category card...")
            await cat_card.click()
            await asyncio.sleep(4)

        # Click on AGATA 250 or NE1840 product row
        prod_row = await page.query_selector("text='AGATA 250', text='NE1840', text='AGATA'")
        if prod_row:
            print("Clicking Product row...")
            await prod_row.click()
            await asyncio.sleep(5)

        await page.screenshot(path="product_diagram_screen.png")

        print(f"[3] Total media captured: {len(captured_media)}")
        for u, (ct, b) in captured_media.items():
            print(f"  Media: {ct} ({len(b)/1024:.1f} KB) -> {u}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
