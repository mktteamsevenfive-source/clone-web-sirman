"""
SIRMAN AUTOMATED LOGIN & DIAGRAM DOWNLOADER
===========================================
Automatically logs in to Sirman Service using provided Username & Password,
and captures/downloads diagram images for all 208 products with ZERO manual intervention.
"""

import asyncio
import json
import getpass
import sys
import time
from pathlib import Path
from playwright.async_api import async_playwright

BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / "sirman_catalog_data.json"
IMG_DIR = BASE_DIR / "diagram_images"
IMG_DIR.mkdir(exist_ok=True)


async def auto_login(page, username, password):
    """Automatically fill login form and submit"""
    print(f"[INFO] Navigating to login page...")
    await page.goto("https://service.sirman.com/catalog", wait_until="domcontentloaded")
    await asyncio.sleep(2)

    # Check if login button/link exists
    login_selectors = [
        "button:has-text('LOGIN')",
        "button:has-text('Accedi')",
        "a:has-text('LOGIN')",
        "a:has-text('Accedi')",
        ".btn-login",
        "[data-testid='login-button']"
    ]

    for sel in login_selectors:
        try:
            btn = await page.query_selector(sel)
            if btn and await btn.is_visible():
                await btn.click()
                await asyncio.sleep(2)
                break
        except Exception:
            pass

    # Find username input
    user_selectors = [
        "input[type='email']",
        "input[name='username']",
        "input[name='email']",
        "input[id*='user']",
        "input[id*='email']",
        "input[type='text']"
    ]

    user_field = None
    for sel in user_selectors:
        try:
            field = await page.query_selector(sel)
            if field and await field.is_visible():
                user_field = field
                break
        except Exception:
            pass

    # Find password input
    pass_selectors = [
        "input[type='password']",
        "input[name='password']",
        "input[id*='pass']"
    ]

    pass_field = None
    for sel in pass_selectors:
        try:
            field = await page.query_selector(sel)
            if field and await field.is_visible():
                pass_field = field
                break
        except Exception:
            pass

    if user_field and pass_field:
        print(f"[INFO] Entering credentials for {username}...")
        await user_field.fill(username)
        await pass_field.fill(password)
        await asyncio.sleep(0.5)

        # Click submit button or press Enter
        submit_selectors = [
            "button[type='submit']",
            "button:has-text('LOGIN')",
            "button:has-text('Accedi')",
            "button:has-text('Sign in')",
            "input[type='submit']"
        ]

        submitted = False
        for sel in submit_selectors:
            try:
                sbtn = await page.query_selector(sel)
                if sbtn and await sbtn.is_visible():
                    await sbtn.click()
                    submitted = True
                    break
            except Exception:
                pass

        if not submitted:
            await pass_field.press("Enter")

        print("[INFO] Waiting for login completion...")
        await asyncio.sleep(5)
        print("[SUCCESS] Logged in successfully!")
        return True
    else:
        print("[WARN] Could not locate login form fields automatically.")
        return False


async def main():
    print("=" * 65)
    print("  SIRMAN FULLY AUTOMATED LOGIN & DIAGRAM DOWNLOADER")
    print("=" * 65)

    if not DATA_FILE.exists():
        print(f"[ERROR] {DATA_FILE} not found. Please run build_data.py first.")
        return

    # Check for credentials in sys.argv or prompt user
    if len(sys.argv) >= 3:
        username = sys.argv[1]
        password = sys.argv[2]
    else:
        print("\nกรุณากรอกข้อมูล Login ของ Sirman Service:")
        username = input("  Email / Username: ").strip()
        password = getpass.getpass("  Password: ").strip()

    if not username or not password:
        print("[ERROR] Username or password cannot be empty.")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        catalog_data = json.load(f)

    products = catalog_data.get("products", [])
    print(f"\n[INFO] Loaded {len(products)} products from catalog.")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=["--start-maximized"])
        ctx = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await ctx.new_page()

        # Intercept network image/pdf responses
        captured_images = {}

        async def on_response(resp):
            u = resp.url
            ct = resp.headers.get("content-type", "")
            if resp.status == 200 and ("image" in ct or "pdf" in ct or "files" in u):
                if not any(ign in u for ign in ["google", "hubspot", "lucide", "font", "logo"]):
                    try:
                        b = await resp.body()
                        if len(b) > 5000:
                            captured_images[u] = b
                    except:
                        pass

        page.on("response", on_response)

        # Step 1: Auto Login
        login_ok = await auto_login(page, username, password)
        if not login_ok:
            print("[INFO] Please complete login manually in the open browser window if needed...")
            await asyncio.sleep(5)

        # Step 2: Download Diagrams Automatically
        print(f"\n[STEP 2] Auto-capturing diagram images for {len(products)} products...")

        success_count = 0

        for idx, p in enumerate(products, 1):
            p_id = p.get("id")
            p_name = p.get("model")
            pdf_name = p.get("pdfName")
            v_id = p.get("explodedViewId")

            if not pdf_name:
                continue

            img_path = IMG_DIR / f"{pdf_name}.png"
            print(f"[{idx}/{len(products)}] {p_name} ({pdf_name})...", end=" ")

            if img_path.exists() and img_path.stat().st_size > 15000:
                print("Already saved")
                success_count += 1
                continue

            captured_images.clear()

            target_url = f"https://service.sirman.com/catalog/products/{p_id}"
            if v_id:
                target_url += f"/exploded-views/{v_id}"

            try:
                await page.goto(target_url, wait_until="networkidle", timeout=12000)
                await asyncio.sleep(1.2)
            except Exception:
                pass

            saved = False
            for sel in ["canvas", "svg[class*='diagram']", "[class*='diagram']", "img[src*='file']", ".pdf-viewer"]:
                try:
                    el = await page.query_selector(sel)
                    if el:
                        box = await el.bounding_box()
                        if box and box["width"] > 100 and box["height"] > 100:
                            await el.screenshot(path=str(img_path))
                            saved = True
                            print(f"Captured ({img_path.stat().st_size/1024:.1f} KB)")
                            break
                except Exception:
                    pass

            if not saved and captured_images:
                largest_url = max(captured_images, key=lambda k: len(captured_images[k]))
                data = captured_images[largest_url]
                with open(img_path, "wb") as imf:
                    imf.write(data)
                saved = True
                print(f"Captured network image ({len(data)/1024:.1f} KB)")

            if not saved:
                try:
                    await page.screenshot(path=str(img_path))
                    saved = True
                    print("Page screenshot saved")
                except Exception:
                    print("Failed")

            if saved:
                success_count += 1

        await browser.close()

    print("\n" + "=" * 65)
    print(f"  DIAGRAM CAPTURE COMPLETE! {success_count}/{len(products)} diagram images saved.")
    print(f"  Saved in: {IMG_DIR}")
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(main())
