import csv
import requests
import sys

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

SUPABASE_URL = "https://ofrerwyoasklgsejlbzr.supabase.co"
SUPABASE_SERVICE = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9mcmVyd3lvYXNrbGdzZWpsYnpyIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NTM2NjY1NSwiZXhwIjoyMTAwOTQyNjU1fQ.shN-wvqCOZi1GtPO3rwCHF51OQ0hf23E_GVn9bt3bHQ"

SUPABASE_HEADERS = {
    "apikey": SUPABASE_SERVICE,
    "Authorization": f"Bearer {SUPABASE_SERVICE}",
    "Content-Type": "application/json",
}

OUTPUT_FILE = "u:/25.WEBSITE/clone web sirman/clone-web-sirman/sirman_parts_export.csv"

def main():
    print(f"[INFO] Exporting parts from Supabase to {OUTPUT_FILE}...")
    
    # Get total count first for progress reporting
    print("[INFO] Fetching total parts count...")
    count_headers = {**SUPABASE_HEADERS, "Prefer": "count=exact"}
    r = requests.get(f"{SUPABASE_URL}/rest/v1/parts?select=id", headers=count_headers, timeout=30)
    
    if r.status_code not in (200, 206):
        print(f"[ERROR] Failed to get parts: HTTP {r.status_code}")
        print(r.text)
        return
        
    # The count is returned in the 'Content-Range' header, e.g., '0-9/455780'
    content_range = r.headers.get("Content-Range", "")
    total_count_str = content_range.split('/')[-1] if '/' in content_range else "?"
    total_count = int(total_count_str) if total_count_str.isdigit() else 0
    print(f"[INFO] Expected total parts: {total_count}")

    page = 0
    limit = 1000
    total_fetched = 0
    
    # We'll select specific columns to avoid pulling massive payloads if not needed,
    # or just select all. Let's select common fields.
    columns = "id,product_id,code,name,price,stock,ref,view_name,created_at,products(category_id)"
    
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        # Write header
        writer.writerow(["id", "product_id", "code", "name", "price", "stock", "ref", "view_name", "created_at", "category"])
        
        while True:
            url = f"{SUPABASE_URL}/rest/v1/parts?select={columns}"
            headers = {**SUPABASE_HEADERS, "Range": f"{page*limit}-{(page+1)*limit-1}"}
            
            try:
                res = requests.get(url, headers=headers, timeout=60)
            except Exception as e:
                print(f"[ERROR] Request failed on page {page}: {e}")
                break
                
            if res.status_code not in (200, 206):
                print(f"[ERROR] Fetch failed with HTTP {res.status_code}: {res.text[:100]}")
                break
                
            data = res.json()
            if not data:
                break
                
            for row in data:
                category = ""
                products_obj = row.get("products")
                if products_obj and isinstance(products_obj, dict):
                    category = products_obj.get("category_id", "")
                    
                writer.writerow([
                    row.get('id', ''),
                    row.get('product_id', ''),
                    row.get('code', ''),
                    row.get('name', ''),
                    row.get('price', ''),
                    row.get('stock', ''),
                    row.get('ref', ''),
                    row.get('view_name', ''),
                    row.get('created_at', ''),
                    category
                ])
                
            total_fetched += len(data)
            print(f"[INFO] Fetched {total_fetched}/{total_count} parts...")
            
            if len(data) < limit:
                break
            page += 1
            
    print(f"[SUCCESS] Exported {total_fetched} parts to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
