"""
SIRMAN 100% ENGLISH HIGH-RES BLUEPRINT DIAGRAM DOWNLOADER
===========================================================
Ensures x-language: en is passed to API to fetch authentic ENGLISH diagram blueprints
from Sirman CloudFront CDN, overwriting any previous 404/Italian images.
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stdout.flush()

BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / "sirman_catalog_data.json"
SESSION_FILE = BASE_DIR / "session_state_eu.json"
IMG_DIR = BASE_DIR / "diagram_images"
IMG_DIR.mkdir(exist_ok=True)

captured_headers = {}


async def main():
    print("=" * 65)
    print("  SIRMAN 100% ENGLISH DIAGRAM BLUEPRINT DOWNLOADER")
    print("=" * 65)

    if not DATA_FILE.exists() or not SESSION_FILE.exists():
        print("[ERROR] Required JSON files missing.")
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
    print(f"[INFO] Processing {len(pdf_items)} unique diagram blueprints in ENGLISH...")

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

        print("\n[STEP 1] Fetching DWH Authorization Token...")
        await page.goto("https://www.service.sirman.com/home", wait_until="networkidle")
        await asyncio.sleep(2)

        cat_btn = await page.wait_for_selector("text=Catalog")
        if cat_btn:
            await cat_btn.click()
            await asyncio.sleep(3)

        if "authorization" not in captured_headers:
            print("[ERROR] Authorization token capture failed.")
            return

        headers = dict(captured_headers)
        headers["x-language"] = "en"
        headers["Accept-Language"] = "en-US,en;q=0.9"

        print(f"[SUCCESS] Authorization Token: {headers['authorization'][:35]}...")
        print(f"[SUCCESS] Language set to: {headers.get('x-language')}")

        print(f"\n[STEP 2] Downloading English CloudFront diagram blueprints...")
        print("=" * 65)

        success_count = 0

        for idx, (pdf_name, model) in enumerate(pdf_items, 1):
            out_file = IMG_DIR / f"{pdf_name}.png"
            safe_model = model.encode('ascii', errors='ignore').decode('ascii').strip() or "Model"

            print(f"[{idx}/{len(pdf_items)}] {pdf_name} ({safe_model})...", end=" ")

            base_key = pdf_name.replace(".pdf", ".png").lower()
            api_url = f"https://api-service.sirman.com/service-dwh/resources/exploded-view/jpeg/{base_key}?quality=full"

            try:
                resp = await ctx.request.get(api_url, headers=headers)
                if resp.status == 200:
                    data = await resp.json()
                    signed_url = data.get("url")

                    if signed_url:
                        img_resp = await ctx.request.get(signed_url)
                        if img_resp.status == 200:
                            img_bytes = await img_resp.body()
                            if len(img_bytes) > 20000:
                                with open(out_file, "wb") as f:
                                    f.write(img_bytes)
                                print(f"SUCCESS EN ({len(img_bytes)/1024:.1f} KB)")
                                success_count += 1
                                continue

                print(f"Not found (Status {resp.status})")
            except Exception as err:
                print(f"Error: {err}")

            time.sleep(0.04)

        await browser.close()

    print("\n" + "=" * 65)
    print(f"  ENGLISH BLUEPRINT DOWNLOAD COMPLETED!")
    print(f"  Saved authentic EN blueprints: {success_count}/{len(pdf_items)}")
    print(f"  Image folder: {IMG_DIR}")
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(main())
