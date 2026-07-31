"""
Sirman Master Scraper v9 - Resumable / Incremental
====================================================
SMART FEATURES:
- Checks existing sirman_catalog_data.json / sirman_parts.json
- Skips categories + products that are already scraped
- Resumes from last saved point if interrupted
- Never re-downloads data that already exists
- Saves progress after every product batch
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
    from playwright.async_api import async_playwright
except ImportError:
    print("Run: pip install playwright && playwright install chromium")
    sys.exit(1)

OUTPUT_FILE  = Path(__file__).parent / "sirman_parts.json"
CATALOG_FILE = Path(__file__).parent / "sirman_catalog_data.json"
HEADERS_FILE = Path(__file__).parent / "sirman_headers.json"
API_BASE     = "https://api-service.sirman.com"


# ── Load existing data (for resume) ──────────────────────────────────────────
def load_existing_data() -> tuple[dict, list, set]:
    """Load existing scraped data. Returns (category_map, all_products, scraped_ids)."""
    category_map: dict = {}
    all_products: list = []
    all_raw_parts: list = []
    scraped_product_ids: set = set()

    if OUTPUT_FILE.exists():
        try:
            d = json.load(open(OUTPUT_FILE, encoding="utf-8"))
            category_map = d.get("categories", {})
            all_raw_parts = d.get("all_parts", [])
            print(f"[RESUME] Loaded {len(category_map)} categories from {OUTPUT_FILE.name}")
        except Exception as e:
            print(f"[WARN] Could not load {OUTPUT_FILE.name}: {e}")

    if CATALOG_FILE.exists():
        try:
            d = json.load(open(CATALOG_FILE, encoding="utf-8"))
            all_products = d.get("products", [])
            scraped_product_ids = {str(p["id"]) for p in all_products if p.get("id")}
            print(f"[RESUME] Loaded {len(all_products)} products from {CATALOG_FILE.name}")
            print(f"[RESUME] Already have {len(scraped_product_ids)} unique product IDs → will skip these")
        except Exception as e:
            print(f"[WARN] Could not load {CATALOG_FILE.name}: {e}")

    return category_map, all_products, all_raw_parts, scraped_product_ids


# ── Save progress ──────────────────────────────────────────────────────────────
def save_progress(category_map: dict, all_products: list, all_raw_parts: list, downloaded_images: int):
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

    with open(CATALOG_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "categories": list(category_map.keys()),
            "products": all_products
        }, f, ensure_ascii=False, indent=2)


# ── Capture or load Sirman auth session ───────────────────────────────────────
async def get_sirman_session() -> req_lib.Session:
    """Load saved session or capture new one from browser."""

    if HEADERS_FILE.exists():
        try:
            data = json.load(open(HEADERS_FILE, encoding="utf-8"))
            hdrs = data.get("headers", {})
            cookies = data.get("cookies", [])
            if hdrs and any("authorization" in k.lower() or "x-customer-code" in k.lower() for k in hdrs):
                session = req_lib.Session()
                clean = {k: v for k, v in hdrs.items() if not k.startswith(":")}
                session.headers.update(clean)
                cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
                if cookie_str:
                    session.headers["cookie"] = cookie_str

                # Quick test if session still works
                test = session.get(f"{API_BASE}/service-dwh/products?category=4&page=1&pageSize=1", timeout=8)
                if test.status_code == 200:
                    print("[AUTH] Reusing saved session from sirman_headers.json ✅")
                    return session
                else:
                    print(f"[AUTH] Saved session expired (HTTP {test.status_code}), need to re-login...")
        except Exception as e:
            print(f"[AUTH] Could not load headers: {e}")

    # Capture new session
    print("\n[AUTH] Opening browser to capture new session...")
    captured_hdrs: dict = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=["--start-maximized"])
        ctx = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await ctx.new_page()

        async def on_request(req):
            if "api-service.sirman.com/service-dwh/products" in req.url and "category=" in req.url:
                hdrs = dict(req.headers)
                if any(k.lower() in hdrs for k in ["authorization", "x-customer-code"]):
                    captured_hdrs.update({k: v for k, v in hdrs.items() if not k.startswith(":")})
                    print(f"  [AUTH] Captured from: {req.url[:80]}")

        page.on("request", on_request)
        await page.goto("https://service.sirman.com/catalog", wait_until="domcontentloaded")

        print("\n[WAIT] Please LOGIN and CLICK a category, then press Enter...")
        input("  >> ")

        try:
            await page.wait_for_load_state("networkidle", timeout=6000)
        except Exception:
            pass

        cookies = await ctx.cookies()
        await browser.close()

    session = req_lib.Session()
    clean = {k: v for k, v in captured_hdrs.items() if not k.startswith(":")}
    session.headers.update(clean)
    cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
    if cookie_str:
        session.headers["cookie"] = cookie_str

    with open(HEADERS_FILE, "w", encoding="utf-8") as f:
        json.dump({"headers": captured_hdrs, "cookies": cookies}, f, indent=2)
    print("[AUTH] Session saved to sirman_headers.json for future runs ✅")
    return session


# ── Main scraping logic ───────────────────────────────────────────────────────
async def main():
    print("=" * 65)
    print("  SIRMAN SCRAPER v9 - Resumable / Incremental")
    print("=" * 65)

    # Load existing data
    print("\n[RESUME] Checking existing data...")
    category_map, all_products, all_raw_parts, scraped_ids = load_existing_data()

    # Get authenticated session
    session = await get_sirman_session()

    def get_json(url: str):
        try:
            r = session.get(url, timeout=15)
            if r.status_code == 200:
                return r.json()
            print(f"    [WARN] HTTP {r.status_code}: {url[-60:]}")
        except Exception as e:
            print(f"    [ERR] {e}")
        return None

    cat_list = [
        (7, "Meat processors"), (6, "Slicers"), (4, "Bar machines"),
        (31, "Cooking machines"), (5, "Packaging machines"), (51, "Scales"),
        (52, "Ozone generators"), (61, "Dishwashers"), (2, "Snack and pizza"),
        (3, "Food processors"), (27, "Consumables"), (28, "Laundry"), (18, "Microwaves ovens"),
    ]

    downloaded_images = 0
    start = time.time()

    print(f"\n{'='*65}")
    print("  STARTING INCREMENTAL SCRAPE (skipping already scraped items)")
    print(f"{'='*65}")

    for cat_id, cat_name in cat_list:
        print(f"\n[Category] {cat_name} (id={cat_id})")

        # Fetch full product list for category
        cat_products = []
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
                print(f"  -> Page {page_num}/{total_pages}: {len(cat_products)}/{total_items}")
                if page_num >= total_pages:
                    break
                page_num += 1
            else:
                break

        # Split into new vs already scraped
        new_products = [p for p in cat_products if str(p.get("id", "")) not in scraped_ids]
        skipped = len(cat_products) - len(new_products)

        print(f"  Total: {len(cat_products)} | Already scraped: {skipped} (skip) | New: {len(new_products)}")

        if not new_products:
            print(f"  ✅ All products in {cat_name} already scraped — skipping")
            continue

        # Load existing entries for this category
        cat_entries = list(category_map.get(cat_name, []))

        for idx, prod in enumerate(new_products, 1):
            prod_id = prod.get("id")
            if not prod_id:
                continue

            i18n = prod.get("i18n") or {}
            prod_name = i18n.get("en") or prod.get("name", "Unknown")
            code = prod.get("code") or f"SIR-{cat_id}-{prod_id}"
            serial = prod.get("serialNumber") or prod.get("sn") or f"SN-{prod_id}"
            barcode = prod.get("barcode") or prod.get("ean") or code

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
                            "_product_id": prod_id, "_product_name": prod_name,
                            "_view_id": view_id, "_view_name": view_name,
                            "serial": pt.get("serialNumber") or f"SN-{pt_code}",
                            "barcode": pt.get("barcode") or pt.get("ean") or pt_code,
                        })
                        prod_parts.append(pt)
                        all_raw_parts.append(pt)

            prod_entry = {
                "id": prod_id, "code": code, "model": prod_name,
                "serial": serial, "barcode": barcode,
                "category_id": str(cat_id), "category_name": cat_name,
                "description": i18n.get("en", prod_name), "pdf_name": pdf_name,
                "parts_count": len(prod_parts),
                "discontinued": prod.get("discontinued", False),
                "parts": [{
                    "id": pt.get("id"), "code": pt.get("id"), "name": pt.get("name"),
                    "price": float(pt.get("price") or 0), "stock": pt.get("dispTot", 10),
                    "ref": pt.get("explodedViewRef"), "view_name": pt.get("_view_name"),
                    "suggested": pt.get("suggested", False),
                    "serial": pt.get("serial"), "barcode": pt.get("barcode"),
                } for pt in prod_parts]
            }

            all_products.append(prod_entry)
            cat_entries.append(prod_entry)
            scraped_ids.add(str(prod_id))

            if idx % 25 == 0 or idx == len(new_products):
                elapsed = time.time() - start
                rate = len(scraped_ids) / elapsed
                print(f"    [{idx}/{len(new_products)}] {prod_name}: {len(prod_parts)} parts | {rate:.1f} prods/s")

        category_map[cat_name] = cat_entries
        save_progress(category_map, all_products, all_raw_parts, downloaded_images)
        print(f"  [SAVED] Total: {len(all_products)} products, {len(all_raw_parts)} parts")

    elapsed = time.time() - start
    save_progress(category_map, all_products, all_raw_parts, downloaded_images)

    print(f"\n{'='*65}")
    print(f"  [DONE] Complete in {elapsed:.1f}s")
    print(f"  Total Products: {len(all_products)}")
    print(f"  Total Parts:    {len(all_raw_parts)}")
    print(f"{'='*65}")


if __name__ == "__main__":
    asyncio.run(main())
