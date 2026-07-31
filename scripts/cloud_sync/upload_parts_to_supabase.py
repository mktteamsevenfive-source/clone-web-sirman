"""
upload_parts_to_supabase.py
============================
Upload all parts from SQLite to Supabase (upsert - skip duplicates)
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

BATCH = 1000

print("=== UPLOADING PARTS TO SUPABASE ===")

# Load valid product IDs from Supabase
print("[1] Fetching valid product IDs from Supabase...")
valid_ids = set()
page = 0
while True:
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/products?select=id",
        headers={**HEADERS, "Range-Unit": "items", "Range": f"{page*1000}-{page*1000+999}"},
        timeout=15
    )
    batch = r.json()
    if not batch:
        break
    valid_ids.update(str(p["id"]) for p in batch)
    if len(batch) < 1000:
        break
    page += 1
print(f"    Valid product IDs in Supabase: {len(valid_ids)}")

# Load parts from SQLite
print("[2] Loading parts from SQLite...")
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()
rows = c.execute(
    "SELECT product_id, code, name, price, stock, ref, view_name FROM parts"
).fetchall()
conn.close()
print(f"    Total parts in SQLite: {len(rows)}")

# Filter valid only and deduplicate
seen = set()
parts_rows = []
for product_id, code, name, price, stock, ref, view_name in rows:
    if str(product_id) not in valid_ids:
        continue
    key = f"{product_id}:{code}"
    if key in seen:
        continue
    seen.add(key)
    parts_rows.append({
        "product_id": product_id,
        "code": str(code or ""),
        "name": str(name or ""),
        "price": float(price or 0),
        "stock": int(stock or 0),
        "ref": str(ref or ""),
        "view_name": str(view_name or ""),
    })

print(f"    Parts after deduplication: {len(parts_rows)}")

# Clear old parts then re-upload
print("[3] Clearing old parts in Supabase...")
r = requests.delete(f"{SUPABASE_URL}/rest/v1/parts?id=gt.0", headers=HEADERS, timeout=30)
print(f"    Delete response: HTTP {r.status_code}")

# Upload in batches
print(f"[4] Uploading {len(parts_rows)} parts in batches of {BATCH}...")
success = 0
start = time.time()
for i in range(0, len(parts_rows), BATCH):
    batch = parts_rows[i:i+BATCH]
    r = requests.post(f"{SUPABASE_URL}/rest/v1/parts", headers=HEADERS, json=batch, timeout=60)
    if r.status_code in (200, 201):
        success += len(batch)
    else:
        print(f"  [WARN] Batch {i//BATCH+1} HTTP {r.status_code}: {r.text[:80]}")
    done = min(i + BATCH, len(parts_rows))
    elapsed = time.time() - start
    rate = done / elapsed if elapsed > 0 else 0
    pct = (done / len(parts_rows)) * 100
    print(f"  [{done}/{len(parts_rows)}] {pct:5.1f}% | {rate:.0f} rows/s")

print(f"\n[SUCCESS] Uploaded {success}/{len(parts_rows)} parts to Supabase!")
print(f"Time: {time.time()-start:.1f}s")
