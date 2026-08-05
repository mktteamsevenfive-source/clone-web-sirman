import asyncio
import json
import sys
from pathlib import Path
from playwright.async_api import async_playwright
import requests

# Ensure stdout supports UTF-8 on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
HEADERS_FILE = ROOT_DIR / "sirman_headers.json"
USERNAME = "korralak.sa@sevenfive.co.th"
PASSWORD = "Service@1234"
API_BASE = "https://api-service.sirman.com"

async def auto_refresh_session():
    print("=" * 65)
    print("  SIRMAN AUTO AUTH SESSION REFRESH")
    print("=" * 65)

    captured_hdrs = {}
    captured_cookies = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await ctx.new_page()

        async def on_request(req):
            if "api-service.sirman.com" in req.url:
                hdrs = dict(req.headers)
                if "authorization" in hdrs:
                    captured_hdrs.update({k: v for k, v in hdrs.items() if not k.startswith(":")})
                    print(f"  [BEARER AUTH CAPTURED!] from {req.url[:80]}")

        page.on("request", on_request)

        print("[1] Navigating to Sirman login...")
        await page.goto("https://service.sirman.com/login", wait_until="domcontentloaded")
        await asyncio.sleep(3)

        # Look for credentials input
        user_field = await page.query_selector("input[type='email'], input[name='username'], input[name='email'], #inputEmail")
        pass_field = await page.query_selector("input[type='password'], input[name='password'], #inputPassword")

        if user_field and pass_field and await user_field.is_visible():
            print(f"[2] Filling credentials for {USERNAME}...")
            await user_field.fill(USERNAME)
            await pass_field.fill(PASSWORD)
            await asyncio.sleep(0.5)

            submit_btn = await page.query_selector("button[type='submit'], input[type='submit']")
            if submit_btn:
                await submit_btn.click()
                await asyncio.sleep(5)

        print("[3] Navigating to a product page to trigger API requests...")
        try:
            await page.goto("https://www.service.sirman.com/products/2775/tavola/11832", wait_until="networkidle")
            await asyncio.sleep(4)
        except Exception as e:
            print(f"  [NOTE] {e}")

        captured_cookies = await ctx.cookies()
        await browser.close()

    if captured_hdrs:
        with open(HEADERS_FILE, "w", encoding="utf-8") as f:
            json.dump({"headers": captured_hdrs, "cookies": captured_cookies}, f, indent=2)
        print(f"\n[OK] Fresh auth session saved to {HEADERS_FILE.name}")

        # Verify
        session = requests.Session()
        clean = {k: v for k, v in captured_hdrs.items() if not k.startswith(":")}
        session.headers.update(clean)
        cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in captured_cookies)
        if cookie_str:
            session.headers["cookie"] = cookie_str

        r = session.get(f"{API_BASE}/service-dwh/products/2775/exploded-views", timeout=8)
        print(f"Test Product 2775 API verification: HTTP {r.status_code}")
        if r.status_code == 200:
            print("[SUCCESS] Auth refresh successful! Token active.")
            return True
    else:
        print("[FAIL] Could not capture auth headers automatically.")
    return False

if __name__ == "__main__":
    asyncio.run(auto_refresh_session())
