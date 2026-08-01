import requests, time
from concurrent.futures import ThreadPoolExecutor, as_completed

SUPABASE_URL = "https://ofrerwyoasklgsejlbzr.supabase.co"
SUPABASE_SERVICE = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9mcmVyd3lvYXNrbGdzZWpsYnpyIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NTM2NjY1NSwiZXhwIjoyMTAwOTQyNjU1fQ.shN-wvqCOZi1GtPO3rwCHF51OQ0hf23E_GVn9bt3bHQ"

HEADERS = {
    "apikey": SUPABASE_SERVICE,
    "Authorization": f"Bearer {SUPABASE_SERVICE}",
    "Content-Type": "application/json"
}

def get_all_product_ids():
    print("[1] Fetching all product IDs from Supabase...")
    prods = []
    page = 0
    limit = 1000
    while True:
        r = requests.get(
            f"{SUPABASE_URL}/rest/v1/products?select=id&order=id.asc&offset={page*limit}&limit={limit}",
            headers=HEADERS,
            timeout=30
        )
        data = r.json()
        if not data:
            break
        prods.extend([p['id'] for p in data])
        if len(data) < limit:
            break
        page += 1
    print(f"Total products fetched: {len(prods):,}")
    return prods

def clean_product_duplicates(pid):
    r = requests.get(f"{SUPABASE_URL}/rest/v1/parts?product_id=eq.{pid}", headers=HEADERS, timeout=30)
    if r.status_code != 200:
        return pid, 0, 0
    parts = r.json()
    if not parts:
        return pid, 0, 0

    seen = set()
    to_delete = []

    for p in parts:
        key = (p['product_id'], str(p.get('code', '')).strip(), str(p.get('ref', '') or '').strip())
        if key in seen:
            to_delete.append(p['id'])
        else:
            seen.add(key)

    if to_delete:
        for i in range(0, len(to_delete), 100):
            batch = to_delete[i:i+100]
            ids_str = ','.join(map(str, batch))
            requests.delete(f"{SUPABASE_URL}/rest/v1/parts?id=in.({ids_str})", headers=HEADERS, timeout=30)

    return pid, len(parts), len(to_delete)

def main():
    print("=== SUPABASE PARTS DEDUPLICATION UTILITY ===")
    start_time = time.time()
    
    # Get total count before
    r_cnt = requests.get(f"{SUPABASE_URL}/rest/v1/parts?select=count", headers={**HEADERS, "Prefer": "count=exact"})
    total_before = r_cnt.headers.get("content-range", "").split("/")[-1]
    print(f"Total rows in parts table BEFORE: {total_before}")

    product_ids = get_all_product_ids()

    total_deleted = 0
    processed = 0

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(clean_product_duplicates, pid): pid for pid in product_ids}
        for future in as_completed(futures):
            pid, total, deleted = future.result()
            total_deleted += deleted
            processed += 1
            if processed % 500 == 0 or processed == len(product_ids):
                print(f"  Processed {processed}/{len(product_ids)} products... (Deleted {total_deleted:,} duplicates so far)")

    # Get total count after
    r_cnt_after = requests.get(f"{SUPABASE_URL}/rest/v1/parts?select=count", headers={**HEADERS, "Prefer": "count=exact"})
    total_after = r_cnt_after.headers.get("content-range", "").split("/")[-1]

    elapsed = time.time() - start_time
    print("\n=== DEDUPLICATION COMPLETED ===")
    print(f"Total rows BEFORE: {total_before}")
    print(f"Total rows AFTER : {total_after}")
    print(f"Total duplicates removed: {total_deleted:,}")
    print(f"Time taken: {elapsed:.2f} seconds")

if __name__ == "__main__":
    main()
