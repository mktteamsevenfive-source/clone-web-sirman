"""
SIRMAN DIAGRAM DOWNLOADER & CONVERTER (Playwright Authenticated Session)
========================================================================
1. Opens Chromium browser to service.sirman.com
2. Waits for user login to capture authorization token & session context
3. Uses Playwright's authenticated API context (ctx.request) to download all 150 PDF diagrams
4. Converts downloaded PDFs into high-resolution PNG images using PyMuPDF (fitz)
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    print("[INFO] Installing pymupdf...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "pymupdf"], check=True)
    import fitz

try:
    from playwright.async_api import async_playwright, Request
except ImportError:
    print("[ERROR] Playwright not installed. Run: pip install playwright")
    sys.exit(1)

BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / "sirman_catalog_data.json"
PDF_DIR = BASE_DIR / "pdf_diagrams"
IMG_DIR = BASE_DIR / "diagram_images"

PDF_DIR.mkdir(exist_ok=True)
IMG_DIR.mkdir(exist_ok=True)

captured_headers = {}


async def on_request(request: Request):
    url = request.url
    if "api-service.sirman.com" in url:
        headers = dict(request.headers)
        if "authorization" in [k.lower() for k in headers.keys()]:
            captured_headers["auth"] = headers.get("authorization") or headers.get("Authorization")
            captured_headers[url] = headers


async def main():
    print("=" * 65)
    print("  SIRMAN AUTHENTICATED PDF DIAGRAM DOWNLOADER & CONVERTER")
    print("=" * 65)

    if not DATA_FILE.exists():
        print(f"[ERROR] {DATA_FILE} not found. Please run build_data.py first.")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        catalog_data = json.load(f)

    products = catalog_data.get("products", [])
    print(f"[INFO] Loaded {len(products)} products from catalog data.")

    # Unique PDF files & exploded view IDs map
    pdf_map = {}
    for p in products:
        pdf_name = p.get("pdfName", "").strip()
        exploded_id = p.get("explodedViewId")
        if pdf_name and pdf_name not in pdf_map:
            pdf_map[pdf_name] = {
                "model": p.get("model", "Unknown"),
                "explodedViewId": exploded_id,
                "productId": p.get("id")
            }

    print(f"[INFO] Found {len(pdf_map)} unique PDF diagrams to download.")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=50,
            args=["--start-maximized"]
        )
        ctx = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await ctx.new_page()

        page.on("request", on_request)

        print("\n[STEP 1] Opening service.sirman.com/catalog...")
        await page.goto("https://service.sirman.com/catalog", wait_until="domcontentloaded")

        print("\n" + "*" * 65)
        print("  PLEASE LOG IN TO SIRMAN SERVICE IN THE BROWSER WINDOW.")
        print("  AFTER LOGIN IS COMPLETE AND YOU SEE THE CATALOG, PRESS ENTER.")
        print("*" * 65 + "\n")

        input("  >> Press ENTER after logging in... ")

        # Check for Authorization token in localStorage
        token = await page.evaluate("""() => {
            for (let i = 0; i < localStorage.length; i++) {
                const k = localStorage.key(i);
                if (k.toLowerCase().includes('token') || k.toLowerCase().includes('auth')) {
                    return localStorage.getItem(k);
                }
            }
            return '';
        }""")

        auth_header = captured_headers.get("auth") or (f"Bearer {token}" if token else None)
        print(f"[INFO] Captured Auth Token: {auth_header[:35] + '...' if auth_header else 'None'}")

        req_headers = {}
        if auth_header:
            req_headers["Authorization"] = auth_header

        print(f"\n[STEP 2] Downloading {len(pdf_map)} PDF files using Playwright context...")

        downloaded_count = 0
        converted_count = 0

        for idx, (pdf_name, info) in enumerate(pdf_map.items(), 1):
            pdf_path = PDF_DIR / pdf_name
            img_path = IMG_DIR / f"{pdf_name}.png"
            model_name = info["model"]
            view_id = info["explodedViewId"]

            print(f"[{idx}/{len(pdf_map)}] {pdf_name} ({model_name})...", end=" ")

            # Test endpoints
            urls_to_try = [
                f"https://api-service.sirman.com/service-dwh/files/{pdf_name}",
                f"https://api-service.sirman.com/service-dwh/exploded-views/{view_id}/file" if view_id else None,
                f"https://service.sirman.com/pdf/{pdf_name}"
            ]
            urls_to_try = [u for u in urls_to_try if u]

            success = False
            for u in urls_to_try:
                try:
                    resp = await ctx.request.get(u, headers=req_headers)
                    if resp.status == 200:
                        body = await resp.body()
                        # Check if it is really a PDF (starts with %PDF or has size > 5KB)
                        if body.startswith(b"%PDF") or len(body) > 5000:
                            with open(pdf_path, "wb") as pf:
                                pf.write(body)
                            success = True
                            print(f"Downloaded ({len(body)/1024:.1f} KB)", end=" | ")
                            downloaded_count += 1
                            break
                except Exception:
                    pass

            if not success:
                print("Failed (403/404)", end=" | ")
            else:
                downloaded_count += 1

            # Convert PDF page 1 to PNG image using PyMuPDF
            if pdf_path.exists() and pdf_path.stat().st_size > 3000:
                try:
                    doc = fitz.open(pdf_path)
                    if len(doc) > 0:
                        pg = doc[0]
                        pix = pg.get_pixmap(dpi=150)
                        pix.save(img_path)
                        converted_count += 1
                        print("Converted to PNG")
                    else:
                        print("Empty PDF")
                except Exception as err:
                    print(f"PNG conversion error: {err}")
            else:
                print("Skipped PNG conversion")

            time.sleep(0.1)

        await browser.close()

    print("\n" + "=" * 65)
    print("  DOWNLOAD & CONVERSION COMPLETED")
    print(f"  PDFs downloaded: {downloaded_count}/{len(pdf_map)}")
    print(f"  PNGs rendered:    {converted_count}/{len(pdf_map)}")
    print(f"  PDF folder:       {PDF_DIR}")
    print(f"  PNG folder:       {IMG_DIR}")
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(main())
