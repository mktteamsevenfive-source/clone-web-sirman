"""
authenticated_full_scraper.py
===============================
1. Automates Keycloak login to Sirman Service Portal using Playwright
2. Captures authenticated API bearer token and session headers
3. Queries all ~1,638 missing products from Supabase
4. Concurrently fetches exploded views and spare parts via Sirman DWH API (10 workers)
5. Stream-uploads all recovered spare parts & updates product status live on Supabase
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
    print("=" * 65)
    print("  [1] LAUNCHING PLAYWRIGHT TO CAPTURE AUTHENTICATED SESSION")
    print("=" * 65)
    
    captured_hdrs = {}
    captured_cookies = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await ctx.new_page()

        async def on_request(req):
            if "api-service.sirman.com" in req.url:
                hdrs = dict(req.headers)
                if "authorization" in hdrs or "x-customer-code" in hdrs:
                    captured_hdrs.update({k: v for k, v in hdrs.items() if not k.startswith(":")})

        page.on("request", on_request)

        print("  Navigating to Sirman login...")
        await page.goto("https://service.sirman.com/login", wait_until="networkidle")
        await asyncio.sleep(2)

        # Login flow
        user_field = await page.query_selector("#username, input[type='email'], input[name='username']")
        pass_field = await page.query_selector("#password, input[type='password']")

        if user_field and pass_field:
            print(f"  Filling login credentials for {USERNAME}...")
            await user_field.fill(USERNAME)
            await pass_field.fill(PASSWORD)
            submit_btn = await page.query_selector("#kc-login, button[type='submit']")
            if submit_btn:
                await submit_btn.click()
                await asyncio.sleep(5)

        # Navigate to product page to trigger authenticated API call
        await page.goto("https://www.service.sirman.com/products/4578/tavola/19666", wait_until="networkidle")
        await asyncio.sleep(3)

        captured_cookies = await ctx.cookies()
        await browser.close()

    if captured_hdrs:
        with open(HEADERS_FILE, "w", encoding="utf-8") as f:
            json.dump({"headers": captured_hdrs, "cookies": captured_cookies}, f, indent=2)
        print("  [SUCCESS] Auth headers captured!")
        return captured_hdrs, captured_cookies
    else:
        print("  [WARN] Using existing sirman_headers.json if available...")
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
        return pid, [], 0, f"View error: {e}"

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
    
    clean_headers = {k: v for k, v in headers.items() if not k.startswith(":")}
    cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
    if cookie_str:
        clean_headers["cookie"] = cookie_str

    print("\n=" * 65)
    print("  [2] QUERYING MISSING PRODUCTS FROM SUPABASE")
    print("=" * 65)
    
    # 1. Fetch all products
    all_prods = []
    for page in range(0, 5):
        r = requests.get(
            f"{SUPABASE_URL}/rest/v1/products?select=id,code,model,parts_count",
            headers={**SUP_HEADERS, "Range": f"{page*1000}-{(page+1)*1000-1}"},
            timeout=15
        ).json()
        if not r:
            break
        all_prods.extend(r)

    # 2. Fetch existing product_ids in parts table
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

    missing_prods = [p for p in all_prods if p['id'] not in pids_with_parts]
    print(f"Total missing products to scrape: {len(missing_prods):,} / {len(all_prods):,}")

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
        futures = {executor.submit(fetch_product_parts_worker, p, clean_headers): p for p in missing_prods}

        for future in as_completed(futures):
            p = futures[future]
            try:
                pid, parts, count, main_pdf, main_view_id = future.result()
                scraped_count += 1
                
                if parts:
                    total_parts_recovered += len(parts)
                    parts_buffer.extend(parts)
                    prod_updates_buffer.append({
                        "id": pid,
                        "parts_count": len(parts),
                        "pdf_name": main_pdf or "",
                        "exploded_view_id": main_view_id or None
                    })
                    print(f"  [{scraped_count}/{len(missing_prods)}] Product {pid} ('{p['model'][:35]}') -> RECOVERED {len(parts)} parts!")
                else:
                    print(f"  [{scraped_count}/{len(missing_prods)}] Product {pid} ('{p['model'][:35]}') -> 0 parts on Sirman")

                # Flush to Supabase every 500 parts or 100 products
                if len(parts_buffer) >= 500 or len(prod_updates_buffer) >= 50:
                    print(f"\n  ---> [SUPABASE FLUSH] Stream-uploading {len(parts_buffer)} parts & {len(prod_updates_buffer)} product updates...")
                    # Upload parts
                    requests.post(f"{SUPABASE_URL}/rest/v1/parts", headers=SUP_HEADERS, json=parts_buffer, timeout=45)
                    # Update products
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
