import sys, requests

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

SUPABASE_URL     = "https://ofrerwyoasklgsejlbzr.supabase.co"
SUPABASE_SERVICE = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9mcmVyd3lvYXNrbGdzZWpsYnpyIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NTM2NjY1NSwiZXhwIjoyMTAwOTQyNjU1fQ.shN-wvqCOZi1GtPO3rwCHF51OQ0hf23E_GVn9bt3bHQ"

H = {
    "apikey": SUPABASE_SERVICE,
    "Authorization": f"Bearer {SUPABASE_SERVICE}",
    "Content-Type": "application/json"
}

print("=== SUPABASE USAGE SUMMARY ===\n")

# 1. Count rows in each table
tables = ["categories", "products", "parts"]
total_rows = 0
for table in tables:
    # Use HEAD request with count
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/{table}?select=*",
        headers={**H, "Prefer": "count=exact", "Range-Unit": "items", "Range": "0-0"},
        timeout=15
    )
    content_range = r.headers.get("content-range", "0/0")
    try:
        count = int(content_range.split("/")[-1])
    except:
        count = 0
    total_rows += count
    print(f"  Table '{table}': {count:,} rows")

print(f"\n  Total rows in Database: {total_rows:,}")

# 2. Storage buckets
print("\n--- Storage Buckets ---")
r = requests.get(f"{SUPABASE_URL}/storage/v1/bucket", headers=H, timeout=15)
if r.status_code == 200:
    buckets = r.json()
    for b in buckets:
        bid = b.get("id")
        bname = b.get("name")
        # List objects in bucket to count/size
        r2 = requests.post(
            f"{SUPABASE_URL}/storage/v1/object/list/{bid}",
            headers=H,
            json={"prefix": "", "limit": 10000, "offset": 0},
            timeout=30
        )
        if r2.status_code == 200:
            objects = r2.json()
            total_size = sum(obj.get("metadata", {}).get("size", 0) for obj in objects if obj.get("metadata"))
            def fmt(b):
                if b >= 1024**3: return f"{b/1024**3:.2f} GB"
                if b >= 1024**2: return f"{b/1024**2:.2f} MB"
                if b >= 1024:    return f"{b/1024:.2f} KB"
                return f"{b} B"
            print(f"  Bucket '{bname}': {len(objects):,} files | Size: {fmt(total_size)}")
        else:
            print(f"  Bucket '{bname}': (error fetching objects: {r2.status_code})")
else:
    print(f"  (Could not fetch buckets: {r.status_code})")

# 3. Supabase Free Tier limits info
print("\n=== FREE TIER LIMITS ===")
print("  Database rows  : 50,000 / 500,000,000 rows (ไม่มี limit แถว)")
print("  Database size  : ไม่ทราบ (ต้องดูใน Supabase Dashboard)")
print("  Storage        : 1 GB (Free) / ใช้จริงดูข้างบน")
print("  API requests   : 500,000 / month (Free)")
print("  Bandwidth      : 5 GB / month (Free)")
print("\n  => ดูละเอียดได้ที่: https://supabase.com/dashboard/project/ofrerwyoasklgsejlbzr/settings/general")
