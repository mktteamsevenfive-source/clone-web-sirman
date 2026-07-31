"""
Inspect Post-Login Page Structure
"""

import asyncio
from playwright.async_api import async_playwright

USERNAME = "korralak.sa@sevenfive.co.th"
PASSWORD = "Service@1234"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=100)
        ctx = await browser.new_context()
        page = await ctx.new_page()

        print("[1] Opening login page...")
        await page.goto("https://www.service.sirman.com/login", wait_until="networkidle")

        login_btn = await page.wait_for_selector("button:has-text('LOGIN'), .login-btn")
        if login_btn:
            await login_btn.click()
            await asyncio.sleep(2)

        user_el = await page.wait_for_selector("#inputEmail, input[type='email']", timeout=10000)
        pass_el = await page.wait_for_selector("#inputPassword, input[type='password']", timeout=10000)

        if user_el and pass_el:
            print("[2] Filling credentials and logging in...")
            await user_el.fill(USERNAME)
            await pass_el.fill(PASSWORD)
            await page.click("button[type='submit'], input[type='submit']")

        print("[3] Waiting 8 seconds for post-login navigation...")
        await page.wait_for_timeout(8000)

        print(f"Current URL post-login: {page.url}")

        # Screenshot post login page
        await page.screenshot(path="post_login_preview.png")

        # List all text elements, links, buttons
        elements = await page.query_selector_all("button, a, div[class*='card'], [role='button']")
        print(f"Found {len(elements)} clickable elements post-login:")
        for el in elements[:20]:
            try:
                txt = (await el.inner_text()).strip()
                if txt and len(txt) < 100:
                    print(f"  - '{txt[:50]}'")
            except:
                pass

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
