"""
Fetch All Meat Processors Products (Category ID: 7)
===================================================
1. Configures UTF-8 encoding for Windows console
2. Queries Category ID 7 (Meat Processors / Carne)
3. Tests pagination parameters to fetch all 2,000+ items
"""

import asyncio
import json
import sys
from pathlib import Path
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).parent
SESSION_FILE = BASE_DIR / "session_state_eu.json"

captured_headers = {}

async def main():
    print("=" * 65)
    print("  SIRMAN MEAT PROCESSORS (CAT 7) FULL SCRAPER TEST")
    print("=" * 65)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        ctx = await browser.new_context(
            storage_state=str(SESSION_FILE),
            viewport={"width": 1440, "height": 900},
            locale="en-GB",
            timezone_id="Europe/Rome",
            geolocation={"latitude": 45.4642, "longitude": 9.1900},
            permissions=["geolocation"]
        )
        page = await ctx.new_page()

        async def on_req(req):
            if "service-dwh" in req.url:
                hdrs = dict(req.headers)
                if "authorization" in hdrs:
                    captured_headers.update(hdrs)

        page.on("request", on_req)

        await page.goto("https://www.service.sirman.com/home", wait_until="networkidle")
        await asyncio.sleep(2)

        cat_btn = await page.wait_for_selector("text=Catalog")
        if cat_btn:
            await cat_btn.click()
            await asyncio.sleep(3)

        headers = dict(captured_headers)
        headers["x-language"] = "en"

        # Category 7 = Meat Processors (Carne)
        cat_id = 7
        
        urls_to_test = [
            f"https://api-service.sirman.com/service-dwh/categories/{cat_id}/products",
            f"https://api-service.sirman.com/service-dwh/categories/{cat_id}/products?limit=1000",
            f"https://api-service.sirman.com/service-dwh/categories/{cat_id}/products?page_size=2000",
            f"https://api-service.sirman.com/service-dwh/categories/{cat_id}/customer-categories"
        ]

        for u in urls_to_test:
            resp = await ctx.request.get(u, headers=headers)
            print(f"[TEST] {u} -> Status: {resp.status}")
            if resp.status == 200:
                data = await resp.json()
                if isinstance(data, list):
                    print(f"  --> Success! Returned list of {len(data)} items!")
                    if len(data) > 0:
                        sample = data[0]
                        print(f"      Sample item 1: ID={sample.get('id')} | Name={sample.get('name')}")
                elif isinstance(data, dict):
                    print(f"  --> Success dict! Keys: {list(data.keys())}")
                    prods = data.get("products") or data.get("items") or []
                    print(f"      Products count: {len(prods)}, Total reported: {data.get('total')}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
