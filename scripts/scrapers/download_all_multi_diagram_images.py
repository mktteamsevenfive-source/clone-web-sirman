"""
download_all_multi_diagram_images.py
======================================
1. Loads public/product_views.json containing all 4,049 products & diagram tables
2. Identifies all missing diagram table images in Supabase Storage
3. Logs into Sirman portal via Playwright
4. Navigates to tavola view pages and intercepts CloudFront JPEG image bytes
5. Uploads all diagram images to Supabase Storage 'diagram_images' bucket
"""
import asyncio
import json
import re
import sys
import time
import requests as req_lib
from pathlib import Path
from playwright.async_api import async_playwright

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
VIEWS_FILE = ROOT_DIR / "public" / "product_views.json"

SUPABASE_URL     = 'https://ofrerwyoasklgsejlbzr.supabase.co'
SUPABASE_SERVICE = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9mcmVyd3lvYXNrbGdzZWpsYnpyIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NTM2NjY1NSwiZXhwIjoyMTAwOTQyNjU1fQ.shN-wvqCOZi1GtPO3rwCHF51OQ0hf23E_GVn9bt3bHQ'
SUP_HEADERS = {'apikey': SUPABASE_SERVICE, 'Authorization': 'Bearer ' + SUPABASE_SERVICE}
USERNAME = 'korralak.sa@sevenfive.co.th'
PASSWORD = 'Service@1234'

def list_supabase_images() -> set:
    existing = set()
    offset = 0
    while True:
        url = f'{SUPABASE_URL}/storage/v1/object/list/diagram_images'
        r = req_lib.post(url, headers=SUP_HEADERS,
                         json={'limit': 1000, 'offset': offset, 'prefix': '',
                               'sortBy': {'column': 'name', 'order': 'asc'}}, timeout=15)
        if r.status_code != 200:
            break
        items = r.json()
        if not items:
            break
        for item in items:
            existing.add(item.get('name', '').lower())
        if len(items) < 1000:
            break
        offset += 1000
    return existing

def get_missing_diagram_tables(existing_images: set) -> list:
    if not VIEWS_FILE.exists():
        print(f"[ERROR] {VIEWS_FILE} not found!")
        return []

    views_data = json.load(open(VIEWS_FILE, encoding='utf-8'))
    missing = []

    for pid_str, views in views_data.items():
        for v in views:
            v_id = v.get("id")
            pdf = v.get("pdfName", "")
            if not v_id or not pdf:
                continue
            clean = re.sub(r'\.pdf$', '', pdf, flags=re.IGNORECASE).strip()
            clean_safe = clean.replace(' ', '_')
            clean_lower = clean.lower()

            variants = [
                f"{pdf.lower()}.png",
                f"{clean_lower}.png",
                f"{clean_lower}.pdf.png",
                f"{clean_safe.lower()}.png",
                f"{v_id}.png"
            ]

            if not any(var in existing_images for var in variants):
                missing.append({
                    "product_id": pid_str,
                    "view_id": v_id,
                    "pdf_name": pdf,
                    "clean": clean,
                    "clean_safe": clean_safe,
                    "name": v.get("name", "")
                })

    return missing

sup_session = req_lib.Session()
adapter = req_lib.adapters.HTTPAdapter(max_retries=3)
sup_session.mount("https://", adapter)

def upload_to_supabase(filename: str, data: bytes) -> bool:
    url = f'{SUPABASE_URL}/storage/v1/object/diagram_images/{filename}'
    try:
        r = sup_session.post(url,
                             headers={**SUP_HEADERS, 'Content-Type': 'image/png', 'x-upsert': 'true'},
                             data=data, timeout=15)
        return r.status_code in (200, 201)
    except Exception as e:
        print(f"  [UPLOAD RETRY WARN] {filename}: {e}")
        return False

async def main():
    print("=" * 65)
    print("  SCRAPING ALL MISSING MULTI-DIAGRAM TABLE IMAGES")
    print("=" * 65)

    print("Checking Supabase Storage for existing diagram images...")
    existing = list_supabase_images()
    print(f"  Found {len(existing)} images already on Supabase Storage")

    missing = get_missing_diagram_tables(existing)
    print(f"  Total missing diagram table images to download: {len(missing)}")

    if not missing:
        print("All diagram table images are already completely uploaded! ✅")
        return

    ok = 0
    fail = 0
    total = len(missing)
    start = time.time()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={'width': 1440, 'height': 900})

        # ── Login ────────────────────────────────────────────────────────────
        print('\nLogging in to Sirman portal...')
        page = await ctx.new_page()
        await page.goto('https://service.sirman.com/catalog', wait_until='domcontentloaded', timeout=30000)
        await asyncio.sleep(2)
        try:
            login_btn = await page.query_selector("button:has-text('LOGIN'), a:has-text('LOGIN')")
            if login_btn and await login_btn.is_visible():
                await page.click("button:has-text('LOGIN'), a:has-text('LOGIN')")
                await asyncio.sleep(3)
        except Exception:
            pass
        email_in = await page.query_selector("#inputEmail, input[type='email']")
        pass_in  = await page.query_selector("#inputPassword, input[type='password']")
        if email_in and pass_in:
            await email_in.fill(USERNAME)
            await pass_in.fill(PASSWORD)
            try:
                await page.click("button[type='submit']")
                await asyncio.sleep(5)
            except Exception:
                pass
        try:
            consent = await page.query_selector("button:has-text('Authorize')")
            if consent and await consent.is_visible():
                await page.click("button:has-text('Authorize')")
                await asyncio.sleep(5)
        except Exception:
            pass
        print(f'  Logged in! Current URL: {page.url}')
        await page.close()

        # ── Download Loop ─────────────────────────────────────────────────────
        print(f'\nDownloading & Uploading {total} missing diagram images...')
        print('=' * 75)

        for i, item in enumerate(missing, 1):
            prod_id = item['product_id']
            view_id = item['view_id']
            pdf = item['pdf_name']
            clean = item['clean']
            clean_safe = item['clean_safe']

            tavola_url = f'https://www.service.sirman.com/products/{prod_id}/tavola/{view_id}'

            captured_bytes = []
            page = await ctx.new_page()

            async def on_response(response, _cap=captured_bytes):
                if _cap:
                    return
                url = response.url
                if 'service-media-prod.service247.net' in url and response.status == 200:
                    try:
                        body = await response.body()
                        if len(body) > 5000:
                            _cap.append(body)
                    except Exception:
                        pass

            page.on('response', on_response)

            try:
                await page.goto(tavola_url, wait_until='domcontentloaded', timeout=20000)
                deadline = time.time() + 15
                while not captured_bytes and time.time() < deadline:
                    await asyncio.sleep(0.3)
            except Exception:
                pass

            await page.close()

            img_data = captured_bytes[0] if captured_bytes else None

            if img_data:
                filenames = [
                    f"{pdf}.png",
                    f"{clean}.png",
                    f"{clean_safe}.png",
                    f"{clean.lower()}.png",
                    f"{clean_safe.lower()}.png",
                    f"{view_id}.png"
                ]
                uploaded = False
                for fn in set(filenames):
                    if upload_to_supabase(fn, img_data):
                        uploaded = True
                if uploaded:
                    ok += 1
                    rate = ok / max(time.time() - start, 1)
                    print(f'  [{i}/{total}] OK   Prod={prod_id} View={view_id} | {pdf} ({rate:.2f}/s)')
                else:
                    fail += 1
                    print(f'  [{i}/{total}] UPLOAD FAIL  Prod={prod_id} View={view_id}')
            else:
                fail += 1
                if i <= 20 or i % 50 == 0:
                    print(f'  [{i}/{total}] NO IMG  Prod={prod_id} View={view_id} | {pdf}')

        await browser.close()

    elapsed = time.time() - start
    print('\n' + '=' * 75)
    print(f'  [DONE] Completed in {elapsed:.1f}s')
    print(f'  Successfully Uploaded: {ok}')
    print(f'  Failed / Not Found:    {fail}')
    print('=' * 75)

if __name__ == "__main__":
    asyncio.run(main())
