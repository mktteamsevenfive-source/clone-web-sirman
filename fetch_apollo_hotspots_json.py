"""
Fetch Apollo_y15 Hotspots JSON Coordinates
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

BASE_DIR = Path(__file__).parent
SESSION_FILE = BASE_DIR / "session_state_eu.json"

captured_headers = {}

async def main():
    print("=" * 65)
    print("  FETCH APOLLO HOTSPOTS JSON DATA")
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

        # Fetch hotspot json for Apollo_y15.pdf -> apollo_y15.json/content
        url = "https://api-service.sirman.com/service-dwh/resources/exploded-view/json/apollo_y15.json/content"
        print(f"Fetching: {url}")
        resp = await ctx.request.get(url, headers=headers)
        print(f"Status: {resp.status}")

        if resp.status == 200:
            data = await resp.json()
            print("=" * 65)
            print("HOTSPOTS JSON DATA FOR APOLLO_Y15:")
            print(json.dumps(data, indent=2)[:1500])
            print("=" * 65)
            with open("apollo_hotspots_data.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print("Saved apollo_hotspots_data.json!")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
