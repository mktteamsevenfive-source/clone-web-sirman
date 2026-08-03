"""
authenticated_full_scraper_fixed.py
=====================================
1. Captures or uses authenticated Bearer token from Sirman login
2. Queries all missing products in Supabase
3. Scrapes missing exploded views and parts (8 workers)
4. Stream-uploads all recovered parts & updates to Supabase
"""

import sys, json, time, asyncio, requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
HEADERS_FILE = PROJECT_ROOT / "sirman_headers.json"
USERNAME     = "korralak.sa@sevenfive.co.th"
PASSWORD     = "Service@1234"
API_BASE     = "https://api-service.sirman.com"

SUPABASE_URL     = "https://ofrerwyoasklgsejlbzr.supabase.co"
SUPABASE_SERVICE = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9mcmVyd3lvYXNrbGdzZWpsYnpyIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NTM2NjY1NSwiZXhwIjoyMTAwOTQyNjU1fQ.shN-wvqCOZi1GtPO3rwCHF51OQ0hf23E_GVn9bt3bHQ"
SUP_HEADERS = {
    "apikey": SUPABASE_SERVICE,
    "Authorization": f"Bearer {SUPABASE_SERVICE}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates"
}

async def capture_sirman_auth():
    # If valid headers file exists, try testing it first
    if HEADERS_FILE.exists():
        try:
            data = json.load(open(HEADERS_FILE, encoding="utf-8"))
            hdrs = data.get("headers", {})
            test_r = requests.get(f"{API_BASE}/service-dwh/products/4578/exploded-views", headers=hdrs, timeout=8)
            if test_r.status_code == 200:
                print("  [OK] Saved Bearer Token is ACTIVE!")
                return hdrs, data.get("cookies", [])
        except Exception:
            pass

    print("=" * 65)
    print("  [1] LAUNCHING PLAYWRIGHT TO CAPTURE AUTHENTICATED SESSION")
    print("=" * 65)
    
    captured_bearer = ""
    captured_cookies = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await ctx.new_page()

        async def on_request(req):
            nonlocal captured_bearer
            auth = req.headers.get("authorization", "")
            if auth and auth.startswith("Bearer ") and ("exploded-views" in req.url or "products" in req.url):
                captured_bearer = auth
                print(f"  [BEARER TOKEN CAPTURED!] from {req.url[:70]}")

        page.on("request", on_request)

        print("  Navigating to Sirman portal...")
        await page.goto("https://service.sirman.com/catalog", wait_until="domcontentloaded")
        await asyncio.sleep(2)

        login_btn = await page.query_selector("button:has-text('LOGIN'), button:has-text('Log into Sirman Service'), a:has-text('LOGIN')")
        if login_btn and await login_btn.is_visible():
            print("  Clicking LOGIN button...")
            await login_btn.click()
            await asyncio.sleep(3)

        email_in = await page.query_selector("#inputEmail, input[type='email'], input[name='email']")
        pass_in  = await page.query_selector("#inputPassword, input[type='password'], input[name='password']")

        if email_in and pass_in:
            print(f"  Filling login credentials for {USERNAME}...")
            await email_in.fill(USERNAME)
            await pass_in.fill(PASSWORD)
            submit_btn = await page.query_selector("button[type='submit'], input[type='submit']")
            if submit_btn:
                print("  Submitting login form...")
                await submit_btn.click()
                await asyncio.sleep(4)

        try:
            consent_btn = await page.query_selector("button:has-text('Authorize'), button:has-text('Allow'), button[type='submit']")
            if consent_btn and await consent_btn.is_visible():
                print("  Clicking OAuth Authorize button...")
                await consent_btn.click()
                await asyncio.sleep(4)
        except Exception:
            pass

        print("  Navigating to Product 4578 page...")
        try:
            await page.goto("https://www.service.sirman.com/products/4578/tavola/19666", wait_until="domcontentloaded", timeout=15000)
            await asyncio.sleep(3)
        except Exception:
            pass

        captured_cookies = await ctx.cookies()
        await browser.close()

    if captured_bearer:
        hdrs = {
            "authorization": captured_bearer,
            "x-company": "srm",
            "x-language": "en",
            "referer": "https://www.service.sirman.com/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        }
        with open(HEADERS_FILE, "w", encoding="utf-8") as f:
            json.dump({"headers": hdrs, "cookies": captured_cookies}, f, indent=2)
        print("  [SUCCESS] Valid Bearer Token saved!")
        return hdrs, captured_cookies

    if HEADERS_FILE.exists():
        data = json.load(open(HEADERS_FILE, encoding="utf-8"))
        return data.get("headers", {}), data.get("cookies", [])

    return {}, []

def fetch_product_parts_worker(product, session_headers):
    pid = product['id']
    session = requests.Session()
    session.headers.update(session_headers)
    
    views = []
    try:
        r = session.get(f"{API_BASE}/service-dwh/products/{pid}/exploded-views", timeout=12)
        if r.status_code == 200:
            views = r.json() or []
    except Exception as e:
        return pid, [], 0, "", f"View error: {e}"

    parts = []
    main_pdf = ""
    main_view_id = ""

    for v in views:
        if not isinstance(v, dict):
            continue
        v_id = v.get("id")
        v_name = v.get("name", "")
        if not main_view_id and v_id:
            main_view_id = str(v_id)
        v_pdf = v.get("pdfName") or v.get("code") or v.get("fileName")
        if v_pdf and not main_pdf:
            main_pdf = str(v_pdf)

        if not v_id:
            continue

        try:
            pr = session.get(f"{API_BASE}/service-dwh/products/{pid}/exploded-views/{v_id}/parts", timeout=12)
            if pr.status_code == 200:
                pts = pr.json() or []
                for pt in pts:
                    if isinstance(pt, dict):
                        pt_code = pt.get("code") or pt.get("partCode") or f"P-{pt.get('id','')}"
                        pt_i18n = pt.get("i18n") or {}
                        pt_name = pt_i18n.get("en") or pt.get("description") or pt.get("name") or "Part"
                        parts.append({
                            "product_id": pid,
                            "code": str(pt_code),
                            "name": str(pt_name),
                            "price": float(pt.get("price") or 0.0),
                            "stock": int(pt.get("availability") or 0),
                            "ref": str(pt.get("position") or pt.get("ref") or ""),
                            "view_name": str(v_name)
                        })
        except Exception:
            pass

    return pid, parts, len(parts), main_pdf, main_view_id

def main():
    headers, cookies = asyncio.run(capture_sirman_auth())
    
    if not headers:
        print("[ERROR] Could not obtain Bearer Token from Sirman login.")
        return

    print("\n=" * 65)
    print("  [2] QUERYING MISSING PRODUCTS FROM SUPABASE")
    print("=" * 65)
    
    # Fetch all products
    all_prods = []
    for page in range(0, 5):
        r = requests.get(
            f"{SUPABASE_URL}/rest/v1/products?select=id,code,model,pdf_name,parts_count",
            headers={**SUP_HEADERS, "Range": f"{page*1000}-{(page+1)*1000-1}"},
            timeout=15
        ).json()
        if not r:
            break
        all_prods.extend(r)

    # Fetch existing product_ids in parts table
    pids_with_parts = set()
    for page in range(0, 450):
        r = requests.get(
            f"{SUPABASE_URL}/rest/v1/parts?select=product_id",
            headers={**SUP_HEADERS, "Range": f"{page*1000}-{(page+1)*1000-1}"},
            timeout=15
        ).json()
        if not r or not isinstance(r, list):
            break
        for row in r:
            if row.get('product_id'):
                pids_with_parts.add(row['product_id'])
        if len(r) < 1000:
            break

    # Query products missing pdf_name OR missing parts
    missing_prods = []
    for p in all_prods:
        if not p.get('pdf_name') or p['id'] not in pids_with_parts:
            missing_prods.append(p)
    print(f"Total missing products (missing diagram or parts): {len(missing_prods):,} / {len(all_prods):,}")

    if not missing_prods:
        print("🎉 ALL PRODUCTS ALREADY HAVE PARTS IN SUPABASE (100% COMPLETE)!")
        return

    print("\n=" * 65)
    print(f"  [3] SCRAPING & STREAMING PARTS TO SUPABASE ({len(missing_prods)} PRODUCTS)")
    print("=" * 65)

    start_time = time.time()
    total_parts_recovered = 0
    scraped_count = 0

    parts_buffer = []
    prod_updates_buffer = []

    WORKERS = 8
    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = {executor.submit(fetch_product_parts_worker, p, headers): p for p in missing_prods}

        for future in as_completed(futures):
            p = futures[future]
            try:
                pid, parts, count, main_pdf, main_view_id = future.result()
                scraped_count += 1
                
                if main_pdf or main_view_id or parts:
                    if parts:
                        total_parts_recovered += len(parts)
                        parts_buffer.extend(parts)
                    prod_updates_buffer.append({
                        "id": pid,
                        "parts_count": len(parts),
                        "pdf_name": main_pdf or "",
                        "exploded_view_id": main_view_id or None
                    })
                    print(f"  [{scraped_count}/{len(missing_prods)}] Product {pid} ('{p['model'][:35]}') -> PDF: '{main_pdf}', Parts: {len(parts)}")
                else:
                    print(f"  [{scraped_count}/{len(missing_prods)}] Product {pid} ('{p['model'][:35]}') -> No view on Sirman")

                if len(parts_buffer) >= 500 or len(prod_updates_buffer) >= 50:
                    print(f"\n  ---> [SUPABASE FLUSH] Stream-uploading {len(parts_buffer)} parts & {len(prod_updates_buffer)} product updates...")
                    if parts_buffer:
                        requests.post(f"{SUPABASE_URL}/rest/v1/parts", headers=SUP_HEADERS, json=parts_buffer, timeout=45)
                    for pu in prod_updates_buffer:
                        requests.patch(f"{SUPABASE_URL}/rest/v1/products?id=eq.{pu['id']}", headers=SUP_HEADERS, json=pu, timeout=15)
                    parts_buffer.clear()
                    prod_updates_buffer.clear()

            except Exception as exc:
                print(f"  [ERROR] Product {p['id']} generated exception: {exc}")

    # Final flush
    if parts_buffer or prod_updates_buffer:
        print(f"\n  ---> [FINAL FLUSH] Stream-uploading remaining {len(parts_buffer)} parts & {len(prod_updates_buffer)} product updates...")
        if parts_buffer:
            requests.post(f"{SUPABASE_URL}/rest/v1/parts", headers=SUP_HEADERS, json=parts_buffer, timeout=45)
        for pu in prod_updates_buffer:
            requests.patch(f"{SUPABASE_URL}/rest/v1/products?id=eq.{pu['id']}", headers=SUP_HEADERS, json=pu, timeout=15)

    elapsed = time.time() - start_time
    print("\n" + "=" * 65)
    print(f"🎉 SCRAPING COMPLETE IN {elapsed:.1f}s!")
    print(f"   Total Recovered Parts: {total_parts_recovered:,} items")
    print("=" * 65)

if __name__ == "__main__":
    main()
