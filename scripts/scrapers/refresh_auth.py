import asyncio
import json
import sys
from pathlib import Path
from playwright.async_api import async_playwright
import requests

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
        browser = await p.chromium.launch(headless=False, slow_mo=100)
        ctx = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await ctx.new_page()

        async def on_request(req):
            if "api-service.sirman.com" in req.url:
                hdrs = dict(req.headers)
                if any(k.lower() in hdrs for k in ["authorization", "x-customer-code"]):
                    captured_hdrs.update({k: v for k, v in hdrs.items() if not k.startswith(":")})
                    print(f"  [AUTH CAPTURED] from {req.url[:80]}")

        page.on("request", on_request)

        print("[1] Navigating to Sirman catalog...")
        await page.goto("https://service.sirman.com/catalog", wait_until="domcontentloaded")
        await asyncio.sleep(2)

        # Check if already logged in or need to click LOGIN
        login_btn = await page.query_selector("button:has-text('LOGIN'), button:has-text('Accedi'), a:has-text('LOGIN')")
        if login_btn and await login_btn.is_visible():
            print("[2] Clicking Login button...")
            await login_btn.click()
            await asyncio.sleep(2)

        # Look for credentials input
        user_field = await page.query_selector("input[type='email'], input[name='username'], #inputEmail")
        pass_field = await page.query_selector("input[type='password'], input[name='password'], #inputPassword")

        if user_field and pass_field and await user_field.is_visible():
            print(f"[3] Filling credentials for {USERNAME}...")
            await user_field.fill(USERNAME)
            await pass_field.fill(PASSWORD)
            await asyncio.sleep(0.5)

            submit_btn = await page.query_selector("button[type='submit'], input[type='submit']")
            if submit_btn:
                await submit_btn.click()
                await asyncio.sleep(3)

        # Wait for network calls to settle and auth headers to be captured
        await asyncio.sleep(5)
        
        # Try navigating to a category page to ensure service-dwh headers are captured
        try:
            await page.goto("https://service.sirman.com/catalog", wait_until="networkidle")
            await asyncio.sleep(2)
        except Exception as e:
            print(f"  [NOTE] {e}")

        captured_cookies = await ctx.cookies()
        await browser.close()

    if captured_hdrs:
        with open(HEADERS_FILE, "w", encoding="utf-8") as f:
            json.dump({"headers": captured_hdrs, "cookies": captured_cookies}, f, indent=2)
        print(f"\n✅ Fresh auth session saved to {HEADERS_FILE}")

        # Verify
        session = requests.Session()
        clean = {k: v for k, v in captured_hdrs.items() if not k.startswith(":")}
        session.headers.update(clean)
        cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in captured_cookies)
        if cookie_str:
            session.headers["cookie"] = cookie_str

        r = session.get(f"{API_BASE}/service-dwh/categories", timeout=8)
        print(f"Test API verification: HTTP {r.status_code}")
        if r.status_code == 200:
            print("Auth refresh successful! Token active.")
            return True
    else:
        print("❌ Could not capture auth headers automatically.")
    return False

if __name__ == "__main__":
    asyncio.run(auto_refresh_session())
