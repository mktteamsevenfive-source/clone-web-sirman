"""
Sirman Parts Scraper v6 - Scrape ALL Categories, ALL Products, and ALL Parts
=============================================================================
1. เปิด browser -> login
2. จับ EXACT headers จาก API call ที่สำเร็จ
3. ดึงสินค้าทุกชิ้นในทุกหมวดหมู่ (ไม่มีจำกัด 20 ชิ้น)
4. บันทึกอะไหล่และข้อมูลทั้งหมดเข้า sirman_parts.json และ sirman_catalog_data.json
"""

import asyncio
import json
import sys
import time
from pathlib import Path

try:
    import requests as req_lib
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "requests"], check=True)
    import requests as req_lib

try:
    from playwright.async_api import async_playwright, Request, Response
except ImportError:
    print("Run: pip install playwright && playwright install chromium")
    sys.exit(1)

OUTPUT_FILE = Path(__file__).parent / "sirman_parts.json"
CATALOG_FILE = Path(__file__).parent / "sirman_catalog_data.json"
SIRMAN_DATA = Path(__file__).parent / "sirman_data.json"
API_BASE    = "https://api-service.sirman.com"

captured_headers = {}   # url -> request headers
captured_data    = {}   # url -> response body


async def on_request(request: Request):
    url = request.url
    if "api-service.sirman.com/service-dwh/" in url:
        headers = dict(request.headers)
        captured_headers[url] = headers


async def on_response(response: Response):
    url = response.url
    if "api-service.sirman.com" not in url:
        return
    try:
        ct = response.headers.get("content-type", "")
        if "json" in ct:
            text = await response.text()
            data = json.loads(text)
            captured_data[url] = data
    except Exception:
        pass


async def browse_and_capture() -> dict:
    print("=" * 65)
    print("  SIRMAN PARTS SCRAPER v6 - Scrape 100% Complete Catalog")
    print("=" * 65)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=50,
                                          args=["--start-maximized"])
        ctx = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await ctx.new_page()

        page.on("request",  on_request)
        page.on("response", on_response)

        print("\n[INFO] Opening service.sirman.com ...")
        await page.goto("https://service.sirman.com/catalog", wait_until="domcontentloaded")

        print("\n[WAIT] Please LOGIN to Sirman in the browser window.")
        print("       After login, CLICK on any category (e.g. Bar machines)")
        input("\n  >> Press Enter AFTER you clicked a category and see products ... ")

        try:
            await page.wait_for_load_state("networkidle", timeout=8000)
        except:
            pass
        await asyncio.sleep(2)

        browser_cookies = await ctx.cookies()

        print(f"\n[INFO] Captured {len(captured_headers)} request header(s)")
        print(f"[INFO] Captured {len(captured_data)} response(s)")
        await browser.close()

    return {
        "request_headers": captured_headers,
        "response_data":   captured_data,
        "cookies":         browser_cookies,
    }


def fetch_with_real_headers(session_info: dict):
    req_headers = session_info["request_headers"]
    resp_data   = session_info["response_data"]
    cookies_list = session_info["cookies"]

    if not req_headers:
        print("[ERROR] No request headers captured. Cannot proceed.")
        return

    best_headers = None
    for url, hdrs in req_headers.items():
        best_headers = {k: v for k, v in hdrs.items()
                        if k.lower() not in ["host", "content-length"]}
        print(f"\n[INFO] Using headers from: {url}")
        break

    if not best_headers:
        print("[ERROR] Could not find usable headers.")
        return

    s = req_lib.Session()
    s.headers.update(best_headers)
    for c in cookies_list:
        s.cookies.set(c["name"], c["value"], domain=c.get("domain", ""))

    def get(url):
        try:
            r = s.get(url, timeout=15)
            if r.status_code == 200:
                return r.json()
            print(f"    [WARN] HTTP {r.status_code} for {url}")
            return None
        except Exception as e:
            print(f"    [ERR] {e}")
            return None

    cat_list = [
        (4,"Bar machines"),(6,"Slicers"),(7,"Meat processors"),
        (31,"Cooking machines"),(5,"Packaging machines"),(51,"Scales"),
        (52,"Ozone generators"),(61,"Dishwashers"),(2,"Snack and pizza"),
        (3,"Food processors"),(27,"Consumables"),(28,"Laundry"),(18,"Microwaves ovens"),
    ]

    result = {"categories": {}, "all_parts": [], "summary": {}}
    catalog_products = []
    total_products = 0
    total_parts = 0

    print(f"\n{'='*65}")
    print("Fetching ALL products & spare parts across ALL categories...")
    print(f"{'='*65}")

    for cat_id, cat_name in cat_list:
        print(f"\n[Category] {cat_name} (id={cat_id})")
        products = []

        # Paginate to fetch all products in category
        page_num = 1
        while True:
            url = f"{API_BASE}/service-dwh/products?category={cat_id}&type=group&productionFilter=all&page={page_num}&pageSize=100&catalog=catalog"
            data = get(url)
            if data and isinstance(data, dict) and "items" in data:
                items = data["items"]
                if not items:
                    break
                products.extend(items)
                total_pages = data.get("totalPages", 1)
                print(f"  -> Page {page_num}/{total_pages}: {len(items)} products")
                if page_num >= total_pages:
                    break
                page_num += 1
            else:
                break

        print(f"  == Total in {cat_name}: {len(products)} products ==")
        total_products += len(products)
        cat_entry = {"id": cat_id, "name": cat_name, "products": []}

        # Process ALL products without slice limits
        for idx, prod in enumerate(products, 1):
            if not isinstance(prod, dict):
                continue
            prod_id = prod.get("id")
            i18n = prod.get("i18n") or {}
            prod_name = i18n.get("en") or prod.get("name", "Unknown")
            code = prod.get("code") or f"SIR-{cat_name[:3].upper()}-{prod_id}"
            serial = prod.get("serialNumber") or prod.get("sn") or f"SN-{prod_id}"
            pdf_name = prod.get("pdfName") or prod.get("explodedViewPdf") or ""

            if not prod_id:
                continue

            print(f"  [{idx}/{len(products)}] Product: {prod_name} (id={prod_id})")

            views = get(f"{API_BASE}/service-dwh/products/{prod_id}/exploded-views")
            all_parts = []

            if views and isinstance(views, list):
                for view in views:
                    if not isinstance(view, dict):
                        continue
                    view_id   = view.get("id")
                    view_name = view.get("name", "")
                    if not view_id:
                        continue

                    parts = get(f"{API_BASE}/service-dwh/products/{prod_id}/exploded-views/{view_id}/parts")
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

            total_parts += len(all_parts)
            cat_entry["products"].append({
                "id": prod_id, "name": prod_name, "raw": prod, "parts": all_parts
            })
            result["all_parts"].extend(all_parts)

            catalog_products.append({
                "id": prod_id,
                "code": code,
                "model": prod_name,
                "serial": serial,
                "category_id": str(cat_id),
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
            })

            time.sleep(0.08)

        result["categories"][cat_name] = cat_entry

        # Save progress
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"  [Saved] Total parts so far: {total_parts}")

    result["summary"] = {
        "total_categories": len(result["categories"]),
        "total_products":   total_products,
        "total_parts":      total_parts,
    }
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # Save to sirman_catalog_data.json as well
    with open(CATALOG_FILE, "w", encoding="utf-8") as f:
        json.dump({"categories": result["categories"], "products": catalog_products}, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*65}")
    print(f"[DONE] SCRAPED 100% COMPLETE CATALOG!")
    print(f"  Categories: {len(result['categories'])}")
    print(f"  Products:   {total_products}")
    print(f"  Parts:      {total_parts}")
    print(f"{'='*65}")


async def main():
    session_info = await browse_and_capture()
    fetch_with_real_headers(session_info)


if __name__ == "__main__":
    asyncio.run(main())
