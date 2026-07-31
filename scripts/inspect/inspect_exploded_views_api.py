"""
Inspect Exploded Views API Details
"""

import asyncio
import json
from playwright.async_api import async_playwright

USERNAME = "korralak.sa@sevenfive.co.th"
PASSWORD = "Service@1234"

captured_jwt = {}

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=50)
        ctx = await browser.new_context()
        page = await ctx.new_page()

        async def on_req(req):
            hdrs = dict(req.headers)
            for k, v in hdrs.items():
                if k.lower() == "authorization" and v.startswith("Bearer eyJ"):
                    captured_jwt["token"] = v

        page.on("request", on_req)

        print("[1] Logging in...")
        await page.goto("https://www.service.sirman.com/login", wait_until="networkidle")

        login_btn = await page.wait_for_selector("button:has-text('LOGIN'), .login-btn")
        if login_btn:
            await login_btn.click()
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

        # Navigate to catalog to trigger API request
        await page.goto("https://www.service.sirman.com/catalog", wait_until="networkidle")
        await asyncio.sleep(3)

        token = captured_jwt.get("token", "")
        print(f"[2] JWT Token: {token[:40]}...")

        headers = {"Authorization": token} if token else {}

        # Fetch exploded views for product 234 (AGATA 250)
        url = "https://api-service.sirman.com/service-dwh/products/234/exploded-views"
        resp = await ctx.request.get(url, headers=headers)
        print(f"[3] Exploded Views API Status: {resp.status}")
        if resp.status == 200:
            views_json = await resp.json()
            print(f"Views Response: {json.dumps(views_json, indent=2)}")

            if views_json and isinstance(views_json, list):
                view_id = views_json[0].get("id")
                # Test view detail endpoints
                for endpoint in [
                    f"https://api-service.sirman.com/service-dwh/products/234/exploded-views/{view_id}",
                    f"https://api-service.sirman.com/service-dwh/exploded-views/{view_id}",
                    f"https://api-service.sirman.com/service-dwh/exploded-views/{view_id}/parts"
                ]:
                    r = await ctx.request.get(endpoint, headers=headers)
                    print(f"  Endpoint {endpoint} -> Status {r.status}")
                    if r.status == 200:
                        try:
                            d = await r.json()
                            print(f"    Data: {json.dumps(d, indent=2)[:500]}")
                        except:
                            b = await r.body()
                            print(f"    Raw bytes len: {len(b)}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
