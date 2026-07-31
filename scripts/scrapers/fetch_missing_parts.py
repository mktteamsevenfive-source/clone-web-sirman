"""
fetch_missing_parts.py
======================
Fast parallel fetcher for products with parts_count = 0.
1. Reads sirman_headers.json
2. Finds products in SQLite with parts_count = 0 (1,638 products)
3. Fetches exploded-views and parts via Sirman API concurrently (10 workers)
4. Saves parts into SQLite and updates products.parts_count
5. Uploads updated products and parts to Supabase
"""
import sys, json, sqlite3, time, requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_FILE      = PROJECT_ROOT / "sirman_catalog.db"
HEADERS_FILE = PROJECT_ROOT / "sirman_headers.json"
API_BASE     = "https://api-service.sirman.com"

SUPABASE_URL     = "https://ofrerwyoasklgsejlbzr.supabase.co"
SUPABASE_SERVICE = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9mcmVyd3lvYXNrbGdzZWpsYnpyIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NTM2NjY1NSwiZXhwIjoyMTAwOTQyNjU1fQ.shN-wvqCOZi1GtPO3rwCHF51OQ0hf23E_GVn9bt3bHQ"
SUP_HEADERS = {
    "apikey": SUPABASE_SERVICE,
    "Authorization": f"Bearer {SUPABASE_SERVICE}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates"
}

def get_sirman_session():
    if not HEADERS_FILE.exists():
        print("[ERROR] sirman_headers.json not found!")
        sys.exit(1)
    with open(HEADERS_FILE, encoding="utf-8") as f:
        data = json.load(f)
    session = requests.Session()
    clean = {k: v for k, v in data.get("headers", {}).items() if not k.startswith(":")}
    session.headers.update(clean)
    cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in data.get("cookies", []))
    if cookie_str:
        session.headers["cookie"] = cookie_str
    
    # Test API
    r = session.get(f"{API_BASE}/service-dwh/categories", timeout=10)
    if r.status_code != 200:
        print(f"[ERROR] Session expired (HTTP {r.status_code}). Need refresh_auth!")
        sys.exit(1)
    print(f"[AUTH OK] Sirman API active!")
    return session

def fetch_product_parts(p_id, session):
    """Fetch views & parts for a single product_id"""
    views = []
    try:
        r = session.get(f"{API_BASE}/service-dwh/products/{p_id}/exploded-views", timeout=10)
        if r.status_code == 200:
            views = r.json() or []
    except Exception as e:
        return p_id, [], "", "", f"views err: {e}"

    parts = []
    pdf_name = ""
    main_view_id = ""

    for v in views:
        if not isinstance(v, dict):
            continue
        v_id = v.get("id")
        v_name = v.get("name", "")
        if not main_view_id and v_id:
            main_view_id = str(v_id)
        v_pdf = v.get("pdfName") or v.get("code") or v.get("fileName")
        if v_pdf and not pdf_name:
            pdf_name = str(v_pdf)

        if not v_id:
            continue

        try:
            pr = session.get(f"{API_BASE}/service-dwh/products/{p_id}/exploded-views/{v_id}/parts", timeout=10)
            if pr.status_code == 200:
                pts = pr.json() or []
                for pt in pts:
                    if isinstance(pt, dict):
                        pt_code = pt.get("code") or pt.get("partCode") or f"P-{pt.get('id','')}"
                        pt_i18n = pt.get("i18n") or {}
                        pt_name = pt_i18n.get("en") or pt.get("description") or pt.get("name") or "Part"
                        parts.append({
                            "product_id": p_id,
                            "code": str(pt_code),
                            "name": str(pt_name),
                            "price": float(pt.get("price") or 0.0),
                            "stock": int(pt.get("availability") or 0),
                            "ref": str(pt.get("position") or pt.get("ref") or ""),
                            "view_name": str(v_name)
                        })
        except Exception:
            pass

    return p_id, parts, pdf_name, main_view_id, None

def main():
    session = get_sirman_session()

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Find target products
    target_prods = c.execute("SELECT id FROM products WHERE parts_count = 0").fetchall()
    target_ids = [r[0] for r in target_prods]
    print(f"\n[TARGET] Found {len(target_ids)} products with parts_count = 0")

    if not target_ids:
        print("[OK] All products already have parts!")
        conn.close()
        return

    start_time = time.time()
    completed = 0
    total_parts_added = 0
    new_parts_batch = []
    prod_updates = []

    print(f"[START] Processing {len(target_ids)} products using 12 parallel threads...\n")

    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = {executor.submit(fetch_product_parts, pid, session): pid for pid in target_ids}

        for future in as_completed(futures):
            pid, parts, pdf_name, view_id, err = future.result()
            completed += 1

            if parts:
                new_parts_batch.extend(parts)
                total_parts_added += len(parts)

            prod_updates.append((len(parts), pdf_name, view_id, pid))

            if completed % 50 == 0 or completed == len(target_ids):
                elapsed = time.time() - start_time
                rate = completed / elapsed if elapsed > 0 else 0
                eta = (len(target_ids) - completed) / rate if rate > 0 else 0
                pct = (completed / len(target_ids)) * 100
                print(f"  [{completed}/{len(target_ids)}] {pct:5.1f}% | {rate:.1f} prods/s | ETA: {eta:.0f}s | Parts added: {total_parts_added}")

            # Save in batches of 200 products
            if len(prod_updates) >= 200:
                for cnt, pdf, vid, p_id in prod_updates:
                    c.execute("UPDATE products SET parts_count = ?, pdf_name = ?, exploded_view_id = ? WHERE id = ?", (cnt, pdf, vid, p_id))
                for pt in new_parts_batch:
                    c.execute("""
                        INSERT INTO parts (product_id, code, name, price, stock, ref, view_name)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (pt["product_id"], pt["code"], pt["name"], pt["price"], pt["stock"], pt["ref"], pt["view_name"]))
                conn.commit()
                prod_updates = []
                new_parts_batch = []

    # Final commit
    if prod_updates or new_parts_batch:
        for cnt, pdf, vid, p_id in prod_updates:
            c.execute("UPDATE products SET parts_count = ?, pdf_name = ?, exploded_view_id = ? WHERE id = ?", (cnt, pdf, vid, p_id))
        for pt in new_parts_batch:
            c.execute("""
                INSERT INTO parts (product_id, code, name, price, stock, ref, view_name)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (pt["product_id"], pt["code"], pt["name"], pt["price"], pt["stock"], pt["ref"], pt["view_name"]))
        conn.commit()

    conn.close()

    print(f"\n[DONE FETCHING] Total time: {time.time()-start_time:.1f}s")
    print(f"Total parts added to SQLite: {total_parts_added:,}")

    # Step 2: Upload new parts to Supabase
    print("\n=== STEP 2: Uploading updated products & parts to Supabase ===")
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Update products on Supabase
    prods = c.execute("SELECT id, parts_count, pdf_name, exploded_view_id FROM products WHERE id IN ({})".format(",".join(map(str, target_ids)))).fetchall()
    prod_rows = [{"id": r[0], "parts_count": r[1], "pdf_name": r[2] or ""} for r in prods]

    print(f"Updating {len(prod_rows)} products on Supabase...")
    for i in range(0, len(prod_rows), 500):
        batch = prod_rows[i:i+500]
        requests.post(f"{SUPABASE_URL}/rest/v1/products", headers=SUP_HEADERS, json=batch, timeout=30)

    # Upload new parts
    all_parts = c.execute("SELECT product_id, code, name, price, stock, ref, view_name FROM parts WHERE product_id IN ({})".format(",".join(map(str, target_ids)))).fetchall()
    conn.close()

    print(f"Uploading {len(all_parts):,} parts to Supabase...")
    seen = set()
    parts_payload = []
    for pid, code, name, price, stock, ref, view_name in all_parts:
        key = f"{pid}:{code}"
        if key in seen:
            continue
        seen.add(key)
        parts_payload.append({
            "product_id": pid,
            "code": str(code or ""),
            "name": str(name or ""),
            "price": float(price or 0),
            "stock": int(stock or 0),
            "ref": str(ref or ""),
            "view_name": str(view_name or "")
        })

    for i in range(0, len(parts_payload), 1000):
        batch = parts_payload[i:i+1000]
        requests.post(f"{SUPABASE_URL}/rest/v1/parts", headers=SUP_HEADERS, json=batch, timeout=45)
        print(f"  Uploaded [{min(i+1000, len(parts_payload))}/{len(parts_payload)}]")

    print("\n🎉 ALL MISSING PARTS FETCHED & UPLOADED TO SUPABASE!")

if __name__ == "__main__":
    main()
