"""
Sirman DOM Navigation & Diagram Screen Capturer
================================================
Navigates the Sirman website like a real user (clicks Category -> Product -> Exploded View),
and captures the rendered diagram directly from the browser window.
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / "sirman_catalog_data.json"
IMG_DIR = BASE_DIR / "diagram_images"
IMG_DIR.mkdir(exist_ok=True)

USERNAME = "korralak.sa@sevenfive.co.th"
PASSWORD = "Service@1234"


async def main():
    print("=" * 65)
    print("  SIRMAN DOM NAVIGATION DIAGRAM CAPTURER")
    print("=" * 65)

    if not DATA_FILE.exists():
        print(f"[ERROR] {DATA_FILE} not found.")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        catalog_data = json.load(f)

    categories = catalog_data.get("categories", [])
    products = catalog_data.get("products", [])

    print(f"[INFO] Loaded {len(categories)} categories and {len(products)} products.")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=50, args=["--start-maximized"])
        ctx = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await ctx.new_page()

        # Intercept any image/pdf files loaded by the page
        media_blobs = {}

        async def on_resp(resp):
            u = resp.url
            ct = resp.headers.get("content-type", "")
            if resp.status == 200 and ("image" in ct or "pdf" in ct or "files" in u):
                if not any(ign in u for ign in ["google", "hubspot", "lucide", "font", "logo"]):
                    try:
                        b = await resp.body()
                        if len(b) > 4000:
                            media_blobs[u] = b
                    except:
                        pass

        page.on("response", on_resp)

        # STEP 1: Login
        print("\n[STEP 1] Logging in...")
        await page.goto("https://www.service.sirman.com/login", wait_until="networkidle")

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

        # STEP 2: Navigate Catalog
        print("\n[STEP 2] Navigating Catalog to capture diagrams...")
        await page.goto("https://www.service.sirman.com/catalog", wait_until="networkidle")
        await asyncio.sleep(3)

        success_count = 0

        # Loop categories
        for cat in categories:
            cat_name = cat["name"]
            cat_prods = [p for p in products if p["categoryId"] == cat["id"]]
            if not cat_prods:
                continue

            print(f"\n--- Category: {cat_name} ({len(cat_prods)} products) ---")

            # Click Category link in sidebar or card
            try:
                await page.goto("https://www.service.sirman.com/catalog", wait_until="domcontentloaded")
                await asyncio.sleep(2)

                cat_link = await page.query_selector(f"text='{cat_name}'")
                if cat_link:
                    await cat_link.click()
                    await asyncio.sleep(2.5)
            except Exception as cat_err:
                print(f"[WARN] Category click: {cat_err}")
                continue

            # Iterate products in this category
            for p in cat_prods:
                pdf_name = p.get("pdfName", "").strip()
                p_name = p.get("model", "Unknown")

                if not pdf_name:
                    continue

                img_path = IMG_DIR / f"{pdf_name}.png"
                safe_model = p_name.encode('ascii', errors='ignore').decode('ascii').strip() or "Model"
                print(f"  --> {p_name} ({pdf_name})...", end=" ")

                if img_path.exists() and img_path.stat().st_size > 10000:
                    print("Already saved")
                    success_count += 1
                    continue

                media_blobs.clear()

                try:
                    # Click on product row/text
                    p_el = await page.query_selector(f"text='{p_name}'")
                    if p_el:
                        await p_el.click()
                        await asyncio.sleep(3)

                    # Look for diagram image/canvas on page
                    saved = False
                    for sel in ["canvas", "svg[class*='diagram']", "[class*='diagram']", ".pdf-viewer", "img[src*='file']"]:
                        el = await page.query_selector(sel)
                        if el:
                            box = await el.bounding_box()
                            if box and box["width"] > 100 and box["height"] > 100:
                                await el.screenshot(path=str(img_path))
                                saved = True
                                print(f"Captured screenshot ({img_path.stat().st_size/1024:.1f} KB)")
                                break

                    if not saved and media_blobs:
                        largest_u = max(media_blobs, key=lambda k: len(media_blobs[k]))
                        with open(img_path, "wb") as imf:
                            imf.write(media_blobs[largest_u])
                        saved = True
                        print(f"Captured network blob ({len(media_blobs[largest_u])/1024:.1f} KB)")

                    if not saved:
                        print("Not displayed")
                    else:
                        success_count += 1
                except Exception as err:
                    print(f"Click err: {err}")

        await browser.close()

    print("\n" + "=" * 65)
    print(f"  DOM CAPTURE COMPLETED: {success_count} diagram images saved!")
    print(f"  Image folder: {IMG_DIR}")
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(main())
