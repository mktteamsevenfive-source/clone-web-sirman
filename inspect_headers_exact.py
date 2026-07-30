"""
Inspect All Request Headers sent by Sirman Web App
"""

import asyncio
import json
from playwright.async_api import async_playwright

USERNAME = "korralak.sa@sevenfive.co.th"
PASSWORD = "Service@1234"

captured_requests = {}

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=50)
        ctx = await browser.new_context()
        page = await ctx.new_page()

        async def on_req(req):
            u = req.url
            if "api-service.sirman.com/service-dwh/" in u:
                captured_requests[u] = dict(req.headers)
                print(f"\n[DWH API REQUEST] {u}")
                for k, v in req.headers.items():
                    print(f"  {k}: {v[:60] if len(v)>60 else v}")

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

        # Click Catalog in top navigation
        print("[2] Clicking Catalog...")
        await page.goto("https://www.service.sirman.com/catalog", wait_until="networkidle")
        await asyncio.sleep(4)

        # Click on first category or model on page
        print("[3] Clicking category on screen...")
        try:
            cards = await page.query_selector_all("[class*='category'], [class*='Card'], [class*='Item']")
            for c in cards[:5]:
                txt = (await c.inner_text()).strip()
                if "Bar" in txt or "Slicer" in txt or "Meat" in txt or "Food" in txt:
                    await c.click()
                    print(f"Clicked: {txt}")
                    await asyncio.sleep(3)
                    break
        except Exception as e:
            print(f"Click notice: {e}")

        await asyncio.sleep(2)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
