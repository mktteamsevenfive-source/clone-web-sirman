"""
Sirman Master Incremental Scraper
==================================
- Reads sirman_headers.json from project root
- Queries Sirman API for all categories and all products (handling full pagination)
- Skips already scraped product IDs
- Fetches exploded views, parts, pdf names
- Updates sirman_catalog_data.json, sirman_parts.json, and sirman_catalog.db
"""

import asyncio
import json
import sqlite3
import sys
import time
from pathlib import Path

try:
    import requests as req_lib
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "requests"], check=True)
    import requests as req_lib

# Paths in project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_FILE  = PROJECT_ROOT / "sirman_parts.json"
CATALOG_FILE = PROJECT_ROOT / "sirman_catalog_data.json"
HEADERS_FILE = PROJECT_ROOT / "sirman_headers.json"
DB_FILE      = PROJECT_ROOT / "sirman_catalog.db"
API_BASE     = "https://api-service.sirman.com"

def get_session():
    if not HEADERS_FILE.exists():
        print(f"[ERROR] {HEADERS_FILE.name} not found! Run refresh_auth.py first.")
        sys.exit(1)

    with open(HEADERS_FILE, encoding="utf-8") as f:
        data = json.load(f)

    hdrs = data.get("headers", {})
    cookies = data.get("cookies", [])

    session = req_lib.Session()
    clean = {k: v for k, v in hdrs.items() if not k.startswith(":")}
    session.headers.update(clean)
    cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
    if cookie_str:
        session.headers["cookie"] = cookie_str

    # Test
    r = session.get(f"{API_BASE}/service-dwh/categories", timeout=10)
    if r.status_code != 200:
        print(f"[ERROR] Session expired (HTTP {r.status_code}). Need to refresh auth!")
        sys.exit(1)
    print(f"[AUTH] Session active! ({len(r.json())} categories found)")
    return session, r.json()

def load_existing():
    existing_products = []
    scraped_ids = set()
    category_map = {}
    all_raw_parts = []

    if CATALOG_FILE.exists():
        try:
            d = json.load(open(CATALOG_FILE, encoding="utf-8"))
            existing_products = d.get("products", [])
            for p in existing_products:
                if p.get("id"):
                    scraped_ids.add(str(p["id"]))
            print(f"[RESUME] Loaded {len(existing_products)} products from {CATALOG_FILE.name}")
        except Exception as e:
            print(f"[WARN] Error loading {CATALOG_FILE.name}: {e}")

    if OUTPUT_FILE.exists():
        try:
            d = json.load(open(OUTPUT_FILE, encoding="utf-8"))
            category_map = d.get("categories", {})
            all_raw_parts = d.get("all_parts", [])
            for cname, plist in category_map.items():
                if isinstance(plist, list):
                    for p in plist:
                        if isinstance(p, dict) and p.get("id"):
                            scraped_ids.add(str(p["id"]))
            print(f"[RESUME] Loaded {len(category_map)} categories & {len(all_raw_parts)} parts from {OUTPUT_FILE.name}")
        except Exception as e:
            print(f"[WARN] Error loading {OUTPUT_FILE.name}: {e}")

    if DB_FILE.exists():
        try:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            db_ids = [str(r[0]) for r in c.execute("SELECT id FROM products").fetchall()]
            scraped_ids.update(db_ids)
            conn.close()
            print(f"[RESUME] Found {len(db_ids)} product IDs in SQLite database {DB_FILE.name}")
        except Exception:
            pass

    print(f"[RESUME TOTAL] Total unique product IDs already saved: {len(scraped_ids)} (all will be skipped)")
    return existing_products, scraped_ids, category_map, all_raw_parts

def save_progress(all_products, category_map, all_raw_parts):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "categories": category_map,
            "all_parts": all_raw_parts,
            "summary": {
                "total_categories": len(category_map),
                "total_products": len(all_products),
                "total_parts": len(all_raw_parts),
                "last_updated": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        }, f, ensure_ascii=False, indent=2)

    with open(CATALOG_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "categories": list(category_map.keys()),
            "products": all_products
        }, f, ensure_ascii=False, indent=2)

    update_sqlite_db(all_products, category_map, all_raw_parts)

def update_sqlite_db(all_products, category_map, all_raw_parts):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id TEXT PRIMARY KEY,
            sirman_id INTEGER,
            name TEXT NOT NULL,
            count INTEGER DEFAULT 0
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            code TEXT NOT NULL,
            model TEXT NOT NULL,
            serial TEXT,
            category_id TEXT,
            category_name TEXT,
            description TEXT,
            pdf_name TEXT,
            exploded_view_id TEXT,
            parts_count INTEGER DEFAULT 0
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS parts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            code TEXT NOT NULL,
            name TEXT NOT NULL,
            price REAL DEFAULT 0.0,
            stock INTEGER DEFAULT 0,
            ref TEXT,
            view_name TEXT
        )
    """)

    # Sync Categories
    for cname, items in category_map.items():
        cid = cname.lower().replace(" ", "-")
        c.execute("INSERT OR REPLACE INTO categories (id, name, count) VALUES (?, ?, ?)",
                  (cid, cname, len(items)))

    # Sync Products
    for p in all_products:
        p_id = p.get("id")
        if not p_id:
            continue
        c.execute("""
            INSERT OR REPLACE INTO products
            (id, code, model, serial, category_id, category_name, description, pdf_name, exploded_view_id, parts_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            p_id,
            p.get("code", ""),
            p.get("model") or p.get("name", ""),
            p.get("serial", ""),
            p.get("category_id", ""),
            p.get("category_name", ""),
            p.get("description", ""),
            p.get("pdf_name", ""),
            p.get("exploded_view_id", ""),
            p.get("parts_count", 0)
        ))

    # Sync Parts (clear & rebuild or replace)
    c.execute("DELETE FROM parts")
    for pt in all_raw_parts:
        c.execute("""
            INSERT INTO parts (product_id, code, name, price, stock, ref, view_name)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            pt.get("product_id"),
            pt.get("code", ""),
            pt.get("name", ""),
            pt.get("price", 0.0),
            pt.get("stock", 0),
            pt.get("ref", ""),
            pt.get("view_name", "")
        ))

    conn.commit()
    conn.close()
    print(f"[DB] Updated SQLite database {DB_FILE.name} successfully!")

import sys
import os

# Ensure stdout supports UTF-8 on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

def run_scraper():
    session, categories = get_session()
    all_products, scraped_ids, category_map, all_raw_parts = load_existing()

    start_time = time.time()
    total_new = 0

    print(f"\n[START] Starting scrape across {len(categories)} categories...")

    for idx, cat in enumerate(categories, 1):
        cid = cat.get("id")
        cname = cat.get("i18n", {}).get("en") or cat.get("name", f"Category-{cid}")
        pct = (idx / len(categories)) * 100
        filled = int(25 * idx // len(categories))
        bar = '█' * filled + '░' * (25 - filled)
        
        print(f"[{bar}] {pct:5.1f}% | Category {idx}/{len(categories)}: '{cname}' (id={cid})")

        # Page loop to fetch ALL products in this category
        cat_products = []
        page = 1
        while True:
            url = f"{API_BASE}/service-dwh/products?category={cid}&productionFilter=all&page={page}&pageSize=100"
            try:
                r = session.get(url, timeout=12)
                if r.status_code == 200:
                    data = r.json()
                    items = data.get("items", [])
                    if not items:
                        break
                    cat_products.extend(items)
                    print(f"  -> Page {page}: +{len(items)} items | Total for '{cname}': {len(cat_products)}")
                    page += 1
                else:
                    print(f"  [WARN] HTTP {r.status_code} for category {cid} page {page}")
                    break
            except Exception as e:
                print(f"  [ERR] {e}")
                break

        new_items = [p for p in cat_products if str(p.get("id", "")) not in scraped_ids]
        print(f"  Category '{cname}': Total={len(cat_products)} | Previously Scraped={len(cat_products)-len(new_items)} | New={len(new_items)}")

        if not new_items:
            print(f"  [SKIP] All items in '{cname}' already present.")
            continue

        cat_entries = list(category_map.get(cname, []))

        for n_idx, prod in enumerate(new_items, 1):
            p_id = prod.get("id")
            if not p_id:
                continue

            i18n = prod.get("i18n") or {}
            p_name = i18n.get("en") or prod.get("name", "Unknown")
            code = prod.get("code") or f"SIR-{cid}-{p_id}"
            serial = prod.get("serialNumber") or prod.get("sn") or f"SN-{p_id}"

            # Fetch exploded views
            views = []
            try:
                v_res = session.get(f"{API_BASE}/service-dwh/products/{p_id}/exploded-views", timeout=10)
                if v_res.status_code == 200:
                    views = v_res.json() or []
            except Exception as e:
                print(f"    [ERR views] {e}")

            prod_parts = []
            pdf_name = ""
            main_view_id = ""

            for v in views:
                if not isinstance(v, dict):
                    continue
                v_id = v.get("id")
                v_name = v.get("name", "")
                if not main_view_id and v_id:
                    main_view_id = str(v_id)
                v_pdf = v.get("pdfName") or v.get("code") or v.get("fileName")
                if v_pdf and not pdf_name:
                    pdf_name = v_pdf

                if not v_id:
                    continue

                # Fetch parts for this view
                try:
                    p_res = session.get(f"{API_BASE}/service-dwh/products/{p_id}/exploded-views/{v_id}/parts", timeout=10)
                    if p_res.status_code == 200:
                        pts = p_res.json() or []
                        for pt in pts:
                            if isinstance(pt, dict):
                                pt_code = pt.get("code") or pt.get("partCode") or f"P-{pt.get('id','')}"
                                pt_i18n = pt.get("i18n") or {}
                                pt_name = pt_i18n.get("en") or pt.get("description") or pt.get("name") or "Part"
                                part_obj = {
                                    "product_id": p_id,
                                    "code": pt_code,
                                    "name": pt_name,
                                    "price": pt.get("price", 0.0),
                                    "stock": pt.get("availability", 0),
                                    "ref": str(pt.get("position") or pt.get("ref") or ""),
                                    "view_name": v_name
                                }
                                prod_parts.append(part_obj)
                                all_raw_parts.append(part_obj)
                except Exception as e:
                    print(f"    [ERR parts] {e}")

            prod_entry = {
                "id": p_id,
                "code": code,
                "model": p_name,
                "serial": serial,
                "category_id": str(cid),
                "category_name": cname,
                "description": prod.get("description", ""),
                "pdf_name": pdf_name,
                "exploded_view_id": main_view_id,
                "parts_count": len(prod_parts),
                "parts": prod_parts
            }

            cat_entries.append(prod_entry)
            all_products.append(prod_entry)
            scraped_ids.add(str(p_id))
            total_new += 1

            if n_idx % 10 == 0 or n_idx == len(new_items):
                print(f"    Processed {n_idx}/{len(new_items)} new products for '{cname}' (Total new overall: {total_new})")
                category_map[cname] = cat_entries
                save_progress(all_products, category_map, all_raw_parts)

        category_map[cname] = cat_entries
        save_progress(all_products, category_map, all_raw_parts)

    elapsed = round(time.time() - start_time, 2)
    print(f"\n==================================================")
    print(f"  SCRAPE FINISHED IN {elapsed}s")
    print(f"  New products scraped: {total_new}")
    print(f"  Total products in DB: {len(all_products)}")
    print(f"  Total parts in DB: {len(all_raw_parts)}")
    print(f"==================================================")

if __name__ == "__main__":
    run_scraper()
