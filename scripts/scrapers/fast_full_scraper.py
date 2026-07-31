"""
fast_full_scraper.py - Complete 1,282 Categories Sirman Scraper & Supabase Sync
================================================================================
1. Opens browser to capture fresh Auth Headers if session expired
2. Queries ALL 1,282 category IDs from Sirman API in parallel (20 workers)
3. Fetches products, exploded views, parts for any missing items
4. Saves data to sirman_catalog_data.json & sirman_parts.json
5. Automatically syncs to Supabase database
"""

import asyncio
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

try:
    import requests as req_lib
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "requests"], check=True)
    import requests as req_lib

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("Run: pip install playwright && playwright install chromium")
    sys.exit(1)

BASE_DIR     = Path(__file__).parent
OUTPUT_FILE  = BASE_DIR / "sirman_parts.json"
CATALOG_FILE = BASE_DIR / "sirman_catalog_data.json"
HEADERS_FILE = BASE_DIR / "sirman_headers.json"
API_BASE     = "https://api-service.sirman.com"


# ── Load or Capture Session ──────────────────────────────────────────────────
async def get_valid_session() -> req_lib.Session:
    """Check if saved session works, otherwise open browser to refresh."""
    if HEADERS_FILE.exists():
        try:
            data = json.load(open(HEADERS_FILE, encoding="utf-8"))
            hdrs = data.get("headers", {})
            cookies = data.get("cookies", [])
            if hdrs:
                session = req_lib.Session()
                clean = {k: v for k, v in hdrs.items() if not k.startswith(":")}
                session.headers.update(clean)
                cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
                if cookie_str:
                    session.headers["cookie"] = cookie_str

                # Test if token is still valid
                test = session.get(f"{API_BASE}/service-dwh/categories", timeout=8)
                if test.status_code == 200:
                    print("[AUTH] Reusing valid session from sirman_headers.json ✅")
                    return session
                else:
                    print(f"[AUTH] Saved session expired (HTTP {test.status_code}) -> refreshing via browser...")
        except Exception:
            pass

    # Open browser to capture fresh headers
    print("\n[AUTH] Opening Chromium browser for Sirman authentication...")
    captured_hdrs: dict = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=["--start-maximized"])
        ctx = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await ctx.new_page()

        async def on_request(req):
            url = req.url
            if "api-service.sirman.com/service-dwh/products" in url and "category=" in url:
                hdrs = dict(req.headers)
                if any(k.lower() in hdrs for k in ["authorization", "x-customer-code"]):
                    captured_hdrs.update({k: v for k, v in hdrs.items() if not k.startswith(":")})
                    print(f"  [AUTH] Captured headers from: {url[:80]}")

        page.on("request", on_request)
        await page.goto("https://service.sirman.com/catalog", wait_until="domcontentloaded")

        print("\n[WAIT] Please:")
        print("  1. LOGIN to Sirman in the browser")
        print("  2. CLICK any category (e.g. Meat Processors)")
        print("  3. Press Enter HERE after product grid appears ...")
        input("  >> ")

        try:
            await page.wait_for_load_state("networkidle", timeout=5000)
        except Exception:
            pass

        cookies = await ctx.cookies()
        await browser.close()

    if not captured_hdrs:
        print("[ERROR] No Auth headers captured. Please try again.")
        sys.exit(1)

    session = req_lib.Session()
    clean = {k: v for k, v in captured_hdrs.items() if not k.startswith(":")}
    session.headers.update(clean)
    cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
    if cookie_str:
        session.headers["cookie"] = cookie_str

    with open(HEADERS_FILE, "w", encoding="utf-8") as f:
        json.dump({"headers": captured_hdrs, "cookies": cookies}, f, indent=2)

    print("[AUTH] Session saved to sirman_headers.json ✅")
    return session


# ── Load Existing Data ────────────────────────────────────────────────────────
def load_existing():
    existing_products = []
    scraped_ids = set()
    category_map = {}
    all_raw_parts = []

    if CATALOG_FILE.exists():
        try:
            d = json.load(open(CATALOG_FILE, encoding="utf-8"))
            existing_products = d.get("products", [])
            scraped_ids = {str(p["id"]) for p in existing_products if p.get("id")}
        except Exception:
            pass

    if OUTPUT_FILE.exists():
        try:
            d = json.load(open(OUTPUT_FILE, encoding="utf-8"))
            category_map = d.get("categories", {})
            all_raw_parts = d.get("all_parts", [])
        except Exception:
            pass

    return existing_products, scraped_ids, category_map, all_raw_parts


# ── Save Progress ─────────────────────────────────────────────────────────────
def save_progress(all_products, category_map, all_raw_parts):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "categories": category_map,
            "all_parts": all_raw_parts,
            "summary": {
                "total_categories": len(category_map),
                "total_products": len(all_products),
                "total_parts": len(all_raw_parts),
            }
        }, f, ensure_ascii=False, indent=2)

    with open(CATALOG_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "categories": list(category_map.keys()),
            "products": all_products
        }, f, ensure_ascii=False, indent=2)


async def main():
    print("=" * 65)
    print("  SIRMAN FULL SCRAPER - 1,282 Categories Parallel Scrape")
    print("=" * 65)

    session = await get_valid_session()
    all_products, scraped_ids, category_map, all_raw_parts = load_existing()
    print(f"[RESUME] Currently have {len(all_products)} products and {len(all_raw_parts)} parts in database")

    # Fetch full category list from Sirman API
    cat_url = f"{API_BASE}/service-dwh/categories"
    r = session.get(cat_url, timeout=15)
    if r.status_code != 200:
        print(f"[ERROR] Failed to fetch category tree: HTTP {r.status_code}")
        sys.exit(1)

    all_cats = r.json()
    print(f"[INFO] Fetched {len(all_cats)} category nodes from Sirman API")

    # Fetch product list for a category ID
    def fetch_products_for_cat(cat_item):
        cid = cat_item["id"]
        cname = cat_item.get("i18n", {}).get("en") or cat_item.get("name", "Unknown")
        prods = []
        page = 1
        while True:
            url = f"{API_BASE}/service-dwh/products?category={cid}&productionFilter=all&page={page}&pageSize=100"
            try:
                res = session.get(url, timeout=12)
                if res.status_code == 200:
                    data = res.json()
                    items = data.get("items", [])
                    if not items:
                        break
                    for item in items:
                        item["_cat_id"] = str(cid)
                        item["_cat_name"] = cname
                    prods.extend(items)
                    if page >= data.get("totalPages", 1):
                        break
                    page += 1
                else:
                    break
            except Exception:
                break
        return cid, cname, prods

    # Worker: Fetch product details (exploded views + parts)
    def fetch_product_details(prod):
        prod_id = prod.get("id")
        if not prod_id:
            return None, []

        cid = prod.get("_cat_id", "")
        cname = prod.get("_cat_name", "")
        i18n = prod.get("i18n") or {}
        prod_name = i18n.get("en") or prod.get("name", "Unknown")
        code = prod.get("code") or f"SIR-{cid}-{prod_id}"
        serial = prod.get("serialNumber") or prod.get("sn") or f"SN-{prod_id}"
        barcode = prod.get("barcode") or prod.get("ean") or code

        views = []
        try:
            v_res = session.get(f"{API_BASE}/service-dwh/products/{prod_id}/exploded-views", timeout=12)
            if v_res.status_code == 200:
                views = v_res.json() or []
        except Exception:
            pass

        prod_parts = []
        pdf_name = ""

        for view in views:
            if not isinstance(view, dict):
                continue
            view_id = view.get("id")
            view_name = view.get("name", "")
            v_pdf = view.get("pdfName") or view.get("code") or view.get("fileName")
            if v_pdf and not pdf_name:
                pdf_name = v_pdf
            if not view_id:
                continue

            try:
                p_res = session.get(f"{API_BASE}/service-dwh/products/{prod_id}/exploded-views/{view_id}/parts", timeout=12)
                if p_res.status_code == 200:
                    parts = p_res.json() or []
                    for pt in parts:
                        if isinstance(pt, dict):
                            pt_code = pt.get("id") or ""
                            pt.update({
                                "_product_id": prod_id,
                                "_product_name": prod_name,
                                "_view_id": view_id,
                                "_view_name": view_name,
                                "serial": pt.get("serialNumber") or f"SN-{pt_code}",
                                "barcode": pt.get("barcode") or pt.get("ean") or pt_code,
                            })
                            prod_parts.append(pt)
            except Exception:
                pass

        prod_entry = {
            "id": prod_id,
            "code": code,
            "model": prod_name,
            "serial": serial,
            "barcode": barcode,
            "category_id": cid,
            "category_name": cname,
            "description": i18n.get("en", prod_name),
            "pdf_name": pdf_name,
            "parts_count": len(prod_parts),
            "parts": [{
                "id": pt.get("id"),
                "code": pt.get("id"),
                "name": pt.get("name"),
                "price": float(pt.get("price") or 0),
                "stock": pt.get("dispTot", 10),
                "ref": pt.get("explodedViewRef"),
                "view_name": pt.get("_view_name"),
            } for pt in prod_parts]
        }

        return prod_entry, prod_parts

    # Step 1: Scan all categories for product listings in parallel
    print(f"\n[Step 1] Scanning {len(all_cats)} category nodes for products (20 workers)...")
    discovered_prods = {}
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(fetch_products_for_cat, c) for c in all_cats]
        completed_cats = 0
        for f in as_completed(futures):
            completed_cats += 1
            cid, cname, prods = f.result()
            for p in prods:
                pid = p.get("id")
                if pid and str(pid) not in discovered_prods:
                    discovered_prods[str(pid)] = p
            if completed_cats % 100 == 0 or completed_cats == len(all_cats):
                print(f"  [{completed_cats}/{len(all_cats)}] categories scanned | Total unique products found so far: {len(discovered_prods)}")

    print(f"  -> Discovered {len(discovered_prods)} total unique products across all {len(all_cats)} categories!")

    # Filter out products already scraped
    new_prods = [p for pid, p in discovered_prods.items() if pid not in scraped_ids]
    print(f"  -> {len(all_products)} already scraped | {len(new_prods)} NEW products to fetch details for!")

    if not new_prods:
        print("\n[SUCCESS] 100% of all products across all categories are already scraped!")
        return

    # Step 2: Fetch details (exploded views + parts) for new products
    print(f"\n[Step 2] Fetching parts for {len(new_prods)} new products (20 workers)...")

    new_saved_count = 0
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(fetch_product_details, p) for p in new_prods]
        for idx, f in enumerate(as_completed(futures), 1):
            prod_entry, prod_parts = f.result()
            if prod_entry:
                all_products.append(prod_entry)
                scraped_ids.add(str(prod_entry["id"]))
                all_raw_parts.extend(prod_parts)
                cname = prod_entry.get("category_name", "General")
                category_map.setdefault(cname, []).append(prod_entry)
                new_saved_count += 1

            if idx % 25 == 0 or idx == len(new_prods):
                save_progress(all_products, category_map, all_raw_parts)
                elapsed = time.time() - start_time
                print(f"  [{idx}/{len(new_prods)}] Fetched details | Total products in DB: {len(all_products)} | Total parts: {len(all_raw_parts)} ({elapsed:.0f}s)")

    save_progress(all_products, category_map, all_raw_parts)
    print(f"\n[SUCCESS] Completed scraping {len(all_products)} products & {len(all_raw_parts)} parts total!")

    # Step 3: Automatically sync to Supabase
    print("\n[Step 3] Syncing all data to Supabase database...")
    import subprocess
    subprocess.run([sys.executable, str(BASE_DIR / "upload_to_supabase.py")], check=True)


if __name__ == "__main__":
    asyncio.run(main())
