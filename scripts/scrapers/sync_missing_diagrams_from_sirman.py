import json, time, requests
from concurrent.futures import ThreadPoolExecutor, as_completed

SUPABASE_URL = "https://ofrerwyoasklgsejlbzr.supabase.co"
SUPABASE_SERVICE = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9mcmVyd3lvYXNrbGdzZWpsYnpyIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NTM2NjY1NSwiZXhwIjoyMTAwOTQyNjU1fQ.shN-wvqCOZi1GtPO3rwCHF51OQ0hf23E_GVn9bt3bHQ"

SUP_HEADERS = {
    "apikey": SUPABASE_SERVICE,
    "Authorization": f"Bearer {SUPABASE_SERVICE}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates"
}

API_BASE = "https://api-service.sirman.com"

# Load Sirman Bearer headers
hd_data = json.load(open("sirman_headers.json", encoding="utf-8"))
SIRMAN_HEADERS = hd_data.get("headers", {})

def fetch_product_diagram_and_parts(prod):
    pid = prod['id']
    session = requests.Session()
    session.headers.update(SIRMAN_HEADERS)

    try:
        r = session.get(f"{API_BASE}/service-dwh/products/{pid}/exploded-views", timeout=12)
        if r.status_code != 200:
            return pid, [], "", "", f"HTTP {r.status_code}"
        views = r.json() or []
    except Exception as e:
        return pid, [], "", "", f"Error: {e}"

    if not views or not isinstance(views, list):
        return pid, [], "", "", "No views"

    main_pdf = ""
    main_view_id = ""

    for v in views:
        if not isinstance(v, dict):
            continue
        v_id = v.get("id")
        v_pdf = v.get("pdfName") or v.get("code") or v.get("fileName")
        if not main_view_id and v_id:
            main_view_id = str(v_id)
        if not main_pdf and v_pdf:
            main_pdf = str(v_pdf)

    # Fetch parts for main view
    parts = []
    for v in views[:2]: # Fetch first 2 views max
        v_id = v.get("id")
        v_name = v.get("name", "")
        if not v_id:
            continue
        try:
            pr = session.get(f"{API_BASE}/service-dwh/products/{pid}/exploded-views/{v_id}/parts", timeout=12)
            if pr.status_code == 200:
                pts = pr.json() or []
                for pt in pts:
                    if isinstance(pt, dict):
                        pt_code = pt.get("code") or pt.get("partCode") or f"P-{pt.get('id','')}"
                        pt_i18n = pt.get("i18n") or {}
                        pt_name = pt_i18n.get("en") or pt.get("description") or pt.get("name") or "Part"
                        parts.append({
                            "product_id": pid,
                            "code": str(pt_code),
                            "name": str(pt_name),
                            "price": float(pt.get("price") or 0.0),
                            "stock": int(pt.get("availability") or 0),
                            "ref": str(pt.get("position") or pt.get("ref") or ""),
                            "view_name": str(v_name)
                        })
        except Exception:
            pass

    return pid, parts, main_pdf, main_view_id, "OK"

def main():
    print("=== SYNCING MISSING DIAGRAMS FROM SIRMAN API TO SUPABASE ===")

    # Fetch products missing pdf_name
    prods = []
    offset = 0
    while True:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/products?select=id,code,model,pdf_name,exploded_view_id&limit=1000&offset={offset}", headers=SUP_HEADERS)
        batch = r.json()
        if not batch:
            break
        prods.extend(batch)
        if len(batch) < 1000:
            break
        offset += 1000

    missing_prods = [p for p in prods if not p.get('pdf_name')]
    print(f"Total products in DB: {len(prods):,}")
    print(f"Products missing diagram (pdf_name): {len(missing_prods):,}")

    if not missing_prods:
        print("🎉 ALL PRODUCTS ALREADY HAVE DIAGRAMS IN SUPABASE!")
        return

    start_time = time.time()
    updated_prods = 0
    parts_added = 0
    processed = 0

    WORKERS = 10
    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = {executor.submit(fetch_product_diagram_and_parts, p): p for p in missing_prods}

        for future in as_completed(futures):
            p = futures[future]
            processed += 1
            pid, parts, main_pdf, main_view_id, status = future.result()

            if main_pdf or main_view_id:
                # Update product in Supabase
                update_data = {
                    "pdf_name": main_pdf,
                    "exploded_view_id": main_view_id,
                    "parts_count": len(parts) if parts else p.get("parts_count", 0)
                }
                requests.patch(f"{SUPABASE_URL}/rest/v1/products?id=eq.{pid}", headers=SUP_HEADERS, json=update_data)
                updated_prods += 1

                # If parts found, insert unique parts
                if parts:
                    unique_map = {}
                    for pt in parts:
                        key = (pt['product_id'], pt['code'], pt['ref'])
                        if key not in unique_map:
                            unique_map[key] = pt
                    unique_parts = list(unique_map.values())
                    requests.post(f"{SUPABASE_URL}/rest/v1/parts", headers=SUP_HEADERS, json=unique_parts)
                    parts_added += len(unique_parts)

                print(f"  [{processed}/{len(missing_prods)}] Product {pid} ('{p['model'][:30]}') -> PDF: '{main_pdf}', Parts: {len(parts)}")
            else:
                print(f"  [{processed}/{len(missing_prods)}] Product {pid} ('{p['model'][:30]}') -> No diagram on Sirman ({status})")

    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print(f"🎉 SYNC COMPLETED IN {elapsed:.1f}s!")
    print(f"   Updated Diagrams for Products: {updated_prods:,}")
    print(f"   Parts Added: {parts_added:,}")
    print("=" * 60)

if __name__ == "__main__":
    main()
