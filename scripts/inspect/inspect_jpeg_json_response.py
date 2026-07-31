"""
Inspect Sirman Diagram Image API JSON Response
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

BASE_DIR = Path(__file__).parent
SESSION_FILE = BASE_DIR / "session_state_eu.json"

captured_headers = {}

async def main():
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

        url = "https://api-service.sirman.com/service-dwh/resources/exploded-view/jpeg/ne1880-1840-1540-2740_1.png?quality=full"
        resp = await ctx.request.get(url, headers=captured_headers)
        data = await resp.json()
        print("=" * 65)
        print("SIRMAN DIAGRAM IMAGE JSON DATA:")
        print(json.dumps(data, indent=2))
        print("=" * 65)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
