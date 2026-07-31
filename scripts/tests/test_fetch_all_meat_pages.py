"""
Test Full Pagination API for Category 7 (Meat Processors)
=========================================================
Calls: https://api-service.sirman.com/service-dwh/products?category=7&type=group&productionFilter=all&page=1&pageSize=100&catalog=catalog
and verifies how many total products/pages are available.
"""

import asyncio
import json
import sys
from pathlib import Path
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).parent
SESSION_FILE = BASE_DIR / "session_state_eu.json"

captured_headers = {}

async def main():
    print("=" * 65)
    print("  SIRMAN FULL PAGINATION TEST (MEAT PROCESSORS - CAT 7)")
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

        cat_id = 7
        url_p1 = f"https://api-service.sirman.com/service-dwh/products?category={cat_id}&type=group&productionFilter=all&page=1&pageSize=100&catalog=catalog"

        print(f"Requesting Page 1: {url_p1}")
        resp = await ctx.request.get(url_p1, headers=headers)
        print(f"Status: {resp.status}")

        if resp.status == 200:
            data = await resp.json()
            if isinstance(data, dict):
                total = data.get("total") or data.get("count")
                items = data.get("items", [])
                print("=" * 65)
                print(f"  --> TOTAL PRODUCTS IN MEAT PROCESSORS REPORTED BY API: {total}")
                print(f"  --> Page 1 items count: {len(items)}")
                print(f"  --> Data response keys: {list(data.keys())}")
                print("=" * 65)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
