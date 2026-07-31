"""
upload_to_supabase.py - Upload Sirman catalog data to Supabase
==============================================================
Reads from sirman_catalog_data.json + sirman_parts.json
Maps numeric category IDs to Supabase category slug IDs.
Uploads all products (829) and parts (61,130) to Supabase (upsert).
Credentials are hardcoded from .env.local
"""

import json
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "requests"], check=True)
    import requests

# ── Credentials (hardcoded) ──────────────────────────────────────────────────
SUPABASE_URL     = "https://ofrerwyoasklgsejlbzr.supabase.co"
SUPABASE_SERVICE = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9mcmVyd3lvYXNrbGdzZWpsYnpyIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NTM2NjY1NSwiZXhwIjoyMTAwOTQyNjU1fQ.shN-wvqCOZi1GtPO3rwCHF51OQ0hf23E_GVn9bt3bHQ"

HEADERS = {
    "apikey": SUPABASE_SERVICE,
    "Authorization": f"Bearer {SUPABASE_SERVICE}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates",  # upsert - skip duplicates
}

BASE_DIR     = Path(__file__).parent
CATALOG_FILE = BASE_DIR / "sirman_catalog_data.json"
PARTS_FILE   = BASE_DIR / "sirman_parts.json"

BATCH_SIZE = 200  # rows per API call


def fetch_category_map() -> dict[str, str]:
    """Fetch Categories from Supabase to build map: sirman_id (str) -> category slug id."""
    url = f"{SUPABASE_URL}/rest/v1/categories?select=id,sirman_id"
    r = requests.get(url, headers=HEADERS, timeout=15)
    if r.status_code == 200:
        return {str(c["sirman_id"]): c["id"] for c in r.json() if "sirman_id" in c and c["sirman_id"]}
    print(f"[WARN] Failed to fetch categories: HTTP {r.status_code}")
    return {}


def upsert_batch(table: str, rows: list) -> bool:
    """Upsert a batch of rows into a Supabase table."""
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    r = requests.post(url, headers=HEADERS, json=rows, timeout=30)
    if r.status_code in (200, 201):
        return True
    print(f"  [WARN] {table} batch HTTP {r.status_code}: {r.text[:120]}")
    return False


def upload_table(table: str, rows: list, id_field: str = "id"):
    """Upload all rows in batches with progress."""
    total = len(rows)
    if total == 0:
        print(f"  [SKIP] No rows for {table}")
        return

    print(f"\n[Upload] {table}: {total} rows in batches of {BATCH_SIZE}...")
    success = 0
    start = time.time()

    for i in range(0, total, BATCH_SIZE):
        batch = rows[i:i + BATCH_SIZE]
        if upsert_batch(table, batch):
            success += len(batch)
        done = min(i + BATCH_SIZE, total)
        elapsed = time.time() - start
        rate = done / elapsed if elapsed > 0 else 0
        print(f"  [{done}/{total}] OK {success} uploaded | {rate:.0f} rows/s")

    print(f"  Done: {success}/{total} rows uploaded to '{table}'")


def main():
    print("=" * 65)
    print("  SUPABASE UPLOAD - Sirman Catalog Data")
    print("=" * 65)

    # 1. Fetch category map
    cat_map = fetch_category_map()
    print(f"[INFO] Loaded category mapping for {len(cat_map)} categories from Supabase")

    # 2. Load catalog products
    if not CATALOG_FILE.exists():
        print(f"[ERROR] {CATALOG_FILE.name} not found. Run scrape_with_browser.py first!")
        sys.exit(1)

    catalog = json.load(open(CATALOG_FILE, encoding="utf-8"))
    all_products = catalog.get("products", [])
    print(f"[INFO] Loaded {len(all_products)} products from {CATALOG_FILE.name}")

    # 3. Load parts
    if not PARTS_FILE.exists():
        print(f"[ERROR] {PARTS_FILE.name} not found. Run scrape_with_browser.py first!")
        sys.exit(1)

    parts_data = json.load(open(PARTS_FILE, encoding="utf-8"))
    all_raw_parts = parts_data.get("all_parts", [])
    print(f"[INFO] Loaded {len(all_raw_parts)} raw parts from {PARTS_FILE.name}")

    # ── Prepare products table rows ──────────────────────────────────────────
    product_rows = []
    category_counts = {}

    for p in all_products:
        raw_cat_id = str(p.get("category_id") or "")
        slug_cat_id = cat_map.get(raw_cat_id, raw_cat_id)

        product_rows.append({
            "id": p.get("id"),
            "code": p.get("code") or "",
            "model": p.get("model") or "",
            "serial": p.get("serial") or "",
            "category_id": slug_cat_id,
            "category_name": p.get("category_name") or "",
            "description": p.get("description") or "",
            "pdf_name": p.get("pdf_name") or "",
            "parts_count": p.get("parts_count") or 0,
        })
        category_counts[slug_cat_id] = category_counts.get(slug_cat_id, 0) + 1

    # ── Prepare parts table rows ─────────────────────────────────────────────
    seen_part_keys = set()
    parts_rows = []
    for pt in all_raw_parts:
        pt_id = pt.get("id") or pt.get("code")
        prod_id = pt.get("_product_id")
        if not pt_id or not prod_id:
            continue

        key = f"{pt_id}:{prod_id}"
        if key in seen_part_keys:
            continue
        seen_part_keys.add(key)

        parts_rows.append({
            "product_id": prod_id,
            "code": str(pt_id),
            "name": pt.get("name") or "",
            "price": float(pt.get("price") or 0),
            "stock": int(pt.get("dispTot") or pt.get("stock") or 0),
            "ref": pt.get("explodedViewRef") or pt.get("ref") or "",
            "view_name": pt.get("_view_name") or pt.get("view_name") or "",
        })

    # Filter out parts whose product_id doesn't exist in the uploaded products
    valid_product_ids = {p["id"] for p in product_rows if p.get("id")}
    parts_rows_filtered = [r for r in parts_rows if r["product_id"] in valid_product_ids]
    skipped_parts = len(parts_rows) - len(parts_rows_filtered)

    if skipped_parts > 0:
        print(f"[INFO] Skipping {skipped_parts} parts with unknown product_id")
    print(f"[INFO] Prepared {len(product_rows)} products and {len(parts_rows_filtered)} parts for upload")

    # ── Upload Products ──────────────────────────────────────────────────────
    upload_table("products", product_rows)

    # ── Upload Parts ─────────────────────────────────────────────────────────
    upload_table("parts", parts_rows_filtered)

    # ── Update Category Counts ───────────────────────────────────────────────
    print("\n[INFO] Updating product counts in categories table...")
    for cat_slug, count in category_counts.items():
        url = f"{SUPABASE_URL}/rest/v1/categories?id=eq.{cat_slug}"
        requests.patch(url, headers=HEADERS, json={"count": count})

    print(f"\n{'='*65}")
    print(f"  [SUCCESS] Upload complete!")
    print(f"  Products uploaded: {len(product_rows)}")
    print(f"  Parts uploaded:    {len(parts_rows_filtered)}")
    print(f"{'='*65}")


if __name__ == "__main__":
    main()
