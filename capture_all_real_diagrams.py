"""
SIRMAN REAL DIAGRAM CAPTURER (Using Authenticated session_state.json)
=====================================================================
1. Loads saved session_state.json (100% authenticated)
2. Navigates Sirman Catalog DOM: Click Category -> Click Product Model
3. Captures the REAL diagram image rendered on screen by Sirman's website
4. Saves high-res PNG images into diagram_images/
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / "sirman_catalog_data.json"
SESSION_FILE = BASE_DIR / "session_state.json"
IMG_DIR = BASE_DIR / "diagram_images"
IMG_DIR.mkdir(exist_ok=True)


async def main():
    print("=" * 65)
    print("  SIRMAN REAL DIAGRAM CAPTURER (AUTHENTICATED SESSION)")
    print("=" * 65)

    if not DATA_FILE.exists():
        print(f"[ERROR] {DATA_FILE} not found.")
        return

    if not SESSION_FILE.exists():
        print(f"[ERROR] {SESSION_FILE} not found. Run save_login_session.py first.")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        catalog_data = json.load(f)

    categories = catalog_data.get("categories", [])
    products = catalog_data.get("products", [])

    print(f"[INFO] Loaded {len(categories)} categories and {len(products)} products.")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=50, args=["--start-maximized"])
        
        # Load saved authenticated storage state!
        ctx = await browser.new_context(
            storage_state=str(SESSION_FILE),
            viewport={"width": 1440, "height": 900}
        )
        page = await ctx.new_page()

        # Track network media responses
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

        print("\n[STEP 1] Opening Catalog page with authenticated session...")
        await page.goto("https://www.service.sirman.com/catalog", wait_until="domcontentloaded")
        await asyncio.sleep(3)

        # Dismiss geolocation banner if present
        try:
            banner_close = await page.query_selector("button:has-text('X'), span:has-text('X')")
            if banner_close:
                await banner_close.click()
                await asyncio.sleep(1)
        except:
            pass

        print(f"[INFO] Catalog URL: {page.url}")

        success_count = 0

        # Loop products grouped by category
        for cat in categories:
            cat_name = cat["name"]
            cat_prods = [p for p in products if p["categoryId"] == cat["id"]]
            if not cat_prods:
                continue

            print(f"\n--- Category: {cat_name} ({len(cat_prods)} products) ---")

            # Go to catalog main
            try:
                await page.goto("https://www.service.sirman.com/catalog", wait_until="domcontentloaded")
                await asyncio.sleep(2)

                # Click category card/link
                cat_btn = await page.query_selector(f"text='{cat_name}'")
                if cat_btn:
                    await cat_btn.click()
                    await asyncio.sleep(2.5)
            except Exception as cat_err:
                print(f"[WARN] Category click: {cat_err}")
                continue

            for p in cat_prods:
                pdf_name = p.get("pdfName", "").strip()
                p_name = p.get("model", "Unknown")

                if not pdf_name:
                    continue

                img_path = IMG_DIR / f"{pdf_name}.png"
                safe_model = p_name.encode('ascii', errors='ignore').decode('ascii').strip() or "Model"

                print(f"  --> {p_name} ({pdf_name})...", end=" ")

                # If file exists and is larger than 30KB (not 404 image)
                if img_path.exists() and img_path.stat().st_size > 35000:
                    print("Already saved valid diagram")
                    success_count += 1
                    continue

                media_blobs.clear()

                try:
                    # Click on product row in category table
                    p_btn = await page.query_selector(f"text='{p_name}'")
                    if p_btn:
                        await p_btn.click()
                        await asyncio.sleep(3.5)

                    # Look for real diagram elements
                    saved = False

                    # Check network blobs first
                    if media_blobs:
                        largest_u = max(media_blobs, key=lambda k: len(media_blobs[k]))
                        blob_data = media_blobs[largest_u]
                        if len(blob_data) > 10000:
                            with open(img_path, "wb") as f:
                                f.write(blob_data)
                            saved = True
                            print(f"Captured network diagram ({len(blob_data)/1024:.1f} KB)")

                    if not saved:
                        for sel in ["canvas", "svg[class*='diagram']", "[class*='diagram']", ".pdf-viewer", "img[src*='file']"]:
                            el = await page.query_selector(sel)
                            if el:
                                box = await el.bounding_box()
                                if box and box["width"] > 150 and box["height"] > 150:
                                    await el.screenshot(path=str(img_path))
                                    saved = True
                                    print(f"Captured diagram element ({img_path.stat().st_size/1024:.1f} KB)")
                                    break

                    if not saved:
                        print("Not loaded yet")
                    else:
                        success_count += 1

                except Exception as p_err:
                    print(f"Click err: {p_err}")

        await browser.close()

    print("\n" + "=" * 65)
    print(f"  REAL DIAGRAM CAPTURE COMPLETED: {success_count}/{len(products)} images saved!")
    print(f"  Image folder: {IMG_DIR}")
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(main())
