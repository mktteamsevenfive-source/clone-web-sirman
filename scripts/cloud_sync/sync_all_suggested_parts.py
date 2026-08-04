import requests, json, sys, time
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
HEADERS_FILE = PROJECT_ROOT / "sirman_headers.json"
OUTPUT_TS    = PROJECT_ROOT / "src" / "lib" / "suggested_set.ts"

if not HEADERS_FILE.exists():
    print(f"Headers file {HEADERS_FILE} does not exist!")
    sys.exit(1)

with open(HEADERS_FILE, "r", encoding="utf-8") as f:
    hdr_data = json.load(f)

headers = hdr_data.get("headers", {})

print("=== FETCHING ALL SUGGESTED PARTS FROM SIRMAN API ===")

# Fetch all products
print("[1] Fetching all products from Sirman API...")
cat_list = [4,6,7,31,5,51,52,61,2,3,27,28,18]
all_products = []

for cat_id in cat_list:
    page = 1
    while True:
        url = f"https://api-service.sirman.com/service-dwh/products?category={cat_id}&type=group&productionFilter=all&page={page}&pageSize=100&catalog=catalog"
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            data = r.json()
            items = data.get("items", [])
            if not items:
                break
            all_products.extend(items)
            if page >= data.get("totalPages", 1):
                break
            page += 1
        else:
            break

print(f"    Total products found: {len(all_products):,}")

# Fetch views and parts for each product
suggested_codes = set()

# Pre-load known suggested codes
suggested_codes.update(["IB5820700", "IB5800100", "IB5940010", "IB5940702", "IB4180710", "IB4000720"])

from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_prod_suggested(prod):
    pid = prod.get("id")
    if not pid:
        return set()
    s_codes = set()
    try:
        r_views = requests.get(f"https://api-service.sirman.com/service-dwh/products/{pid}/exploded-views", headers=headers, timeout=10)
        if r_views.status_code == 200:
            views = r_views.json()
            if isinstance(views, list):
                for v in views:
                    vid = v.get("id")
                    if vid:
                        r_parts = requests.get(f"https://api-service.sirman.com/service-dwh/products/{pid}/exploded-views/{vid}/parts", headers=headers, timeout=10)
                        if r_parts.status_code == 200:
                            parts = r_parts.json()
                            if isinstance(parts, list):
                                for pt in parts:
                                    if pt.get("suggested") is True:
                                        code = str(pt.get("id") or pt.get("code") or "")
                                        if code:
                                            s_codes.add(code)
    except Exception:
        pass
    return s_codes

print(f"[2] Fetching suggested parts across {len(all_products)} products using 20 threads...")
processed = 0
start_t = time.time()

with ThreadPoolExecutor(max_workers=20) as executor:
    futures = {executor.submit(fetch_prod_suggested, p): p for p in all_products}
    for future in as_completed(futures):
        res = future.result()
        suggested_codes.update(res)
        processed += 1
        if processed % 500 == 0 or processed == len(all_products):
            print(f"    Processed {processed}/{len(all_products)} products... (Found {len(suggested_codes)} suggested part codes)")

print(f"\n[3] Total unique suggested part codes found: {len(suggested_codes):,}")

# Save to suggested_set.ts
ts_code = f"""// Auto-generated set of all suggested spare part codes from Sirman API
export const SUGGESTED_CODES_SET = new Set<string>({json.dumps(sorted(list(suggested_codes)))});
"""

with open(OUTPUT_TS, "w", encoding="utf-8") as f:
    f.write(ts_code)

print(f"[SUCCESS] Updated {OUTPUT_TS.name} with {len(suggested_codes)} codes!")
