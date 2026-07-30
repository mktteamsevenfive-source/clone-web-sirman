"""
SIRMAN FULLY AUTOMATED LOGIN & DIRECT PDF DOWNLOADER v2
=========================================================
1. Unicode safe terminal output (UTF-8)
2. Accurate JWT Bearer Token interception ('Bearer eyJ...')
3. Direct download of PDF diagrams from Sirman API
4. Conversion into 150 DPI PNG images
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from playwright.async_api import async_playwright

# Force UTF-8 for Windows console
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

captured_auth = {}


async def on_request(request):
    """Intercept request headers to capture JWT Bearer Token"""
    url = request.url
    headers = dict(request.headers)
    for k, v in headers.items():
        if k.lower() == "authorization" and v.startswith("Bearer eyJ"):
            captured_auth["token"] = v
            print(f"  [JWT TOKEN CAPTURED] {v[:35]}...")
            break


async def main():
    username = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_USER
    password = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_PASS

    print("=" * 65)
    print("  SIRMAN DIRECT PDF DOWNLOADER v2")
    print("=" * 65)

    if not DATA_FILE.exists():
        print(f"[ERROR] {DATA_FILE} not found. Run build_data.py first.")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        catalog_data = json.load(f)

    products = catalog_data.get("products", [])
    
    # Get unique list of PDFs
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
    print(f"[INFO] Using credentials for: {username}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=100, args=["--start-maximized"])
        ctx = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await ctx.new_page()

        page.on("request", on_request)

        # STEP 1: Navigate & Auto Login
        print("\n[STEP 1] Opening Sirman login page...")
        await page.goto("https://www.service.sirman.com/login", wait_until="domcontentloaded")
        await asyncio.sleep(1.5)

        # Click red LOGIN button
        login_btn = await page.query_selector("button:has-text('LOGIN'), a:has-text('LOGIN'), .login-btn")
        if login_btn:
            print("[INFO] Clicking LOGIN button to open Cognito auth portal...")
            await login_btn.click()
            await asyncio.sleep(2.5)

        # Wait for Cognito login form fields
        print(f"[INFO] Entering credentials into login form...")
        try:
            user_el = await page.wait_for_selector("#inputEmail, input[type='email'], input[name='email']", timeout=10000)
            pass_el = await page.wait_for_selector("#inputPassword, input[type='password'], input[name='password']", timeout=10000)

            if user_el and pass_el:
                await user_el.fill(username)
                await pass_el.fill(password)
                await asyncio.sleep(0.5)

                print("[INFO] Submitting credentials...")
                submit_el = await page.query_selector("button[type='submit'], input[type='submit'], button:has-text('Sign in'), button:has-text('Log in')")
                if submit_el:
                    await submit_el.click()
                else:
                    await pass_el.press("Enter")

                print("[INFO] Waiting for login redirect to catalog...")
                await page.wait_for_timeout(6000)
        except Exception as login_err:
            print(f"[WARN] Automatic form filling notice: {login_err}")

        # Trigger an API call by clicking or navigating catalog to capture JWT token
        if "token" not in captured_auth:
            print("[INFO] Triggering catalog API call to capture token...")
            try:
                await page.goto("https://service.sirman.com/catalog", wait_until="networkidle")
                await page.click("text=Slicers")
                await asyncio.sleep(3)
            except Exception:
                pass

        # Extract JWT token from storage if not captured in network
        if "token" not in captured_auth:
            token = await page.evaluate("""() => {
                for (let i = 0; i < localStorage.length; i++) {
                    const k = localStorage.key(i);
                    const v = localStorage.getItem(k);
                    if (v && v.startsWith('eyJ')) {
                        return 'Bearer ' + v;
                    }
                }
                for (let i = 0; i < sessionStorage.length; i++) {
                    const k = sessionStorage.key(i);
                    const v = sessionStorage.getItem(k);
                    if (v && v.startsWith('eyJ')) {
                        return 'Bearer ' + v;
                    }
                }
                return '';
            }""")
            if token:
                captured_auth["token"] = token

        auth_token = captured_auth.get("token")
        if auth_token:
            print(f"[SUCCESS] JWT Token captured: {auth_token[:40]}...")
        else:
            print("[WARN] Token not captured, attempting requests with session cookies...")

        headers = {}
        if auth_token:
            headers["Authorization"] = auth_token

        # STEP 2: Download PDF diagrams from API
        print(f"\n[STEP 2] Downloading {len(pdf_list)} PDF files directly from Sirman API...")

        downloaded_count = 0
        converted_count = 0

        for idx, item in enumerate(pdf_list, 1):
            pdf_name = item["pdfName"]
            model_name = item["model"]
            p_id = item["productId"]
            v_id = item["explodedViewId"]

            pdf_path = PDF_DIR / pdf_name
            img_path = IMG_DIR / f"{pdf_name}.png"

            # Clean name for safe printing
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
                    resp = await ctx.request.get(u, headers=headers)
                    if resp.status == 200:
                        body = await resp.body()
                        if body.startswith(b"%PDF") or (len(body) > 5000 and not body.startswith(b"<!doctype")):
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
