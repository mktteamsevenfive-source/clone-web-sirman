"""
normalize_and_upload.py
=======================
1. Normalize category names in SQLite (fix case duplicates)
2. Re-upload all products to Supabase with correct slugified category_id
"""
import sys, sqlite3, requests, time
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_FILE      = PROJECT_ROOT / "sirman_catalog.db"

SUPABASE_URL     = "https://ofrerwyoasklgsejlbzr.supabase.co"
SUPABASE_SERVICE = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9mcmVyd3lvYXNrbGdzZWpsYnpyIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NTM2NjY1NSwiZXhwIjoyMTAwOTQyNjU1fQ.shN-wvqCOZi1GtPO3rwCHF51OQ0hf23E_GVn9bt3bHQ"
HEADERS = {
    "apikey": SUPABASE_SERVICE,
    "Authorization": f"Bearer {SUPABASE_SERVICE}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates"
}

# Canonical names (Title Case)
CANONICAL = {
    "meat processors": "Meat Processors",
    "food processors": "Food Processors",
    "snack and pizza": "Snack and Pizza",
    "slicers": "Slicers",
    "bar machines": "Bar machines",
    "cooking machines": "Cooking machines",
    "packaging machines": "Packaging machines",
    "microwaves ovens": "Microwaves ovens",
    "consumables": "Consumables and accessories",
    "consumables and accessories": "Consumables and accessories",
    "ozone generators": "Ozone generators",
    "dishwashers": "Dishwashers",
    "laundry": "Laundry",
    "scales": "Scales",
    "food processor": "Food Processors",
    "meat processor": "Meat Processors",
}

def slugify(name: str) -> str:
    return name.lower().strip().replace(" ", "-").replace("&", "and")

def normalize_category(name: str) -> str:
    return CANONICAL.get(name.lower().strip(), name.strip())

print("=== STEP 1: Normalize category_name in SQLite ===")
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

rows = c.execute("SELECT id, category_name FROM products").fetchall()
updates = {}
for pid, cat_name in rows:
    normalized = normalize_category(cat_name or "")
    if normalized != cat_name:
        updates[pid] = normalized

print(f"  Products to normalize: {len(updates)}")
for pid, new_name in updates.items():
    c.execute("UPDATE products SET category_name = ?, category_id = ? WHERE id = ?",
              (new_name, slugify(new_name), pid))
conn.commit()
print(f"  [OK] Normalized {len(updates)} product category names")

# Show final count per category
print("\n=== Category Counts After Normalization ===")
rows2 = c.execute("SELECT category_name, category_id, COUNT(*) FROM products GROUP BY category_name ORDER BY COUNT(*) DESC").fetchall()
total = 0
for cname, cid, cnt in rows2:
    print(f"  [{cid}] {cname}: {cnt}")
    total += cnt
print(f"  TOTAL: {total}")
conn.close()

print("\n=== STEP 2: Re-upload normalized products to Supabase ===")

conn = sqlite3.connect(DB_FILE)
c = conn.cursor()
all_prods = c.execute(
    "SELECT id, code, model, serial, category_id, category_name, description, pdf_name, exploded_view_id, parts_count FROM products"
).fetchall()
conn.close()

# Fetch category map from Supabase
r = requests.get(f"{SUPABASE_URL}/rest/v1/categories?select=id,name,sirman_id", headers=HEADERS)
cat_map = {c["name"].lower().strip(): c["id"] for c in r.json()}
print(f"  Supabase category map loaded: {len(cat_map)} categories")

product_rows = []
for row in all_prods:
    pid, code, model, serial, cat_id, cat_name, desc, pdf_name, ev_id, parts_count = row
    # Map to supabase category slug
    sup_cat_id = cat_map.get((cat_name or "").lower().strip(), cat_id or "")
    product_rows.append({
        "id": pid,
        "code": code or "",
        "model": model or "",
        "serial": serial or "",
        "category_id": sup_cat_id,
        "category_name": cat_name or "",
        "description": desc or "",
        "pdf_name": pdf_name or "",
        "parts_count": parts_count or 0,
    })

print(f"  Total products to upsert: {len(product_rows)}")

BATCH = 500
success = 0
start = time.time()
for i in range(0, len(product_rows), BATCH):
    batch = product_rows[i:i+BATCH]
    r = requests.post(f"{SUPABASE_URL}/rest/v1/products", headers=HEADERS, json=batch, timeout=30)
    if r.status_code in (200, 201):
        success += len(batch)
    else:
        print(f"  [WARN] Batch {i//BATCH+1} HTTP {r.status_code}: {r.text[:80]}")
    done = min(i + BATCH, len(product_rows))
    pct = (done / len(product_rows)) * 100
    elapsed = time.time() - start
    rate = done / elapsed if elapsed > 0 else 0
    print(f"  [{done}/{len(product_rows)}] {pct:5.1f}% | {rate:.0f} rows/s")

print(f"\n[SUCCESS] Upserted {success}/{len(product_rows)} products to Supabase!")

# Update category counts
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()
cat_counts = c.execute("SELECT category_name, COUNT(*) FROM products GROUP BY category_name").fetchall()
conn.close()

print("\n=== STEP 3: Update category counts in Supabase ===")
for cat_name, cnt in cat_counts:
    sup_cat_id = cat_map.get((cat_name or "").lower().strip())
    if sup_cat_id:
        requests.patch(
            f"{SUPABASE_URL}/rest/v1/categories?id=eq.{sup_cat_id}",
            headers=HEADERS,
            json={"count": cnt}
        )
        print(f"  {sup_cat_id}: count={cnt}")

print("\n=== ALL DONE ===")
