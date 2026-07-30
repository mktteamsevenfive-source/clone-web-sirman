"""
Test DWH API PDF Download with Customer Code 1000052367
"""

import asyncio
from playwright.async_api import async_playwright

USERNAME = "korralak.sa@sevenfive.co.th"
PASSWORD = "Service@1234"

captured_headers = {}

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=100)
        ctx = await browser.new_context()
        page = await ctx.new_page()

        async def on_req(req):
            u = req.url
            if "service-dwh" in u:
                hdrs = dict(req.headers)
                if "authorization" in hdrs:
                    captured_headers.update(hdrs)

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

        # Go to catalog page to trigger customer selection
        await page.goto("https://www.service.sirman.com/catalog", wait_until="networkidle")
        await asyncio.sleep(4)

        print(f"[2] Captured Headers keys: {list(captured_headers.keys())}")
        print(f"  Authorization: {captured_headers.get('authorization', '')[:35]}...")
        print(f"  x-company: {captured_headers.get('x-company')}")
        print(f"  x-customer-code: {captured_headers.get('x-customer-code')}")

        # Set customer code to 1000052367 if 0
        api_headers = dict(captured_headers)
        if api_headers.get("x-customer-code") == "0":
            api_headers["x-customer-code"] = "1000052367"

        test_files = ["Agat1.pdf", "MD1000_D.pdf", "NE1027_1.pdf"]
        for tf in test_files:
            urls = [
                f"https://api-service.sirman.com/service-dwh/files/{tf}",
                f"https://api-service.sirman.com/service-dwh/products/234/exploded-views/677/file"
            ]

            for u in urls:
                resp = await ctx.request.get(u, headers=api_headers)
                body = await resp.body()
                print(f"[TEST] {u} -> Status: {resp.status}, Content-Type: {resp.headers.get('content-type')}, Size: {len(body)} bytes")
                if resp.status != 200:
                    print(f"   Body text: {body.decode('utf-8', errors='ignore')[:200]}")
                elif body.startswith(b'%PDF'):
                    with open(tf, "wb") as f:
                        f.write(body)
                    print(f"SUCCESSFULLY DOWNLOADED {tf}! ({len(body)/1024:.1f} KB)")
                    break

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
