import json
import requests
import sys
import time
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

SUPABASE_URL = "https://ofrerwyoasklgsejlbzr.supabase.co"
SUPABASE_SERVICE = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9mcmVyd3lvYXNrbGdzZWpsYnpyIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NTM2NjY1NSwiZXhwIjoyMTAwOTQyNjU1fQ.shN-wvqCOZi1GtPO3rwCHF51OQ0hf23E_GVn9bt3bHQ"

SUPABASE_HEADERS = {
    "apikey": SUPABASE_SERVICE,
    "Authorization": f"Bearer {SUPABASE_SERVICE}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates"
}

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
HEADERS_FILE = ROOT_DIR / "sirman_headers.json"
API_BASE = "https://api-service.sirman.com"

def get_sirman_session():
    if not HEADERS_FILE.exists():
        print(f"[ERROR] {HEADERS_FILE.name} not found!")
        return None
    with open(HEADERS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    hdrs = data.get("headers", {})
    cookies = data.get("cookies", [])
    
    clean_hdrs = {k: v for k, v in hdrs.items() if not k.startswith(":")}
    session = requests.Session()
    session.headers.update(clean_hdrs)
    cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies if 'name' in c and 'value' in c)
    if cookie_str:
        session.headers["cookie"] = cookie_str
    return session

def fetch_all_supabase_products():
    print("[SUPABASE] Fetching all products list...")
    url = f"{SUPABASE_URL}/rest/v1/products?select=id,code,model,pdf_name,parts_count"
    all_prods = []
    page = 0
    limit = 1000
    while True:
        headers = {**SUPABASE_HEADERS, "Range": f"{page*limit}-{(page+1)*limit-1}"}
        r = requests.get(url, headers=headers)
        if r.status_code not in (200, 206):
            break
        data = r.json()
        if not data:
            break
        all_prods.extend(data)
        if len(data) < limit:
            break
        page += 1
    print(f"[SUPABASE] Total products in DB: {len(all_prods)}")
    return all_prods

def fetch_products_with_existing_parts():
    print("[SUPABASE] Finding product IDs that already have parts in DB...")
    url = f"{SUPABASE_URL}/rest/v1/parts?select=product_id"
    prod_ids = set()
    page = 0
    limit = 5000
    while True:
        headers = {**SUPABASE_HEADERS, "Range": f"{page*limit}-{(page+1)*limit-1}"}
        r = requests.get(url, headers=headers)
        if r.status_code not in (200, 206):
            break
        data = r.json()
        if not data:
            break
        for row in data:
            if row.get("product_id"):
                prod_ids.add(row["product_id"])
        if len(data) < limit:
            break
        page += 1
    print(f"[SUPABASE] Products WITH parts in DB: {len(prod_ids)}")
    return prod_ids

def main():
    print("=" * 65)
    print("  PHASE 2: Fetch Missing Parts from Sirman API & Sync to Supabase")
    print("=" * 65)

    all_prods = fetch_all_supabase_products()
    prods_with_parts = fetch_products_with_existing_parts()

    missing_prods = [p for p in all_prods if p["id"] not in prods_with_parts]
    print(f"[INFO] Found {len(missing_prods)} products WITHOUT parts in Supabase.")

    if not missing_prods:
        print("[SUCCESS] All products already have parts in Supabase!")
        return

    sirman_session = get_sirman_session()
    if not sirman_session:
        print("[ERROR] Cannot proceed without Sirman session.")
        return

    # Check session validity
    test_r = sirman_session.get(f"{API_BASE}/service-dwh/categories", timeout=10)
    if test_r.status_code != 200:
        print(f"[WARN] Sirman API test failed HTTP {test_r.status_code}: {test_r.text[:100]}")
        print("Please ensure fresh login session token.")
        return
    print("[INFO] Sirman API session active!")

    total_missing = len(missing_prods)
    uploaded_total_parts = 0

    for idx, prod in enumerate(missing_prods, 1):
        p_id = prod["id"]
        p_model = prod["model"]
        
        views_url = f"{API_BASE}/service-dwh/products/{p_id}/exploded-views"
        try:
            r = sirman_session.get(views_url, timeout=10)
            if r.status_code != 200:
                print(f"[{idx}/{total_missing}] Prod {p_id} ('{p_model[:30]}'): Views HTTP {r.status_code}")
                continue
            views = r.json() or []
        except Exception as e:
            print(f"[{idx}/{total_missing}] Prod {p_id} error fetching views: {e}")
            continue

        prod_parts = []
        for v in views:
            if not isinstance(v, dict):
                continue
            v_id = v.get("id")
            v_name = v.get("name") or v.get("code") or ""
            if not v_id:
                continue

            parts_url = f"{API_BASE}/service-dwh/products/{p_id}/exploded-views/{v_id}/parts"
            try:
                p_res = sirman_session.get(parts_url, timeout=10)
                if p_res.status_code == 200:
                    pts = p_res.json() or []
                    for pt in pts:
                        if not isinstance(pt, dict):
                            continue
                        pt_code = str(pt.get("code") or pt.get("partCode") or pt.get("id") or "").strip()
                        if not pt_code:
                            continue
                        pt_i18n = pt.get("i18n") or {}
                        pt_name = pt_i18n.get("en") or pt_i18n.get("it") or pt.get("description") or pt.get("name") or "Part"
                        
                        prod_parts.append({
                            "product_id": p_id,
                            "code": pt_code,
                            "name": str(pt_name).strip(),
                            "price": float(pt.get("price") or 0.0),
                            "stock": int(pt.get("availability") or pt.get("dispTot") or pt.get("stock") or 0),
                            "ref": str(pt.get("position") or pt.get("ref") or pt.get("explodedViewRef") or "").strip(),
                            "view_name": str(v_name).strip()
                        })
            except Exception as e:
                print(f"  [ERR parts] Prod {p_id} view {v_id}: {e}")

        if prod_parts:
            # Upload parts for this product to Supabase
            up_url = f"{SUPABASE_URL}/rest/v1/parts"
            up_r = requests.post(up_url, headers=SUPABASE_HEADERS, json=prod_parts, timeout=30)
            if up_r.status_code in (200, 201):
                uploaded_total_parts += len(prod_parts)
                print(f"[{idx}/{total_missing}] Prod {p_id} ('{p_model[:30]}'): +{len(prod_parts)} parts uploaded OK!")
                
                # Update parts_count in products table
                patch_url = f"{SUPABASE_URL}/rest/v1/products?id=eq.{p_id}"
                requests.patch(patch_url, headers=SUPABASE_HEADERS, json={"parts_count": len(prod_parts)})
            else:
                print(f"[{idx}/{total_missing}] Prod {p_id} upload FAIL HTTP {up_r.status_code}: {up_r.text[:80]}")
        else:
            print(f"[{idx}/{total_missing}] Prod {p_id} ('{p_model[:30]}'): 0 parts found on Sirman")

    print(f"\n{'='*65}")
    print(f"  [SUCCESS] Phase 2 Complete!")
    print(f"  Total new parts fetched & uploaded: {uploaded_total_parts}")
    print(f"{'='*65}")

if __name__ == "__main__":
    main()
