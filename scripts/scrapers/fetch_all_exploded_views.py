"""
fetch_all_exploded_views.py
============================
Scrapes all 4,052 products for multi-diagram views (Table 1, Table 2...)
using working sirman_headers.json and saves public/product_views.json.
Uploads public/product_views.json to Supabase Storage bucket 'diagram_hotspots'.
"""
import json
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
OUTPUT_FILE = ROOT_DIR / "public" / "product_views.json"
HEADERS_FILE = ROOT_DIR / "sirman_headers.json"

SUPABASE_URL     = "https://ofrerwyoasklgsejlbzr.supabase.co"
SUPABASE_SERVICE = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9mcmVyd3lvYXNrbGdzZWpsYnpyIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NTM2NjY1NSwiZXhwIjoyMTAwOTQyNjU1fQ.shN-wvqCOZi1GtPO3rwCHF51OQ0hf23E_GVn9bt3bHQ"
SUP_HEADERS = {"apikey": SUPABASE_SERVICE, "Authorization": f"Bearer {SUPABASE_SERVICE}"}

def fetch_product_views_worker(prod, session):
    pid = prod["id"]
    try:
        r = session.get(f"https://api-service.sirman.com/service-dwh/products/{pid}/exploded-views", timeout=10)
        if r.status_code == 200:
            views = r.json() or []
            if views:
                cleaned = []
                for v in views:
                    cleaned.append({
                        "id": v.get("id"),
                        "order": v.get("order"),
                        "name": v.get("name"),
                        "pdfName": v.get("pdfName"),
                        "type": v.get("type")
                    })
                return str(pid), cleaned
    except Exception:
        pass
    return str(pid), []

def main():
    print("=" * 65)
    print("  SCRAPING ALL MULTI-DIAGRAM VIEWS FOR 4,052 PRODUCTS")
    print("=" * 65)

    data = json.load(open(HEADERS_FILE, encoding="utf-8"))
    hdrs = data.get("headers", {})
    cookies = data.get("cookies", [])

    session = requests.Session()
    session.headers.update(hdrs)
    if cookies:
        session.headers["cookie"] = "; ".join(f"{c['name']}={c['value']}" for c in cookies)

    # 1. Fetch all products from Supabase DB
    print("[1] Fetching all products from Supabase DB...")
    products = []
    offset = 0
    while True:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/products?select=id,code,model,pdf_name&limit=1000&offset={offset}", headers=SUP_HEADERS)
        batch = r.json()
        if not batch:
            break
        products.extend(batch)
        if len(batch) < 1000:
            break
        offset += 1000

    print(f"  Fetched {len(products)} total products from Supabase DB")

    product_views_map = {}
    multi_count = 0

    print("[2] Extracting exploded views from Sirman API (15 workers)...")
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = {executor.submit(fetch_product_views_worker, p, session): p for p in products}
        completed = 0
        for future in as_completed(futures):
            completed += 1
            pid_str, views = future.result()
            if views:
                product_views_map[pid_str] = views
                if len(views) > 1:
                    multi_count += 1

            if completed % 500 == 0 or completed == len(products):
                print(f"  Processed {completed} / {len(products)} products... (Found {len(product_views_map)} with views, {multi_count} with >1 table)")

    print(f"\n[3] Extraction Complete!")
    print(f"  Total Products Processed: {len(products)}")
    print(f"  Products with Diagram Views: {len(product_views_map)}")
    print(f"  Products with MULTIPLE Diagram Views (>1): {multi_count}")

    # Write local public/product_views.json
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(product_views_map, f, indent=2, ensure_ascii=False)
    print(f"  Saved local index to {OUTPUT_FILE}")

    # Upload to Supabase Storage
    print("\n[4] Uploading product_views.json to Supabase Storage...")
    up_url = f"{SUPABASE_URL}/storage/v1/object/diagram_hotspots/product_views.json"
    headers = {**SUP_HEADERS, "Content-Type": "application/json", "x-upsert": "true"}
    r = requests.post(up_url, headers=headers, data=json.dumps(product_views_map).encode('utf-8'))
    print(f"  [SUPABASE UPLOAD STATUS] product_views.json: {r.status_code}")

if __name__ == "__main__":
    main()
