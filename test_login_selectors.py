"""
Inspect Sirman Login Form Selectors & Auto Login Test
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

        print("[1] Navigating to https://service.sirman.com ...")
        await page.goto("https://service.sirman.com", wait_until="networkidle")
        await page.wait_for_timeout(3000)

        print(f"Current URL: {page.url}")

        # Screenshot login page
        await page.screenshot(path="login_page_preview.png")

        # Find all buttons and inputs
        inputs = await page.query_selector_all("input")
        print(f"Found {len(inputs)} inputs:")
        for i in inputs:
            itype = await i.get_attribute("type")
            iname = await i.get_attribute("name")
            iid = await i.get_attribute("id")
            ipth = await i.get_attribute("placeholder")
            print(f"  Input: type={itype}, name={iname}, id={iid}, placeholder={ipth}")

        buttons = await page.query_selector_all("button, a, input[type='submit']")
        print(f"\nFound {len(buttons)} clickable elements:")
        for b in buttons:
            txt = (await b.inner_text()).strip()
            if txt:
                print(f"  Element text: '{txt}'")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
