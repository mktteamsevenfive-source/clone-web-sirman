"""
Test Geolocation Banner Dismissal & Catalog View
"""

import asyncio
from playwright.async_api import async_playwright

USERNAME = "korralak.sa@sevenfive.co.th"
PASSWORD = "Service@1234"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=100)
        ctx = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await ctx.new_page()

        print("[1] Navigating to login...")
        await page.goto("https://www.service.sirman.com/login", wait_until="domcontentloaded")

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

        # Close geolocation popup if present
        print("[2] Dismissing geolocation banner if present...")
        try:
            close_btn = await page.query_selector("button:has-text('X'), span:has-text('X'), [aria-label='Close']")
            if close_btn:
                await close_btn.click()
                print("  --> Clicked X on banner")
        except Exception as e:
            print(f"  --> Banner notice: {e}")

        # Navigate to catalog
        await page.goto("https://www.service.sirman.com/catalog", wait_until="domcontentloaded")
        await asyncio.sleep(3)

        # Screenshot catalog page
        await page.screenshot(path="real_catalog_page.png")
        print(f"[3] Catalog URL: {page.url}")

        # List category links
        cat_links = await page.query_selector_all("a[href*='catalog'], div[class*='category'], div[class*='Card']")
        print(f"Found {len(cat_links)} category elements:")
        for cl in cat_links[:15]:
            try:
                txt = (await cl.inner_text()).strip()
                if txt and len(txt) < 50:
                    print(f"  Category: '{txt}'")
            except:
                pass

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
