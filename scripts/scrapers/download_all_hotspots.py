"""
download_all_hotspots.py - Master Sirman Hotspot JSON Downloader & Sync
========================================================================
1. Fetches all products directly from Supabase DB 'products' table
2. Downloads hotspot JSON files for each unique clean_pdf_name from Sirman API
3. Saves to public/hotspots/{clean_pdf_name}.json
4. Uploads hotspot JSON files to Supabase Storage bucket 'diagram_hotspots'
"""

import json
import sys
import time
import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

try:
    import requests
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "requests"], check=True)
    import requests

BASE_DIR        = Path(__file__).resolve().parent.parent.parent
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


def ensure_supabase_bucket():
    """Ensure diagram_hotspots bucket exists on Supabase Storage."""
    url = f"{SUPABASE_URL}/storage/v1/bucket"
    r = requests.get(url, headers=SUPABASE_HEADERS)
    if r.status_code == 200:
        buckets = [b.get("id") for b in r.json()]
        if SUPABASE_BUCKET not in buckets:
            payload = {"id": SUPABASE_BUCKET, "name": SUPABASE_BUCKET, "public": True}
            requests.post(url, headers=SUPABASE_HEADERS, json=payload)


def get_sirman_session() -> requests.Session:
    if not HEADERS_FILE.exists():
        print("[ERROR] sirman_headers.json not found! Run capture_fresh_token.py first.")
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


def fetch_pdf_names_from_supabase() -> list[str]:
    """Fetch all unique clean pdf names from Supabase products table."""
    print("[1] Fetching unique diagram pdf_names from Supabase DB...")
    pdf_names = set()
    offset = 0
    while True:
        url = f"{SUPABASE_URL}/rest/v1/products?select=pdf_name&limit=1000&offset={offset}"
        r = requests.get(url, headers=SUPABASE_HEADERS, timeout=15)
        if r.status_code != 200:
            break
        batch = r.json()
        if not batch:
            break
        for p in batch:
            pdf = p.get("pdf_name")
            if pdf:
                clean = re.sub(r'\.pdf$', '', pdf, flags=re.IGNORECASE).strip()
                clean = re.sub(r'\.png$', '', clean, flags=re.IGNORECASE).strip()
                if clean:
                    pdf_names.add(clean)
        if len(batch) < 1000:
            break
        offset += 1000
    print(f"  Found {len(pdf_names)} unique diagram PDF names in DB")
    return sorted(list(pdf_names))


def upload_json_to_supabase(filename: str, json_data: dict) -> bool:
    url = f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET}/{filename}"
    headers = {**SUPABASE_HEADERS, "Content-Type": "application/json", "x-upsert": "true"}
    try:
        payload = json.dumps(json_data, ensure_ascii=False)
        r = requests.post(url, headers=headers, data=payload.encode('utf-8'), timeout=20)
        return r.status_code in (200, 201)
    except Exception:
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
            r = sirman_session.get(url, timeout=12)
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
    print("  SIRMAN DIAGRAM HOTSPOTS DOWNLOADER & SUPABASE SYNC")
    print("=" * 65)

    ensure_supabase_bucket()
    pdf_list = fetch_pdf_names_from_supabase()

    if not pdf_list:
        print("[ERROR] No pdf_names found in DB!")
        return

    session = get_sirman_session()

    success_count = 0
    failed_count = 0
    already_local = sum(1 for p in pdf_list if (HOTSPOTS_DIR / f"{p}.json").exists())

    print(f"[INFO] Local cache already has {already_local}/{len(pdf_list)} hotspot JSON files")
    print(f"[INFO] Fetching missing hotspot JSONs with 15 parallel workers...")

    start = time.time()

    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = [executor.submit(process_pdf, pdf, session) for pdf in pdf_list]
        for idx, f in enumerate(as_completed(futures), 1):
            res = f.result()
            if res == "success":
                success_count += 1
            else:
                failed_count += 1

            if idx % 50 == 0 or idx == len(pdf_list):
                elapsed = time.time() - start
                rate = idx / elapsed if elapsed > 0 else 0
                print(f"  [{idx}/{len(pdf_list)}] Hotspots ready: {success_count} | Failed/No Hotspot: {failed_count} ({rate:.1f} json/s)")

    elapsed = time.time() - start
    print(f"\n{'='*65}")
    print(f"  [DONE] Hotspot Sync Completed in {elapsed:.1f}s")
    print(f"  Hotspot JSONs Ready & Uploaded: {success_count}/{len(pdf_list)}")
    print(f"{'='*65}")


if __name__ == "__main__":
    main()
