"""
Sirman Master Scraper v8.5 - Intercept Auth Headers Then Fetch All
===================================================================
1. Intercepts REAL authorization headers from browser network requests
2. Uses those exact headers to fetch ALL products/parts/images
3. Fetches ALL model variants (no type=group limitation)
4. Downloads diagram PNG images -> public/exploded-views/
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
    from playwright.async_api import async_playwright, Request as PWRequest, Response as PWResponse
except ImportError:
    print("Run: pip install playwright && playwright install chromium")
    sys.exit(1)

OUTPUT_FILE  = Path(__file__).parent / "sirman_parts.json"
CATALOG_FILE = Path(__file__).parent / "sirman_catalog_data.json"
IMAGES_DIR   = Path(__file__).parent / "public" / "exploded-views"
API_BASE     = "https://api-service.sirman.com"

IMAGES_DIR.mkdir(parents=True, exist_ok=True)

captured_auth_headers: dict = {}


async def capture_headers() -> dict:
    """Open browser, wait for user to login and navigate, capture real API headers."""
    print("=" * 65)
    print("  SIRMAN MASTER SCRAPER v8.5 - Capture Auth Headers")
    print("=" * 65)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=["--start-maximized"])
        ctx = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await ctx.new_page()

        auth_headers: dict = {}

        async def on_request(req: PWRequest):
            url = req.url
            if "api-service.sirman.com/service-dwh/products" in url and "category=" in url:
                hdrs = dict(req.headers)
                # Only keep if it has an auth token
                if any(k.lower() in hdrs for k in ["authorization", "x-auth-token", "x-customer-code", "cookie"]):
                    auth_headers.update({k: v for k, v in hdrs.items()
                                         if k.lower() not in ["host", "content-length", ":method", ":path", ":scheme", ":authority"]})
                    print(f"  [AUTH] Captured headers from: {url[:80]}")
                    print(f"         Keys: {list(auth_headers.keys())}")

        page.on("request", on_request)

        print("\n[INFO] Opening service.sirman.com ...")
        await page.goto("https://service.sirman.com/catalog", wait_until="domcontentloaded")

        print("\n[WAIT] Please:")
        print("  1. LOGIN to Sirman in the browser window")
        print("  2. CLICK on any category (e.g. Meat processors) so the API fires")
        print("  3. Wait for the product list to LOAD FULLY")
        input("\n  >> Press Enter AFTER you can see the product grid ... ")

        try:
            await page.wait_for_load_state("networkidle", timeout=5000)
        except Exception:
            pass
        await asyncio.sleep(1)

        cookies_list = await ctx.cookies()
        await browser.close()

    if not auth_headers:
        print("\n[ERROR] No API headers captured. Make sure you clicked on a category!")
        sys.exit(1)

    # Build cookie header string
    cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies_list)
    if cookie_str:
        auth_headers["cookie"] = cookie_str

    print(f"\n[SUCCESS] Auth headers captured: {list(auth_headers.keys())}")
    return auth_headers


def scrape_all(auth_headers: dict):
    """Use captured headers to scrape ALL products, parts and images."""
    session = req_lib.Session()
    # Remove pseudo-headers that can't be sent via requests
    clean_headers = {k: v for k, v in auth_headers.items()
                     if not k.startswith(":")}
    session.headers.update(clean_headers)

    def get_json(url):
        try:
            r = session.get(url, timeout=15)
            if r.status_code == 200:
                return r.json()
            print(f"    [WARN] HTTP {r.status_code}: {url[-60:]}")
        except Exception as e:
            print(f"    [ERR] {e}")
        return None

    def download_image(pdf_name: str) -> bool:
        """Try to download diagram PNG from Sirman CDN."""
        img_filename = f"{pdf_name}.png" if not pdf_name.endswith(".png") else pdf_name
        target = IMAGES_DIR / img_filename
        if target.exists():
            return False  # Already downloaded
        url = f"{API_BASE}/service-dwh/media/exploded-views/{img_filename}"
        try:
            r = session.get(url, timeout=15)
            if r.status_code == 200:
                with open(target, "wb") as f:
                    f.write(r.content)
                return True
        except Exception:
            pass
        return False

    cat_list = [
        (7, "Meat processors"),
        (6, "Slicers"),
        (4, "Bar machines"),
        (31, "Cooking machines"),
        (5, "Packaging machines"),
        (51, "Scales"),
        (52, "Ozone generators"),
        (61, "Dishwashers"),
        (2, "Snack and pizza"),
        (3, "Food processors"),
        (27, "Consumables"),
        (28, "Laundry"),
        (18, "Microwaves ovens"),
    ]

    all_products = []
    all_raw_parts = []
    category_map: dict = {}
    downloaded_images = 0
    start = time.time()

    print(f"\n{'='*65}")
    print("  STARTING FULL CATALOG EXTRACTION")
    print(f"{'='*65}")

    for cat_id, cat_name in cat_list:
        print(f"\n[Category] {cat_name} (id={cat_id})")
        cat_products = []

        # Paginate without type=group so we get ALL variants (2,140+ Meat Processors etc.)
        page_num = 1
        while True:
            url = f"{API_BASE}/service-dwh/products?category={cat_id}&productionFilter=all&page={page_num}&pageSize=100"
            data = get_json(url)
            if data and isinstance(data, dict) and "items" in data:
                items = data.get("items", [])
                if not items:
                    break
                cat_products.extend(items)
                total_pages = data.get("totalPages", 1)
                total_items = data.get("totalItems", len(cat_products))
                print(f"  -> Page {page_num}/{total_pages}: {len(cat_products)}/{total_items} loaded")
                if page_num >= total_pages:
                    break
                page_num += 1
            else:
                break

        print(f"  == TOTAL IN {cat_name}: {len(cat_products)} PRODUCTS ==")
        cat_entries = []

        for idx, prod in enumerate(cat_products, 1):
            prod_id = prod.get("id")
            if not prod_id:
                continue

            i18n = prod.get("i18n") or {}
            prod_name = i18n.get("en") or prod.get("name", "Unknown")
            code = prod.get("code") or f"SIR-{str(cat_id)}-{prod_id}"
            serial = prod.get("serialNumber") or prod.get("sn") or f"SN-{prod_id}"
            barcode = prod.get("barcode") or prod.get("ean") or code

            # Exploded views
            views = get_json(f"{API_BASE}/service-dwh/products/{prod_id}/exploded-views") or []

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

                parts = get_json(f"{API_BASE}/service-dwh/products/{prod_id}/exploded-views/{view_id}/parts") or []
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
                        all_raw_parts.append(pt)

            # Download image
            if pdf_name and download_image(pdf_name):
                downloaded_images += 1

            prod_entry = {
                "id": prod_id,
                "code": code,
                "model": prod_name,
                "serial": serial,
                "barcode": barcode,
                "category_id": str(cat_id),
                "category_name": cat_name,
                "description": i18n.get("en", prod_name),
                "pdf_name": pdf_name,
                "parts_count": len(prod_parts),
                "discontinued": prod.get("discontinued", False),
                "parts": [{
                    "id": pt.get("id"),
                    "code": pt.get("id"),
                    "name": pt.get("name"),
                    "price": float(pt.get("price") or 0),
                    "stock": pt.get("dispTot", 10),
                    "ref": pt.get("explodedViewRef"),
                    "view_name": pt.get("_view_name"),
                    "suggested": pt.get("suggested", False),
                    "serial": pt.get("serial"),
                    "barcode": pt.get("barcode"),
                } for pt in prod_parts]
            }

            all_products.append(prod_entry)
            cat_entries.append(prod_entry)

            if idx % 25 == 0 or idx == len(cat_products):
                elapsed = time.time() - start
                rate = idx / elapsed if elapsed > 0 else 0
                print(f"    [{idx}/{len(cat_products)}] {prod_name} | Parts: {len(prod_parts)} | Images: {downloaded_images} | {rate:.1f} prods/s")

        category_map[cat_name] = cat_entries

        # Save progress after each category
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "categories": category_map,
                "all_parts": all_raw_parts,
                "summary": {
                    "total_categories": len(category_map),
                    "total_products": len(all_products),
                    "total_parts": len(all_raw_parts),
                    "downloaded_images": downloaded_images,
                }
            }, f, ensure_ascii=False, indent=2)
        print(f"  [SAVED] {len(all_products)} products, {len(all_raw_parts)} parts, {downloaded_images} images so far")

    elapsed = time.time() - start

    # Final save
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "categories": category_map,
            "all_parts": all_raw_parts,
            "summary": {
                "total_categories": len(category_map),
                "total_products": len(all_products),
                "total_parts": len(all_raw_parts),
                "downloaded_images": downloaded_images,
                "elapsed_seconds": round(elapsed, 2),
            }
        }, f, ensure_ascii=False, indent=2)

    with open(CATALOG_FILE, "w", encoding="utf-8") as f:
        json.dump({"categories": list(category_map.keys()), "products": all_products}, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*65}")
    print(f"  [DONE] COMPLETE IN {elapsed:.1f}s!")
    print(f"  Total Products:    {len(all_products)}")
    print(f"  Total Parts:       {len(all_raw_parts)}")
    print(f"  Images Downloaded: {downloaded_images}")
    print(f"{'='*65}")


async def main():
    auth_headers = await capture_headers()
    scrape_all(auth_headers)


if __name__ == "__main__":
    asyncio.run(main())
