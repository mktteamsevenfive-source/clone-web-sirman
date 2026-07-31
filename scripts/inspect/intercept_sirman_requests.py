import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
USERNAME = "korralak.sa@sevenfive.co.th"
PASSWORD = "Service@1234"

captured_urls = []

async def intercept():
    print("==================================================")
    print("  INTERCEPTING SIRMAN CATALOG NETWORK REQUESTS")
    print("==================================================")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=100)
        ctx = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await ctx.new_page()

        async def on_req(req):
            if "api-service.sirman.com" in req.url or "service" in req.url:
                if not any(x in req.url for x in ["hubspot", "analytics", "css", "js", "png", "jpg"]):
                    info = f"[{req.method}] {req.url}"
                    captured_urls.append(info)
                    print(f"  [NET REQ] {info}")

        page.on("request", on_req)

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
            await asyncio.sleep(3)

        print("[2] Clicking Meat Processors category card...")
        # Find category card for Meat Processors
        meat_card = await page.query_selector("text=Meat processors, text=Meat Processors, text=Carne")
        if meat_card:
            print("  Found Meat Processors card, clicking...")
            await meat_card.click()
            await asyncio.sleep(5)
        else:
            print("  Meat Processors card not found by text, clicking first card...")
            cards = await page.query_selector_all(".category-card, .card, a[href*='catalog']")
            if cards:
                await cards[0].click()
                await asyncio.sleep(5)

        print(f"[3] Current Page URL after category click: {page.url}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(intercept())
