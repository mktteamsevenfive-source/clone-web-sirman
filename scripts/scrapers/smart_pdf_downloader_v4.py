"""
SIRMAN AUTOMATED PDF DOWNLOADER v4 (Full Auth Headers & DWH API)
================================================================
1. Automated OAuth login & Authorize consent button click
2. Captures full JWT Token, x-company, x-customer-code, x-user-device headers
3. Downloads all 150 PDF diagram files directly from Sirman API
4. Converts all PDFs into crisp 150 DPI PNG images in diagram_images/
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

try:
    import fitz  # PyMuPDF
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "pymupdf"], check=True)
    import fitz

BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / "sirman_catalog_data.json"
PDF_DIR = BASE_DIR / "pdf_diagrams"
IMG_DIR = BASE_DIR / "diagram_images"

PDF_DIR.mkdir(exist_ok=True)
IMG_DIR.mkdir(exist_ok=True)

DEFAULT_USER = "korralak.sa@sevenfive.co.th"
DEFAULT_PASS = "Service@1234"

captured_headers = {}


async def on_request(request):
    """Capture exact DWH API headers"""
    u = request.url
    if "service-dwh" in u:
        hdrs = dict(request.headers)
        if "authorization" in hdrs:
            captured_headers.update(hdrs)


async def main():
    username = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_USER
    password = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_PASS

    print("=" * 65)
    print("  SIRMAN FULLY AUTOMATED DIAGRAM DOWNLOADER v4")
    print("=" * 65)

    if not DATA_FILE.exists():
        print(f"[ERROR] {DATA_FILE} not found.")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        catalog_data = json.load(f)

    products = catalog_data.get("products", [])
    
    pdf_list = []
    seen = set()
    for p in products:
        pdf_name = p.get("pdfName", "").strip()
        if pdf_name and pdf_name not in seen:
            seen.add(pdf_name)
            pdf_list.append({
                "pdfName": pdf_name,
                "model": p.get("model", "Unknown"),
                "productId": p.get("id"),
                "explodedViewId": p.get("explodedViewId")
            })

    print(f"[INFO] Loaded {len(products)} products -> {len(pdf_list)} unique PDF diagrams.")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=100, args=["--start-maximized"])
        ctx = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await ctx.new_page()

        page.on("request", on_request)

        print("\n[STEP 1] Logging in to Sirman Service...")
        await page.goto("https://www.service.sirman.com/login", wait_until="networkidle")

        login_btn = await page.wait_for_selector("button:has-text('LOGIN'), .login-btn")
        if login_btn:
            await login_btn.click()
            await asyncio.sleep(2)

        user_el = await page.wait_for_selector("#inputEmail, input[type='email']")
        pass_el = await page.wait_for_selector("#inputPassword, input[type='password']")

        await user_el.fill(username)
        await pass_el.fill(password)
        await page.click("button[type='submit'], input[type='submit']")
        await asyncio.sleep(3)

        auth_btn = await page.query_selector("button:has-text('Authorize')")
        if auth_btn:
            await auth_btn.click()
            await asyncio.sleep(4)

        # Go to catalog page to trigger API requests and capture exact headers
        await page.goto("https://www.service.sirman.com/catalog", wait_until="domcontentloaded")
        await asyncio.sleep(4)

        # Extract authorization token
        jwt_token = captured_headers.get("authorization", "")
        customer_code = captured_headers.get("x-customer-code", "1000052367")
        if customer_code == "0":
            customer_code = "1000052367"

        company = captured_headers.get("x-company", "srm")
        device = captured_headers.get("x-user-device", "8cbad93e01071a4715853df30f1dc009")

        print(f"[INFO] Captured Auth Token: {jwt_token[:35]}...")
        print(f"[INFO] Company: {company} | Customer Code: {customer_code}")

        api_headers = {
            "Authorization": jwt_token,
            "x-company": company,
            "x-customer-code": customer_code,
            "x-user-device": device,
            "x-language": "en",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        # STEP 2: Download PDF diagrams directly from API
        print(f"\n[STEP 2] Direct-downloading {len(pdf_list)} PDF files from Sirman API...")

        downloaded_count = 0
        converted_count = 0

        for idx, item in enumerate(pdf_list, 1):
            pdf_name = item["pdfName"]
            model_name = item["model"]
            p_id = item["productId"]
            v_id = item["explodedViewId"]

            pdf_path = PDF_DIR / pdf_name
            img_path = IMG_DIR / f"{pdf_name}.png"

            safe_model = model_name.encode('ascii', errors='ignore').decode('ascii').strip() or "Model"

            print(f"[{idx}/{len(pdf_list)}] {pdf_name} ({safe_model})...", end=" ")

            # Skip if already downloaded and valid PDF
            if pdf_path.exists() and pdf_path.stat().st_size > 5000:
                with open(pdf_path, "rb") as check_f:
                    if check_f.read(4) == b"%PDF":
                        downloaded_count += 1
                        print("Already downloaded", end=" | ")
                        if not img_path.exists() or img_path.stat().st_size < 3000:
                            try:
                                doc = fitz.open(pdf_path)
                                if len(doc) > 0:
                                    doc[0].get_pixmap(dpi=150).save(img_path)
                                    converted_count += 1
                                    print("Converted PNG")
                                else:
                                    print("Empty PDF")
                            except Exception as e:
                                print(f"PNG err: {e}")
                        else:
                            print("PNG ready")
                        continue

            urls_to_try = [
                f"https://api-service.sirman.com/service-dwh/files/{pdf_name}",
                f"https://api-service.sirman.com/service-dwh/products/{p_id}/exploded-views/{v_id}/file" if p_id and v_id else None,
                f"https://service.sirman.com/pdf/{pdf_name}"
            ]
            urls_to_try = [u for u in urls_to_try if u]

            success = False
            for u in urls_to_try:
                try:
                    resp = await ctx.request.get(u, headers=api_headers)
                    if resp.status == 200:
                        body = await resp.body()
                        if body.startswith(b"%PDF") or (len(body) > 3000 and not body.startswith(b"<!doctype")):
                            with open(pdf_path, "wb") as pf:
                                pf.write(body)
                            success = True
                            downloaded_count += 1
                            print(f"Downloaded ({len(body)/1024:.1f} KB)", end=" | ")
                            
                            # Render PNG image
                            try:
                                doc = fitz.open(pdf_path)
                                if len(doc) > 0:
                                    doc[0].get_pixmap(dpi=150).save(img_path)
                                    converted_count += 1
                                    print("Converted PNG")
                            except Exception as render_err:
                                print(f"Render err: {render_err}")
                            break
                except Exception:
                    pass

            if not success:
                print("Failed (403/404)")

            time.sleep(0.08)

        await browser.close()

    print("\n" + "=" * 65)
    print("  DOWNLOAD & CONVERSION COMPLETED SUCCESSFULLY!")
    print(f"  PDFs downloaded: {downloaded_count}/{len(pdf_list)}")
    print(f"  PNGs rendered:    {converted_count}/{len(pdf_list)}")
    print(f"  PDF folder:       {PDF_DIR}")
    print(f"  PNG folder:       {IMG_DIR}")
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(main())
