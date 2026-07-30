"""
Discover Sirman Product Pagination API Endpoint
===============================================
Inspects the exact API requests sent when navigating Meat Processors
to find how to fetch ALL products beyond the first 20 items.
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

BASE_DIR = Path(__file__).parent
SESSION_FILE = BASE_DIR / "session_state_eu.json"

captured_apis = []

async def main():
    print("=" * 65)
    print("  SIRMAN PAGINATION API DISCOVERY")
    print("=" * 65)

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
            if "service-dwh" in u or "service-api" in u:
                if not any(ign in u for ign in ["hubspot", "google", "analytics", "font"]):
                    try:
                        ct = resp.headers.get("content-type", "")
                        st = resp.status
                        if "json" in ct:
                            b = await resp.json()
                            summary = f"Status: {st} | URL: {u} | Data keys/type: {list(b.keys()) if isinstance(b, dict) else f'list[{len(b)}]'}"
                            captured_apis.append(summary)
                            print(f"  [API] {summary}")
                    except:
                        pass

        page.on("response", on_resp)

        print("[1] Navigating to /home -> Catalog ...")
        await page.goto("https://www.service.sirman.com/home", wait_until="networkidle")
        await asyncio.sleep(2)

        cat_btn = await page.wait_for_selector("text=Catalog")
        if cat_btn:
            await cat_btn.click()
            await asyncio.sleep(3)

        print("[2] Clicking Meat Processors category...")
        meat_btn = await page.query_selector("text='Meat Processors', text='Meat processors'")
        if meat_btn:
            await meat_btn.click()
            await asyncio.sleep(4)

        # Scroll down to trigger infinite scroll / pagination if any
        print("[3] Scrolling down page to check pagination / infinite scroll...")
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(4)

        await page.screenshot(path="meat_processors_page_scroll.png")

        print(f"\n[4] Summary of all API requests captured:")
        for api in captured_apis:
            print(f"  --> {api}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
