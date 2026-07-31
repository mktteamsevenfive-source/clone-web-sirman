"""
Save Sirman Logged-in Session State to Disk (Robust Version)
============================================================
1. Opens Chromium
2. Performs automated login using korralak.sa@sevenfive.co.th / Service@1234
3. Saves full session storage state to session_state.json
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

BASE_DIR = Path(__file__).parent
SESSION_FILE = BASE_DIR / "session_state.json"
USERNAME = "korralak.sa@sevenfive.co.th"
PASSWORD = "Service@1234"

async def main():
    print("=" * 65)
    print("  SIRMAN SESSION SAVER")
    print("=" * 65)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=100)
        ctx = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await ctx.new_page()

        print("[1] Opening login page...")
        await page.goto("https://www.service.sirman.com/login", wait_until="domcontentloaded")
        await asyncio.sleep(2)

        try:
            print("[2] Clicking red LOGIN button...")
            await page.click("button:has-text('LOGIN'), .login-btn", timeout=10000)
            await asyncio.sleep(3)
        except Exception as e:
            print(f"[WARN] Login click notice: {e}")

        try:
            print("[3] Filling credentials...")
            await page.wait_for_selector("#inputEmail, input[type='email']", timeout=10000)
            await page.fill("#inputEmail, input[type='email']", USERNAME)
            await page.fill("#inputPassword, input[type='password']", PASSWORD)
            await page.click("button[type='submit'], input[type='submit']")
            await asyncio.sleep(4)
        except Exception as e:
            print(f"[WARN] Auth fill notice: {e}")

        try:
            print("[4] Checking for Authorize button...")
            auth_btn = await page.query_selector("button:has-text('Authorize')")
            if auth_btn:
                await auth_btn.click()
                await asyncio.sleep(4)
        except Exception as e:
            print(f"[WARN] Authorize click notice: {e}")

        print(f"[5] Current URL: {page.url}")

        # Save session state
        await ctx.storage_state(path=str(SESSION_FILE))
        print(f"[SUCCESS] Saved session state to {SESSION_FILE}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
