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

async def login_and_capture():
    print("==================================================")
    print("  SIRMAN AUTHENTICATION & HEADER CAPTURE")
    print("==================================================")

    captured_hdrs = {}
    captured_cookies = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=200)
        ctx = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await ctx.new_page()

        async def on_request(req):
            if "api-service.sirman.com" in req.url:
                hdrs = dict(req.headers)
                has_auth = "authorization" in hdrs and hdrs.get("authorization", "").startswith("Bearer ")
                if has_auth:
                    captured_hdrs.clear()
                    captured_hdrs.update({k: v for k, v in hdrs.items() if not k.startswith(":")})
                    print(f"[AUTH CAPTURED] Token from: {req.url[:80]}")

        page.on("request", on_request)

        # Try direct login URL first
        print("[1] Navigating to Sirman login page...")
        try:
            await page.goto("https://service.sirman.com/login", wait_until="networkidle", timeout=15000)
        except Exception:
            await page.goto("https://service.sirman.com/catalog", wait_until="domcontentloaded", timeout=15000)

        await asyncio.sleep(3)

        # Try to find and fill login form
        for attempt in range(3):
            user_field = await page.query_selector("input[type='email'], input[name='email'], input[name='username'], #email, #username")
            pass_field = await page.query_selector("input[type='password']")

            if user_field and pass_field:
                print(f"[2] Found login form (attempt {attempt+1})...")
                try:
                    await user_field.click()
                    await user_field.fill("")
                    await user_field.type(USERNAME, delay=50)
                    await pass_field.click()
                    await pass_field.fill("")
                    await pass_field.type(PASSWORD, delay=50)
                    await asyncio.sleep(1)

                    submit_btn = await page.query_selector("button[type='submit'], input[type='submit'], button:has-text('Login'), button:has-text('Accedi'), button:has-text('Sign in')")
                    if submit_btn:
                        print("[3] Submitting login...")
                        await submit_btn.click()
                        await asyncio.sleep(5)
                    break
                except Exception as e:
                    print(f"  [WARN] Form fill error: {e}")
                    break
            else:
                # Try clicking a login link
                login_link = await page.query_selector("a[href*='login'], button:has-text('LOGIN'), a:has-text('Login'), a:has-text('Accedi')")
                if login_link:
                    print(f"[2] Clicking login link (attempt {attempt+1})...")
                    await login_link.click()
                    await asyncio.sleep(3)
                else:
                    print(f"  [WARN] No login form found (attempt {attempt+1}), waiting...")
                    await asyncio.sleep(3)

        # Navigate to catalog to trigger API calls
        print("[4] Navigating to catalog to trigger API requests...")
        await page.goto("https://service.sirman.com/catalog", wait_until="networkidle", timeout=20000)

        print("[5] Waiting for authenticated API requests (up to 30s)...")
        for i in range(15):
            if captured_hdrs:
                print("  [OK] Auth token captured!")
                break
            await asyncio.sleep(2)
            if i % 3 == 2:
                print(f"  ...waiting {(i+1)*2}s...")

        captured_cookies = await ctx.cookies()

        if not captured_hdrs:
            # Print current URL and page title to help debug
            print(f"  [DEBUG] Current URL: {page.url}")
            print(f"  [DEBUG] Page title: {await page.title()}")

        await browser.close()

    if captured_hdrs:
        with open(HEADERS_FILE, "w", encoding="utf-8") as f:
            json.dump({"headers": captured_hdrs, "cookies": captured_cookies}, f, indent=2)
        print(f"[SUCCESS] Auth session saved to {HEADERS_FILE.name}")

        # Verify
        session = requests.Session()
        clean = {k: v for k, v in captured_hdrs.items() if not k.startswith(":")}
        session.headers.update(clean)
        cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in captured_cookies)
        if cookie_str:
            session.headers["cookie"] = cookie_str

        r = session.get(f"{API_BASE}/service-dwh/categories", timeout=10)
        print(f"[TEST API] HTTP {r.status_code}")
        if r.status_code == 200:
            print("[AUTH VALIDATED] Token active and working!")
            return True
        else:
            print(f"[FAIL] API returned: {r.text[:200]}")
    else:
        print("[ERROR] No auth headers captured.")
        print("  -> กรุณาลองเข้า https://service.sirman.com แล้ว Login ด้วยตัวเองก่อน")
        print("  -> แล้วรัน script นี้ใหม่ (browser จะเปิดขึ้นมา ไม่ต้องทำอะไรเพิ่ม)")
    return False

if __name__ == "__main__":
    asyncio.run(login_and_capture())

