import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
USERNAME = "korralak.sa@sevenfive.co.th"
PASSWORD = "Service@1234"

async def capture_flow():
    print("==================================================")
    print("  SIRMAN FRONTEND NETWORK INTERCEPTOR")
    print("==================================================")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=100)
        ctx = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await ctx.new_page()

        async def on_resp(res):
            url = res.url
            if "api-service.sirman.com" in url:
                print(f"[API RESPONSE {res.status}] {url}")
                try:
                    data = await res.json()
                    if isinstance(data, dict):
                        keys = list(data.keys())
                        total = data.get("totalItems") or data.get("total") or len(data)
                        print(f"   -> JSON keys: {keys} | totalItems: {total}")
                    elif isinstance(data, list):
                        print(f"   -> JSON List length: {len(data)}")
                except Exception:
                    pass

        page.on("response", on_resp)

        print("[1] Opening catalog page...")
        await page.goto("https://www.service.sirman.com/catalog", wait_until="domcontentloaded")
        await asyncio.sleep(2)

        login_btn = await page.query_selector("button:has-text('LOGIN'), button:has-text('Accedi')")
        if login_btn:
            await login_btn.click()
            await asyncio.sleep(2)

        user_el = await page.query_selector("input[type='email'], #inputEmail")
        pass_el = await page.query_selector("input[type='password'], #inputPassword")
        if user_el and pass_el:
            await user_el.fill(USERNAME)
            await pass_el.fill(PASSWORD)
            await page.click("button[type='submit'], input[type='submit']")
            await asyncio.sleep(3)

        auth_btn = await page.query_selector("button:has-text('Authorize')")
        if auth_btn:
            await auth_btn.click()
            await asyncio.sleep(4)

        print("[2] Navigating to https://www.service.sirman.com/catalog...")
        await page.goto("https://www.service.sirman.com/catalog", wait_until="networkidle")
        await asyncio.sleep(3)

        print("[3] Looking for Meat Processors category on screen...")
        meat_elem = await page.wait_for_selector("text='Meat processors', text='Meat Processors', text='Carne'", timeout=10000)
        if meat_elem:
            print("  [CLICKING] Meat Processors...")
            await meat_elem.click()
            await asyncio.sleep(5)

        print("[4] Done! Closing browser in 3 seconds...")
        await asyncio.sleep(3)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(capture_flow())
