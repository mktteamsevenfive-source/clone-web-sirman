"""
generate_hotspot_index.py
==========================
Generates public/hotspots/index.json mapping every product pdf_name
to its direct or best-matching Hotspot JSON file.
Also uploads index.json to Supabase Storage bucket 'diagram_hotspots'.
"""
import json
import re
import requests
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
HOTSPOTS_DIR = ROOT_DIR / "public" / "hotspots"
INDEX_FILE = HOTSPOTS_DIR / "index.json"

SUPABASE_URL     = "https://ofrerwyoasklgsejlbzr.supabase.co"
SUPABASE_SERVICE = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9mcmVyd3lvYXNrbGdzZWpsYnpyIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NTM2NjY1NSwiZXhwIjoyMTAwOTQyNjU1fQ.shN-wvqCOZi1GtPO3rwCHF51OQ0hf23E_GVn9bt3bHQ"
HEADERS = {"apikey": SUPABASE_SERVICE, "Authorization": f"Bearer {SUPABASE_SERVICE}"}


def main():
    print("=" * 65)
    print("  GENERATING HOTSPOT LOOKUP INDEX (public/hotspots/index.json)")
    print("=" * 65)

    HOTSPOTS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Collect all local hotspot files
    existing_hs = {p.name.lower(): p.name for p in HOTSPOTS_DIR.glob("*.json") if p.name != "index.json"}
    print(f"[1] Local hotspot JSON files in public/hotspots/: {len(existing_hs)}")

    # 2. Fetch all products from Supabase DB
    print("[2] Fetching products from Supabase DB...")
    products = []
    offset = 0
    while True:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/products?select=id,pdf_name&limit=1000&offset={offset}", headers=HEADERS)
        batch = r.json()
        if not batch:
            break
        products.extend(batch)
        if len(batch) < 1000:
            break
        offset += 1000
    print(f"  Fetched {len(products)} products")

    # 3. Build mapping
    mapping = {}
    direct_cnt = 0
    fuzzy_cnt = 0

    for p in products:
        pdf = p.get("pdf_name", "")
        if not pdf:
            continue
        clean = re.sub(r'\.pdf$', '', pdf, flags=re.IGNORECASE).strip()
        clean_safe = clean.replace(' ', '_').lower()
        clean_lower = clean.lower()

        fn_direct = f"{clean_lower}.json"
        fn_safe = f"{clean_safe}.json"

        if fn_direct in existing_hs:
            mapping[clean] = existing_hs[fn_direct]
            direct_cnt += 1
        elif fn_safe in existing_hs:
            mapping[clean] = existing_hs[fn_safe]
            direct_cnt += 1
        else:
            # Try stripping dates and qualifiers
            short_clean = re.sub(r'_(from|until)\d+', '', clean_safe, flags=re.IGNORECASE)
            short_clean = re.sub(r'_\d{8}', '', short_clean)
            short_fn = f"{short_clean}.json"

            found = None
            if short_fn in existing_hs:
                found = existing_hs[short_fn]
            else:
                # Fuzzy token matching
                tokens = [t for t in re.split(r'[-_ ]+', clean_safe) if len(t) > 2 and not t.isdigit()]
                best_hs = None
                best_score = 0
                for hs_key, real_name in existing_hs.items():
                    score = sum(1 for t in tokens if t in hs_key)
                    if score > best_score and score >= max(2, len(tokens) - 1):
                        best_score = score
                        best_hs = real_name
                found = best_hs

            if found:
                mapping[clean] = found
                fuzzy_cnt += 1

    print(f"\n[3] Mapping Summary:")
    print(f"  Direct Matches: {direct_cnt}")
    print(f"  Fuzzy Matches:  {fuzzy_cnt}")
    print(f"  Total Mapped:   {len(mapping)} / {len(products)}")

    # Write local index.json
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)
    print(f"\n[SUCCESS] Local index saved to {INDEX_FILE}")

    # Upload index.json to Supabase Storage bucket diagram_hotspots
    up_url = f"{SUPABASE_URL}/storage/v1/object/diagram_hotspots/index.json"
    headers = {**HEADERS, "Content-Type": "application/json", "x-upsert": "true"}
    r = requests.post(up_url, headers=headers, data=json.dumps(mapping).encode('utf-8'))
    print(f"[SUPABASE UPLOAD] index.json status: {r.status_code}")


if __name__ == "__main__":
    main()
