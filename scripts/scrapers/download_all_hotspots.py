"""
download_all_hotspots.py - Master Sirman Hotspot JSON Downloader & Sync
========================================================================
1. Reads all products from sirman_catalog_data.json
2. Downloads hotspot JSON files for each diagram from Sirman API
3. Saves to public/hotspots/{clean_pdf_name}.json
4. Uploads hotspot JSON files to Supabase Storage bucket 'diagram_hotspots'
"""

import json
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import requests
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "requests"], check=True)
    import requests

BASE_DIR        = Path(__file__).resolve().parent.parent.parent
CATALOG_FILE    = BASE_DIR / "sirman_catalog_data.json"
HEADERS_FILE    = BASE_DIR / "sirman_headers.json"
HOTSPOTS_DIR    = BASE_DIR / "public" / "hotspots"

SUPABASE_URL     = "https://ofrerwyoasklgsejlbzr.supabase.co"
SUPABASE_SERVICE = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9mcmVyd3lvYXNrbGdzZWpsYnpyIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NTM2NjY1NSwiZXhwIjoyMTAwOTQyNjU1fQ.shN-wvqCOZi1GtPO3rwCHF51OQ0hf23E_GVn9bt3bHQ"
SUPABASE_BUCKET  = "diagram_hotspots"

HOTSPOTS_DIR.mkdir(parents=True, exist_ok=True)

SUPABASE_HEADERS = {
    "apikey": SUPABASE_SERVICE,
    "Authorization": f"Bearer {SUPABASE_SERVICE}",
}


def get_sirman_session() -> requests.Session:
    if not HEADERS_FILE.exists():
        print("[ERROR] sirman_headers.json not found!")
        sys.exit(1)
    data = json.load(open(HEADERS_FILE, encoding="utf-8"))
    hdrs = data.get("headers", {})
    cookies = data.get("cookies", [])
    session = requests.Session()
    clean = {k: v for k, v in hdrs.items() if not k.startswith(":")}
    session.headers.update(clean)
    cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
    if cookie_str:
        session.headers["cookie"] = cookie_str
    return session


def upload_json_to_supabase(filename: str, json_data: dict) -> bool:
    url = f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET}/{filename}"
    headers = {**SUPABASE_HEADERS, "Content-Type": "application/json", "x-upsert": "true"}
    try:
        payload = json.dumps(json_data, ensure_ascii=False)
        r = requests.post(url, headers=headers, data=payload.encode('utf-8'), timeout=20)
        if r.status_code in (200, 201):
            return True
    except Exception:
        pass
    return False


def process_pdf(clean_pdf_name: str, sirman_session: requests.Session) -> str:
    target_file = HOTSPOTS_DIR / f"{clean_pdf_name}.json"
    
    parsed = None
    if target_file.exists():
        try:
            parsed = json.load(open(target_file, encoding="utf-8"))
        except Exception:
            pass

    if not parsed:
        url = f"https://api-service.sirman.com/service-dwh/resources/exploded-view/json/{clean_pdf_name}.json/content"
        try:
            r = sirman_session.get(url, timeout=10)
            if r.status_code == 200:
                raw = r.json()
                parsed = json.loads(raw) if isinstance(raw, str) else raw
                with open(target_file, "w", encoding="utf-8") as f:
                    json.dump(parsed, f, ensure_ascii=False)
        except Exception:
            pass

    if parsed:
        upload_json_to_supabase(f"{clean_pdf_name}.json", parsed)
        return "success"

    return "failed"


def main():
    print("=" * 65)
    print("  SIRMAN DIAGRAM HOTSPOTS DOWNENLOADER & SUPABASE SYNC")
    print("=" * 65)

    if not CATALOG_FILE.exists():
        print("[ERROR] catalog file not found!")
        sys.exit(1)

    catalog = json.load(open(CATALOG_FILE, encoding="utf-8"))
    prods = catalog.get("products", [])

    # Collect unique pdf names
    pdf_names = set()
    for p in prods:
        pdf = p.get("pdf_name")
        if pdf:
            clean = pdf.replace(".pdf", "").replace(".png", "")
            if clean:
                pdf_names.add(clean)

    print(f"[INFO] Found {len(pdf_names)} unique diagram PDF names to fetch hotspots for")

    session = get_sirman_session()

    success_count = 0
    failed_count = 0
    start = time.time()

    print(f"[INFO] Downloading hotspot JSONs with 15 parallel workers...")
    pdf_list = list(pdf_names)

    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = [executor.submit(process_pdf, pdf, session) for pdf in pdf_list]
        for idx, f in enumerate(as_completed(futures), 1):
            res = f.result()
            if res == "success":
                success_count += 1
            else:
                failed_count += 1

            if idx % 25 == 0 or idx == len(pdf_list):
                elapsed = time.time() - start
                rate = idx / elapsed if elapsed > 0 else 0
                print(f"  [{idx}/{len(pdf_list)}] Hotspots fetched: {success_count} | Failed: {failed_count} ({rate:.1f} json/s)")

    elapsed = time.time() - start
    print(f"\n{'='*65}")
    print(f"  [DONE] Hotspot Sync Completed in {elapsed:.1f}s")
    print(f"  Hotspot JSONs Saved & Uploaded: {success_count}/{len(pdf_list)}")
    print(f"{'='*65}")


if __name__ == "__main__":
    main()
