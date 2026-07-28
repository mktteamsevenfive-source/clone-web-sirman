"""
Sirman Parts Scraper v5 - Capture Real Request Headers
=======================================================
1. เปิด browser -> login
2. จับ EXACT headers จาก API call ที่สำเร็จ (ดักตอน navigate หน้า catalog)
3. ใช้ headers + cookies เหล่านั้นใน Python requests
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
SIRMAN_DATA = Path(__file__).parent / "sirman_data.json"
API_BASE    = "https://api-service.sirman.com"

# Will be filled by interceptor
captured_headers = {}   # url -> request headers
captured_data    = {}   # url -> response body


async def on_request(request: Request):
    url = request.url
    if "api-service.sirman.com/service-dwh/" in url and "products" in url:
        headers = dict(request.headers)
        captured_headers[url] = headers
        print(f"  [REQ CAPTURED] {url.replace(API_BASE,'')[:70]}")
        print(f"    Headers: {[k for k in headers.keys()][:8]}")


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
            path = url.replace(f"{API_BASE}/", "")
            if isinstance(data, list):
                print(f"  [RESP] {path[:70]} -> {len(data)} items")
            elif isinstance(data, dict) and "items" in data:
                print(f"  [RESP] {path[:70]} -> {len(data.get('items',[]))} products")
    except Exception:
        pass


async def browse_and_capture() -> dict:
    """Open browser, intercept real API requests with their headers"""
    print("=" * 65)
    print("  SIRMAN PARTS SCRAPER v5 - Capture Real Headers")
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
        print("       This will trigger the API call we need to capture.")
        input("\n  >> Press Enter AFTER you clicked a category and see products ... ")

        try:
            await page.wait_for_load_state("networkidle", timeout=8000)
        except:
            pass
        await asyncio.sleep(3)

        # Get cookies
        browser_cookies = await ctx.cookies()

        print(f"\n[INFO] Captured {len(captured_headers)} product API request(s)")
        print(f"[INFO] Captured {len(captured_data)} response(s)")
        print(f"[INFO] Cookies: {len(browser_cookies)}")

        await browser.close()

    return {
        "request_headers": captured_headers,
        "response_data":   captured_data,
        "cookies":         browser_cookies,
    }


def fetch_with_real_headers(session_info: dict):
    """Use exact same headers from captured requests to fetch all data"""
    req_headers = session_info["request_headers"]
    resp_data   = session_info["response_data"]
    cookies_list = session_info["cookies"]

    if not req_headers:
        print("[ERROR] No request headers captured. Cannot proceed.")
        return

    # Pick best headers (from any successful product request)
    best_headers = None
    for url, hdrs in req_headers.items():
        best_headers = {k: v for k, v in hdrs.items()
                        if k.lower() not in ["host", "content-length"]}
        print(f"\n[INFO] Using headers from: {url}")
        print(f"  Keys: {list(best_headers.keys())}")
        break

    if not best_headers:
        print("[ERROR] Could not find usable headers.")
        return

    # Build requests session
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

    # Load categories
    cat_list = []
    if SIRMAN_DATA.exists():
        with open(SIRMAN_DATA, encoding="utf-8") as f:
            d = json.load(f)
        raw = d.get("api_responses", {}).get(
            "https://api-service.sirman.com/service-dwh/categories", [])
        cat_list = [(c["id"], c["i18n"].get("en", c["name"]))
                    for c in raw
                    if c.get("father") == 0 and c.get("type") == "group"]

    if not cat_list:
        cat_list = [
            (4,"Bar machines"),(6,"Slicers"),(7,"Meat processors"),
            (31,"Cooking machines"),(5,"Packaging machines"),(51,"Scales"),
            (52,"Ozone generators"),(61,"Dishwashers"),(2,"Snack and pizza"),
            (3,"Food processors"),(27,"Consumables"),(28,"Laundry"),(18,"Microwaves ovens"),
        ]

    result = {"categories": {}, "all_parts": [], "summary": {}}
    total_products = 0
    total_parts = 0

    print(f"\n{'='*65}")
    print("Fetching all products & parts...")
    print(f"{'='*65}")

    for cat_id, cat_name in cat_list:
        print(f"\n[Category] {cat_name} (id={cat_id})")

        # Also check if we already have this in captured responses
        products = []
        for url, data in resp_data.items():
            if f"category={cat_id}" in url and isinstance(data, dict) and "items" in data:
                products = data["items"]
                print(f"  -> {len(products)} products (from cache)")
                break

        if not products:
            url = f"{API_BASE}/service-dwh/products?category={cat_id}&type=group&productionFilter=all&page=1&pageSize=50&catalog=catalog"
            data = get(url)
            if data and isinstance(data, dict) and "items" in data:
                products = data["items"]
                print(f"  -> {len(products)} products")
            else:
                print(f"  -> No products")
                continue

        total_products += len(products)
        cat_entry = {"id": cat_id, "name": cat_name, "products": []}

        for prod in products[:20]:
            if not isinstance(prod, dict):
                continue
            prod_id = prod.get("id")
            i18n = prod.get("i18n") or {}
            prod_name = i18n.get("en") or prod.get("name", "Unknown")
            if not prod_id:
                continue

            print(f"\n  [Product] {prod_name} (id={prod_id})")

            views = get(f"{API_BASE}/service-dwh/products/{prod_id}/exploded-views")
            all_parts = []

            if views and isinstance(views, list):
                print(f"    -> {len(views)} views")
                for view in views[:5]:
                    if not isinstance(view, dict):
                        continue
                    view_id   = view.get("id")
                    view_name = view.get("name", "")
                    if not view_id:
                        continue

                    parts = get(f"{API_BASE}/service-dwh/products/{prod_id}/exploded-views/{view_id}/parts")
                    if parts and isinstance(parts, list):
                        print(f"      -> '{view_name}': {len(parts)} parts")
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
            time.sleep(0.15)

        result["categories"][cat_name] = cat_entry

        # Save progress
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        sz = OUTPUT_FILE.stat().st_size / 1024
        print(f"  [Saved] {total_parts} parts | {sz:.1f} KB")

    result["summary"] = {
        "total_categories": len(result["categories"]),
        "total_products":   total_products,
        "total_parts":      total_parts,
    }
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    sz = OUTPUT_FILE.stat().st_size / 1024
    print(f"\n{'='*65}")
    print(f"[DONE] {OUTPUT_FILE}")
    print(f"  Categories: {len(result['categories'])}")
    print(f"  Products:   {total_products}")
    print(f"  Parts:      {total_parts}")
    print(f"  File:       {sz:.1f} KB")
    print(f"{'='*65}")


async def main():
    # Step 1: Open browser, let user navigate, capture real request headers
    session_info = await browse_and_capture()

    # Step 2: Use those headers with Python requests
    fetch_with_real_headers(session_info)


if __name__ == "__main__":
    asyncio.run(main())
