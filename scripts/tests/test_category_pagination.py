"""
Test Category Pagination API Endpoint
======================================
Tests fetching all products for categories via Sirman DWH API
with limit/offset/page parameters.
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

USERNAME = "korralak.sa@sevenfive.co.th"
PASSWORD = "Service@1234"

captured_headers = {}

async def main():
    print("=" * 65)
    print("  SIRMAN CATEGORY PAGINATION TEST")
    print("=" * 65)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        ctx = await browser.new_context(
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

        # Login
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

        # Save session
        await ctx.storage_state(path="session_state_eu.json")

        headers = dict(captured_headers)
        headers["x-language"] = "en"

        # Fetch categories list to get exact category IDs
        cat_resp = await ctx.request.get("https://api-service.sirman.com/service-dwh/categories", headers=headers)
        cats = await cat_resp.json()
        print(f"Categories count: {len(cats)}")

        # Find Meat Processors category ID
        meat_id = None
        for c in cats:
            name = c.get("name", "")
            print(f"  Cat: ID={c.get('id')} | Name={name} | Code={c.get('code')}")
            if "meat" in name.lower():
                meat_id = c.get("id")

        if meat_id:
            print(f"\n[Meat Processors ID: {meat_id}] Testing product pagination endpoints...")
            
            endpoints_to_test = [
                f"https://api-service.sirman.com/service-dwh/categories/{meat_id}/products",
                f"https://api-service.sirman.com/service-dwh/categories/{meat_id}/products?limit=100",
                f"https://api-service.sirman.com/service-dwh/categories/{meat_id}/products?page=1&limit=50",
                f"https://api-service.sirman.com/service-dwh/products?categoryId={meat_id}&limit=100"
            ]

            for ep in endpoints_to_test:
                r = await ctx.request.get(ep, headers=headers)
                print(f"  {ep} -> Status {r.status}")
                if r.status == 200:
                    data = await r.json()
                    if isinstance(data, list):
                        print(f"    --> Returned {len(data)} products!")
                    elif isinstance(data, dict):
                        print(f"    --> Dict keys: {list(data.keys())}, total={data.get('total') or data.get('count')}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
