"""
Direct Fetch Hotspots JSON File
================================
Navigates to /home -> /products/123/tavola/456 to trigger DWH API calls
and intercepts the json content file (e.g. apollo_y15.json/content).
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

BASE_DIR = Path(__file__).parent
SESSION_FILE = BASE_DIR / "session_state_eu.json"
USERNAME = "korralak.sa@sevenfive.co.th"
PASSWORD = "Service@1234"

captured_json = {}

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=100)
        ctx = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="en-GB",
            timezone_id="Europe/Rome",
            geolocation={"latitude": 45.4642, "longitude": 9.1900},
            permissions=["geolocation"]
        )
        page = await ctx.new_page()

        async def on_resp(resp):
            u = resp.url
            if ".json/content" in u or "resources/exploded-view/json" in u:
                try:
                    data = await resp.json()
                    captured_json[u] = data
                    print(f"\n[HOTSPOTS JSON CAPTURED] {u}")
                    print(json.dumps(data, indent=2)[:1000])
                except Exception as e:
                    print(f"JSON err: {e}")

        page.on("response", on_resp)

        print("[1] Logging in...")
        await page.goto("https://www.service.sirman.com/login", wait_until="domcontentloaded")
        await page.click("button:has-text('LOGIN'), .login-btn")
        await asyncio.sleep(2)

        user_el = await page.wait_for_selector("#inputEmail, input[type='email']")
        pass_el = await page.wait_for_selector("#inputPassword, input[type='password']")
        await user_el.fill(USERNAME)
        await pass_el.fill(PASSWORD)
        await page.click("button[type='submit'], input[type='submit']")
        await asyncio.sleep(3)

        auth_btn = await page.query_selector("button:has-text('Authorize')")
        if auth_btn:
            await auth_btn.click()
            await asyncio.sleep(4)

        print("[2] Navigating to APOLLO product page...")
        # Search APOLLO in catalog
        await page.goto("https://www.service.sirman.com/catalog", wait_until="networkidle")
        await asyncio.sleep(3)

        search_el = await page.query_selector("input[placeholder*='search'], input[placeholder*='Search']")
        if search_el:
            await search_el.fill("APOLLO")
            await search_el.press("Enter")
            await asyncio.sleep(4)

        apollo_row = await page.query_selector("text='APOLLO - from 2015.01', text='APOLLO'")
        if apollo_row:
            print("Clicking APOLLO product...")
            await apollo_row.click()
            await asyncio.sleep(6)

        await page.screenshot(path="apollo_exploded_view_screen.png")

        print(f"\n[3] Total JSON hotspot files captured: {len(captured_json)}")
        for u, d in captured_json.items():
            print(f"  URL: {u}")
            with open("apollo_hotspots.json", "w", encoding="utf-8") as f:
                json.dump(d, f, indent=2)
            print("Saved apollo_hotspots.json")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
