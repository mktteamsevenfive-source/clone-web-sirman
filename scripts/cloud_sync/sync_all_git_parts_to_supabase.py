import subprocess, json, requests, time

SUPABASE_URL = "https://ofrerwyoasklgsejlbzr.supabase.co"
SUPABASE_SERVICE = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9mcmVyd3lvYXNrbGdzZWpsYnpyIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NTM2NjY1NSwiZXhwIjoyMTAwOTQyNjU1fQ.shN-wvqCOZi1GtPO3rwCHF51OQ0hf23E_GVn9bt3bHQ"

HEADERS = {
    "apikey": SUPABASE_SERVICE,
    "Authorization": f"Bearer {SUPABASE_SERVICE}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates"
}

print("=== Syncing All Catalog Parts from Git History to Supabase ===")
cmd = ["git", "cat-file", "blob", "1dc53db566ac077a41d6509f0995355faa4e70f9"]
res = subprocess.run(cmd, capture_output=True, cwd="u:\\25.WEBSITE\\clone web sirman\\clone-web-sirman")

data = json.loads(res.stdout.decode('utf-8'))
prods = data.get('products', [])

all_parts = []
seen = set()

for p in prods:
    pid = p.get('id')
    if not pid:
        continue
    pid_num = int(pid)
    for pt in p.get('parts', []):
        code = str(pt.get('code', '') or '')
        key = f"{pid_num}:{code}"
        if key in seen:
            continue
        seen.add(key)
        all_parts.append({
            "product_id": pid_num,
            "code": code,
            "name": str(pt.get('name', '') or ''),
            "price": float(pt.get('price', 0) or 0),
            "stock": int(pt.get('stock', 0) or 0),
            "ref": str(pt.get('ref', '') or ''),
            "view_name": str(pt.get('view_name', '') or '')
        })

print(f"Total parts to sync: {len(all_parts):,} rows for {len(prods)} products")

BATCH = 1000
success = 0
for i in range(0, len(all_parts), BATCH):
    batch = all_parts[i:i+BATCH]
    r = requests.post(f"{SUPABASE_URL}/rest/v1/parts", headers=HEADERS, json=batch, timeout=60)
    if r.status_code in (200, 201):
        success += len(batch)
    else:
        print(f"  [WARN] Batch {i//BATCH+1} HTTP {r.status_code}: {r.text[:80]}")

print(f"\n[SUCCESS] Uploaded {success:,} parts to Supabase!")
