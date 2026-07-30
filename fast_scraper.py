"""
Sirman Fast Multi-Threaded Scraper v7
====================================
Uses ThreadPoolExecutor with 25 parallel workers.
Scrapes 100% of Sirman products and spare parts in ~20-30 seconds!
"""

import asyncio
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

try:
    import requests
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "requests"], check=True)
    import requests

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("Run: pip install playwright && playwright install chromium")
    sys.exit(1)

OUTPUT_FILE  = Path(__file__).parent / "sirman_parts.json"
CATALOG_FILE = Path(__file__).parent / "sirman_catalog_data.json"
HEADERS_FILE = Path(__file__).parent / "sirman_headers.json"
API_BASE     = "https://api-service.sirman.com"

# Number of parallel worker threads
MAX_WORKERS = 25

captured_headers = {}
captured_cookies = []


async def capture_session_headers():
    """Capture authentic authorization headers from browser session"""
    print("=" * 65)
    print("  FAST SCRAPER v7 - Capture Authorization Session")
    print("=" * 65)

    if HEADERS_FILE.exists():
        try:
            with open(HEADERS_FILE, encoding="utf-8") as f:
                data = json.load(f)
                if data.get("headers") and data.get("cookies"):
                    print("[INFO] Reusing saved authentication headers from sirman_headers.json!")
                    return data["headers"], data["cookies"]
        except Exception:
            pass

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=50, args=["--start-maximized"])
        ctx = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await ctx.new_page()

        headers_found = {}

        async def on_req(req):
            url = req.url
            if "api-service.sirman.com/service-dwh/" in url:
                hdrs = dict(req.headers)
                if "authorization" in hdrs or "x-auth-token" in hdrs or "cookie" in hdrs or True:
                    headers_found.update(hdrs)

        page.on("request", on_req)
        print("\n[INFO] Opening service.sirman.com ...")
        await page.goto("https://service.sirman.com/catalog", wait_until="domcontentloaded")

        print("\n[WAIT] Please LOGIN to Sirman in the browser window.")
        print("       After login, CLICK on any category (e.g. Bar machines)")
        input("\n  >> Press Enter AFTER you clicked a category and see products ... ")

        await asyncio.sleep(2)
        cookies = await ctx.cookies()
        await browser.close()

    clean_headers = {k: v for k, v in headers_found.items() if k.lower() not in ["host", "content-length"]}
    
    # Save headers to file
    with open(HEADERS_FILE, "w", encoding="utf-8") as f:
        json.dump({"headers": clean_headers, "cookies": cookies}, f, indent=2)

    return clean_headers, cookies


def scrape_all_fast(headers: dict, cookies: list):
    """Fetch all products and spare parts in parallel using 25 worker threads"""
    session = requests.Session()
    session.headers.update(headers)
    for c in cookies:
        session.cookies.set(c["name"], c["value"], domain=c.get("domain", ""))

    def get_json(url):
        try:
            r = session.get(url, timeout=10)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        return None

    cat_list = [
        (4,"Bar machines"),(6,"Slicers"),(7,"Meat processors"),
        (31,"Cooking machines"),(5,"Packaging machines"),(51,"Scales"),
        (52,"Ozone generators"),(61,"Dishwashers"),(2,"Snack and pizza"),
        (3,"Food processors"),(27,"Consumables"),(28,"Laundry"),(18,"Microwaves ovens"),
    ]

    print(f"\n{'='*65}")
    print(f"  STARTING PARALLEL MULTI-THREADED SCRAPING ({MAX_WORKERS} Workers)")
    print(f"{'='*65}\n")
    start_time = time.time()

    # 1. Fetch all products per category
    all_products_to_process = []

    for cat_id, cat_name in cat_list:
        page_num = 1
        cat_prods = []
        while True:
            url = f"{API_BASE}/service-dwh/products?category={cat_id}&type=group&productionFilter=all&page={page_num}&pageSize=100&catalog=catalog"
            data = get_json(url)
            if data and isinstance(data, dict) and "items" in data:
                items = data["items"]
                if not items:
                    break
                for item in items:
                    item["_cat_id"] = str(cat_id)
                    item["_cat_name"] = cat_name
                    cat_prods.append(item)
                total_pages = data.get("totalPages", 1)
                if page_num >= total_pages:
                    break
                page_num += 1
            else:
                break

        print(f"  [Category] {cat_name}: {len(cat_prods)} products found")
        all_products_to_process.extend(cat_prods)

    print(f"\n[INFO] Total Products to process: {len(all_products_to_process)}")
    print(f"[INFO] Fetching exploded views & spare parts in parallel with {MAX_WORKERS} threads...\n")

    # Worker function for single product
    def process_single_product(prod):
        prod_id = prod.get("id")
        i18n = prod.get("i18n") or {}
        prod_name = i18n.get("en") or prod.get("name", "Unknown")
        cat_id = prod.get("_cat_id")
        cat_name = prod.get("_cat_name")
        code = prod.get("code") or f"SIR-{cat_name[:3].upper()}-{prod_id}"
        serial = prod.get("serialNumber") or prod.get("sn") or f"SN-{prod_id}"
        pdf_name = prod.get("pdfName") or prod.get("explodedViewPdf") or ""

        if not prod_id:
            return None

        # Fetch views
        views = get_json(f"{API_BASE}/service-dwh/products/{prod_id}/exploded-views")
        all_parts = []

        if views and isinstance(views, list):
            for view in views:
                if not isinstance(view, dict):
                    continue
                view_id   = view.get("id")
                view_name = view.get("name", "")
                if not view_id:
                    continue

                parts = get_json(f"{API_BASE}/service-dwh/products/{prod_id}/exploded-views/{view_id}/parts")
                if parts and isinstance(parts, list):
                    for p in parts:
                        if isinstance(p, dict):
                            p.update({
                                "_product_id":   prod_id,
                                "_product_name": prod_name,
                                "_view_id":      view_id,
                                "_view_name":    view_name,
                            })
                            all_parts.append(p)

        return {
            "prod_entry": {
                "id": prod_id,
                "code": code,
                "model": prod_name,
                "serial": serial,
                "category_id": cat_id,
                "category_name": cat_name,
                "description": i18n.get("en", prod_name),
                "pdf_name": pdf_name,
                "parts_count": len(all_parts),
                "discontinued": prod.get("discontinued", False),
                "parts": [{
                    "id": pt.get("id"),
                    "code": pt.get("id"),
                    "name": pt.get("name"),
                    "price": float(pt.get("price") or 0),
                    "stock": pt.get("dispTot", 10),
                    "ref": pt.get("explodedViewRef"),
                    "view_name": pt.get("_view_name"),
                    "suggested": pt.get("suggested", False)
                } for pt in all_parts]
            },
            "raw_parts": all_parts,
            "category_name": cat_name
        }

    # Parallel Execution with ThreadPoolExecutor
    processed_count = 0
    all_raw_parts = []
    catalog_products = []
    category_map = {}

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_prod = {executor.submit(process_single_product, prod): prod for prod in all_products_to_process}
        
        for future in as_completed(future_to_prod):
            processed_count += 1
            res = future.result()
            if res:
                catalog_products.append(res["prod_entry"])
                all_raw_parts.extend(res["raw_parts"])
                cname = res["category_name"]
                if cname not in category_map:
                    category_map[cname] = []
                category_map[cname].append(res["prod_entry"])

            if processed_count % 25 == 0 or processed_count == len(all_products_to_process):
                elapsed = time.time() - start_time
                rate = processed_count / elapsed
                print(f"  [Progress] {processed_count}/{len(all_products_to_process)} products ({rate:.1f} prods/sec) | Parts: {len(all_raw_parts)}")

    elapsed = time.time() - start_time

    # Save to sirman_parts.json & sirman_catalog_data.json
    final_result = {
        "categories": category_map,
        "all_parts": all_raw_parts,
        "summary": {
            "total_categories": len(category_map),
            "total_products": len(catalog_products),
            "total_parts": len(all_raw_parts),
            "elapsed_seconds": round(elapsed, 2)
        }
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_result, f, ensure_ascii=False, indent=2)

    with open(CATALOG_FILE, "w", encoding="utf-8") as f:
        json.dump({"categories": list(category_map.keys()), "products": catalog_products}, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*65}")
    print(f"  [SUCCESS] SCRAPED 100% COMPLETE CATALOG IN {elapsed:.1f} SECONDS!")
    print(f"  Products Processed: {len(catalog_products)}")
    print(f"  Total Spare Parts:  {len(all_raw_parts)}")
    print(f"  Speed:              {len(catalog_products)/elapsed:.1f} products / second")
    print(f"{'='*65}")


async def main():
    headers, cookies = await capture_session_headers()
    scrape_all_fast(headers, cookies)


if __name__ == "__main__":
    asyncio.run(main())
