"""
Test Exact Auth Header Formats for Sirman API
"""

import asyncio
from playwright.async_api import async_playwright

USERNAME = "korralak.sa@sevenfive.co.th"
PASSWORD = "Service@1234"

captured = {}

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=100)
        ctx = await browser.new_context()
        page = await ctx.new_page()

        async def on_req(req):
            if "service-dwh" in req.url:
                captured["headers"] = dict(req.headers)
                captured["url"] = req.url

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

        await page.goto("https://www.service.sirman.com/catalog", wait_until="networkidle")
        await asyncio.sleep(4)

        raw_headers = captured.get("headers", {})
        jwt_val = raw_headers.get("authorization", "")
        print(f"Captured Raw Authorization Header: '{jwt_val[:50]}...'")

        # Test formats
        test_url = "https://api-service.sirman.com/service-dwh/files/Agat1.pdf"

        # Format 1: Exact captured headers
        resp1 = await ctx.request.get(test_url, headers=raw_headers)
        print(f"Format 1 (Exact captured headers) -> Status: {resp1.status}, Size: {len(await resp1.body())} bytes")

        # Format 2: No 'Bearer ' prefix
        h2 = dict(raw_headers)
        if h2.get("authorization", "").startswith("Bearer "):
            h2["authorization"] = h2["authorization"].replace("Bearer ", "")
        resp2 = await ctx.request.get(test_url, headers=h2)
        print(f"Format 2 (Without Bearer prefix) -> Status: {resp2.status}, Size: {len(await resp2.body())} bytes")

        # Format 3: Fetching via page.evaluate (inside browser DOM)
        res3 = await page.evaluate("""async () => {
            try {
                const r = await fetch('https://api-service.sirman.com/service-dwh/files/Agat1.pdf');
                const b = await r.arrayBuffer();
                return { status: r.status, size: b.byteLength };
            } catch(e) {
                return { error: e.message };
            }
        }""")
        print(f"Format 3 (Browser DOM fetch) -> Result: {res3}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
