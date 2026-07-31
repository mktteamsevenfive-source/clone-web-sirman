"""
export_directly_from_supabase.py
=================================
Fetches ALL live data DIRECTLY from Supabase Cloud via REST API (with pagination)
and exports into clean CSV files in exports/:
- exports/supabase_categories.csv
- exports/supabase_products.csv
- exports/supabase_parts.csv
"""
import sys, requests, csv, time
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
EXPORT_DIR   = PROJECT_ROOT / "exports"
EXPORT_DIR.mkdir(exist_ok=True)

SUPABASE_URL     = "https://ofrerwyoasklgsejlbzr.supabase.co"
SUPABASE_SERVICE = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9mcmVyd3lvYXNrbGdzZWpsYnpyIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NTM2NjY1NSwiZXhwIjoyMTAwOTQyNjU1fQ.shN-wvqCOZi1GtPO3rwCHF51OQ0hf23E_GVn9bt3bHQ"
HEADERS = {
    "apikey": SUPABASE_SERVICE,
    "Authorization": f"Bearer {SUPABASE_SERVICE}",
    "Content-Type": "application/json"
}

def fetch_all_paginated(endpoint, select="*", order_by="id"):
    """Fetch all rows from Supabase bypassing 1000 row limit"""
    all_data = []
    page = 0
    PAGE_SIZE = 1000
    while True:
        from_row = page * PAGE_SIZE
        to_row = from_row + PAGE_SIZE - 1
        url = f"{SUPABASE_URL}/rest/v1/{endpoint}?select={select}&order={order_by}"
        r = requests.get(url, headers={**HEADERS, "Range": f"{from_row}-{to_row}"}, timeout=30)
        if r.status_code not in (200, 206):
            print(f"  [ERR] HTTP {r.status_code}: {r.text[:100]}")
            break
        batch = r.json()
        if not batch:
            break
        all_data.extend(batch)
        if len(batch) < PAGE_SIZE:
            break
        page += 1
        if page % 10 == 0:
            print(f"  Fetched {len(all_data):,} rows from '{endpoint}'...")
    return all_data

print("=== FETCHING DIRECTLY FROM SUPABASE CLOUD ===\n")

# 1. Fetch Categories
print("[1/3] Fetching Categories from Supabase...")
cats = fetch_all_paginated("categories", order_by="name")
print(f"      Loaded {len(cats)} categories")

cat_file = EXPORT_DIR / "supabase_categories.csv"
with open(cat_file, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["Category ID", "Category Name", "Product Count"])
    for c in cats:
        writer.writerow([c.get("id"), c.get("name"), c.get("count")])
print(f"      [OK] Saved to -> {cat_file.name}")

# 2. Fetch Products
print("\n[2/3] Fetching Products from Supabase...")
prods = fetch_all_paginated("products", order_by="id")
print(f"      Loaded {len(prods):,} products")

# Create product lookup map: id -> (model, category_name)
prod_map = {p["id"]: (p.get("model") or "", p.get("category_name") or "") for p in prods}

prod_file = EXPORT_DIR / "supabase_products.csv"
with open(prod_file, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["Product ID", "Code", "Model Name", "Serial", "Category Slug", "Category Name", "Description", "PDF Name", "Parts Count"])
    for p in prods:
        writer.writerow([
            p.get("id"),
            p.get("code"),
            p.get("model"),
            p.get("serial"),
            p.get("category_id"),
            p.get("category_name"),
            p.get("description"),
            p.get("pdf_name"),
            p.get("parts_count")
        ])
print(f"      [OK] Saved to -> {prod_file.name}")

# 3. Fetch Parts
print("\n[3/3] Fetching Parts from Supabase...")
start_time = time.time()
parts = fetch_all_paginated("parts", order_by="id")
print(f"      Loaded {len(parts):,} parts from Supabase in {time.time()-start_time:.1f}s")

parts_file = EXPORT_DIR / "supabase_parts.csv"
with open(parts_file, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["Product ID", "Product Model", "Category", "Part Code", "Part Name", "Price", "Stock", "Ref Position", "Exploded View Name"])
    for pt in parts:
        pid = pt.get("product_id")
        pmodel, pcat = prod_map.get(pid, ("", ""))
        writer.writerow([
            pid,
            pmodel,
            pcat,
            pt.get("code"),
            pt.get("name"),
            pt.get("price"),
            pt.get("stock"),
            pt.get("ref"),
            pt.get("view_name")
        ])
print(f"      [OK] Saved to -> {parts_file.name}")

print("\n🎉 ALL DIRECT SUPABASE CLOUD EXPORTS COMPLETED!")
