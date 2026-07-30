"""
Find Real Sirman PDF & Diagram Image URLs
===========================================
Fully automated login using credentials, navigates to product exploded view,
and captures every single network request to find exact diagram URLs.
"""

import asyncio
from playwright.async_api import async_playwright

USERNAME = "korralak.sa@sevenfive.co.th"
PASSWORD = "Service@1234"

captured_urls = []


async def main():
    print("=" * 65)
    print("  SIRMAN REAL DIAGRAM URL TRACER v2")
    print("=" * 65)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=100, args=["--start-maximized"])
        ctx = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await ctx.new_page()

        async def on_response(response):
            u = response.url
            ct = response.headers.get("content-type", "")
            st = response.status
            if not any(ign in u for ign in ["hubspot", "google", "analytics", "lucide", "font", "css", "chunk.js"]):
                info = f"{st} | {ct[:30]} | {u}"
                captured_urls.append(info)
                print(f"  [NET] {info}")

        page.on("response", on_response)

        print("\n[STEP 1] Opening login page...")
        await page.goto("https://www.service.sirman.com/login", wait_until="networkidle")
        await asyncio.sleep(2)

        # Wait for LOGIN button in React app
        try:
            print("[INFO] Waiting for LOGIN button...")
            login_btn = await page.wait_for_selector("button:has-text('LOGIN'), .login-btn", timeout=15000)
            if login_btn:
                print("[INFO] Clicking LOGIN button...")
                await login_btn.click()
                await asyncio.sleep(3)
        except Exception as e:
            print(f"[WARN] Login button click: {e}")

        # Wait for redirected Auth inputs
        try:
            print("[INFO] Waiting for auth form inputs...")
            user_el = await page.wait_for_selector("#inputEmail, input[type='email'], input[name='email']", timeout=15000)
            pass_el = await page.wait_for_selector("#inputPassword, input[type='password'], input[name='password']", timeout=15000)

            if user_el and pass_el:
                print("[INFO] Filling credentials...")
                await user_el.fill(USERNAME)
                await pass_el.fill(PASSWORD)
                await asyncio.sleep(0.5)

                print("[INFO] Submitting form...")
                submit_btn = await page.query_selector("button[type='submit'], input[type='submit']")
                if submit_btn:
                    await submit_btn.click()
                else:
                    await pass_el.press("Enter")

                print("[INFO] Logged in! Waiting for catalog load...")
                await page.wait_for_timeout(6000)
        except Exception as e:
            print(f"[WARN] Form fill error: {e}")

        print("\n[STEP 2] Navigating to Slicers category...")
        try:
            await page.goto("https://service.sirman.com/catalog", wait_until="networkidle")
            await asyncio.sleep(2)

            # Click Slicers card or link
            slicers = await page.wait_for_selector("text=Slicers", timeout=10000)
            if slicers:
                await slicers.click()
                await asyncio.sleep(3)

            # Click AGATA product
            agata = await page.wait_for_selector("text=AGATA 250", timeout=10000)
            if agata:
                await agata.click()
                await asyncio.sleep(4)
        except Exception as err:
            print(f"[WARN] Catalog navigation: {err}")

        print("\n[STEP 3] ALL CAPTURED API / MEDIA URLS:")
        print("=" * 65)
        for item in captured_urls:
            if any(x in item.lower() for x in ["pdf", "view", "exploded", "draw", "img", "file", "products", "dwh", "media"]):
                print(f"  --> {item}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
