"""
Sirman European Session Saver (Italy/EU Geolocation Context)
============================================================
Sets browser geolocation/locale to Italy (Europe) to prevent Sirman US redirect.
Performs automated login and saves session_state_eu.json.
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

BASE_DIR = Path(__file__).parent
SESSION_FILE = BASE_DIR / "session_state_eu.json"
USERNAME = "korralak.sa@sevenfive.co.th"
PASSWORD = "Service@1234"

async def main():
    print("=" * 65)
    print("  SIRMAN EUROPEAN SESSION SAVER")
    print("=" * 65)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=100)
        
        # Set geolocation to Italy (Sirman HQ) to avoid US redirect banner!
        ctx = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="en-GB",
            timezone_id="Europe/Rome",
            geolocation={"latitude": 45.4642, "longitude": 9.1900},
            permissions=["geolocation"]
        )
        page = await ctx.new_page()

        print("[1] Navigating to European login page...")
        await page.goto("https://www.service.sirman.com/login", wait_until="networkidle")
        await asyncio.sleep(2)

        print("[2] Clicking LOGIN button...")
        await page.click("button:has-text('LOGIN'), .login-btn")
        await asyncio.sleep(3)

        print("[3] Entering credentials...")
        user_el = await page.wait_for_selector("#inputEmail, input[type='email']")
        pass_el = await page.wait_for_selector("#inputPassword, input[type='password']")

        await user_el.fill(USERNAME)
        await pass_el.fill(PASSWORD)
        await page.click("button[type='submit'], input[type='submit']")
        await asyncio.sleep(4)

        print("[4] Checking for Authorize button...")
        auth_btn = await page.query_selector("button:has-text('Authorize')")
        if auth_btn:
            await auth_btn.click()
            await asyncio.sleep(4)

        print(f"[5] Post-login URL: {page.url}")
        await page.screenshot(path="eu_post_login.png")

        # Save European session state
        await ctx.storage_state(path=str(SESSION_FILE))
        print(f"[SUCCESS] Saved European session state to {SESSION_FILE}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
