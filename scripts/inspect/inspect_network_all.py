"""
Sirman Frontend Network Tracer - Find Exact Diagram Endpoint
"""

import asyncio
import json
from playwright.async_api import async_playwright

USERNAME = "korralak.sa@sevenfive.co.th"
PASSWORD = "Service@1234"

all_requests = []

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=50)
        ctx = await browser.new_context()
        page = await ctx.new_page()

        async def on_req(req):
            u = req.url
            if not any(ign in u for ign in ["google", "hubspot", "analytics", "font", "css", "chunk.js"]):
                headers = dict(req.headers)
                all_requests.append((req.method, u, headers))

        page.on("request", on_req)

        print("[1] Opening login page...")
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

        print(f"[2] Post-login URL: {page.url}")

        # Clear request log before opening exploded view
        all_requests.clear()

        # Open product exploded view API directly or navigate
        print("[3] Fetching product views API...")
        # Get views for product 234 (AGATA 250) or product 5165 (MD 1000 Digital)
        view_res = await page.evaluate("""async () => {
            const token = localStorage.getItem('token') || sessionStorage.getItem('token') || '';
            const r1 = await fetch('https://api-service.sirman.com/service-dwh/products/234/exploded-views');
            const data1 = await r1.json();
            
            const r2 = await fetch('https://api-service.sirman.com/service-dwh/products/5165/exploded-views');
            const data2 = await r2.json();
            
            return { data1, data2 };
        }""")

        print(f"Views Data 1 (AGATA): {json.dumps(view_res['data1'], indent=2)[:500]}")
        print(f"Views Data 2 (MD1000): {json.dumps(view_res['data2'], indent=2)[:500]}")

        print("\n[4] All API requests captured during evaluation:")
        for method, u, hdrs in all_requests:
            print(f"  {method} {u}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
