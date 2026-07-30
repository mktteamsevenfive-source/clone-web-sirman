"""
SIRMAN ULTRA-HIGH RESOLUTION REAL DIAGRAM IMAGE DOWNLOADER
===========================================================
Fetches 100% authentic high-resolution exploded view diagrams directly from Sirman CloudFront CDN.
1. Authenticates session via session_state_eu.json
2. Extracts CloudFront signed URLs for all 150 unique diagram blueprints
3. Downloads & saves ultra-crisp PNG images to diagram_images/
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
SESSION_FILE = BASE_DIR / "session_state_eu.json"
IMG_DIR = BASE_DIR / "diagram_images"
IMG_DIR.mkdir(exist_ok=True)

captured_headers = {}


async def main():
    print("=" * 65)
    print("  SIRMAN REAL HIGH-RES DIAGRAM IMAGE DOWNLOADER")
    print("=" * 65)

    if not DATA_FILE.exists():
        print(f"[ERROR] {DATA_FILE} not found.")
        return

    if not SESSION_FILE.exists():
        print(f"[ERROR] {SESSION_FILE} not found.")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        catalog_data = json.load(f)

    products = catalog_data.get("products", [])

    # Extract unique PDF filenames
    pdf_map = {}
    for p in products:
        pdf_name = p.get("pdfName", "").strip()
        if pdf_name and pdf_name not in pdf_map:
            pdf_map[pdf_name] = p.get("model", "Unknown")

    pdf_items = list(pdf_map.items())
    print(f"[INFO] Loaded {len(products)} products -> {len(pdf_items)} unique diagram files.")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=50)
        ctx = await browser.new_context(
            storage_state=str(SESSION_FILE),
            viewport={"width": 1440, "height": 900},
            locale="en-GB",
            timezone_id="Europe/Rome",
            geolocation={"latitude": 45.4642, "longitude": 9.1900},
            permissions=["geolocation"]
        )
        page = await ctx.new_page()

        async def on_req(req):
            if "service-dwh" in req.url:
                hdrs = dict(req.headers)
                if "authorization" in hdrs:
                    captured_headers.update(hdrs)

        page.on("request", on_req)

        print("\n[STEP 1] Initializing DWH session headers...")
        await page.goto("https://www.service.sirman.com/home", wait_until="networkidle")
        await asyncio.sleep(2)

        cat_btn = await page.wait_for_selector("text=Catalog")
        if cat_btn:
            await cat_btn.click()
            await asyncio.sleep(3)

        if "authorization" not in captured_headers:
            print("[ERROR] Authorization token not captured.")
            return

        print(f"[SUCCESS] Authorization Token: {captured_headers['authorization'][:35]}...")
        print(f"[SUCCESS] Customer Code: {captured_headers.get('x-customer-code')}")

        print(f"\n[STEP 2] Downloading {len(pdf_items)} diagram blueprints directly from CloudFront CDN...")
        print("=" * 65)

        success_count = 0

        for idx, (pdf_name, model) in enumerate(pdf_items, 1):
            out_file = IMG_DIR / f"{pdf_name}.png"
            safe_model = model.encode('ascii', errors='ignore').decode('ascii').strip() or "Model"

            print(f"[{idx}/{len(pdf_items)}] {pdf_name} ({safe_model})...", end=" ")

            # Skip if already downloaded valid image (size > 200KB)
            if out_file.exists() and out_file.stat().st_size > 200000:
                # Check if it's not a 404 screenshot
                with open(out_file, "rb") as check_f:
                    header = check_f.read(8)
                    if header.startswith(b"\x89PNG") or header.startswith(b"\xff\xd8"):
                        print(f"Already downloaded ({out_file.stat().st_size/1024:.1f} KB)")
                        success_count += 1
                        continue

            # Format image key for Sirman DWH API
            # e.g. "NE1880-1840-1540-2740_1.pdf" -> "ne1880-1840-1540-2740_1.png"
            base_key = pdf_name.replace(".pdf", ".png").lower()
            api_url = f"https://api-service.sirman.com/service-dwh/resources/exploded-view/jpeg/{base_key}?quality=full"

            try:
                resp = await ctx.request.get(api_url, headers=captured_headers)
                if resp.status == 200:
                    data = await resp.json()
                    signed_url = data.get("url")

                    if signed_url:
                        img_resp = await ctx.request.get(signed_url)
                        if img_resp.status == 200:
                            img_bytes = await img_resp.body()
                            if len(img_bytes) > 20000:  # Valid image (> 20KB)
                                with open(out_file, "wb") as f:
                                    f.write(img_bytes)
                                print(f"SUCCESS ({len(img_bytes)/1024:.1f} KB)")
                                success_count += 1
                                continue

                print(f"Not found (Status {resp.status})")
            except Exception as err:
                print(f"Error: {err}")

            time.sleep(0.05)

        await browser.close()

    print("\n" + "=" * 65)
    print(f"  REAL DIAGRAM BLUEPRINTS DOWNLOAD COMPLETED!")
    print(f"  Downloaded: {success_count}/{len(pdf_items)} images")
    print(f"  Image folder: {IMG_DIR}")
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(main())
