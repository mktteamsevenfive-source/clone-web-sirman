"""
download_all_images_to_supabase.py - Automated Master Diagram Downloader & Supabase Uploader
========================================================================================
1. Fetches list of existing images in Supabase Storage bucket 'diagram_images'
2. Skips files that are already on Supabase (Smart duplicate avoidance)
3. For missing images, requests signed CloudFront URL from Sirman API
4. Downloads PNG image and uploads directly to Supabase Storage
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

# ── Config ──────────────────────────────────────────────────────────────────
SUPABASE_URL     = "https://ofrerwyoasklgsejlbzr.supabase.co"
SUPABASE_SERVICE = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9mcmVyd3lvYXNrbGdzZWpsYnpyIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NTM2NjY1NSwiZXhwIjoyMTAwOTQyNjU1fQ.shN-wvqCOZi1GtPO3rwCHF51OQ0hf23E_GVn9bt3bHQ"
SUPABASE_BUCKET  = "diagram_images"
API_BASE         = "https://api-service.sirman.com"

BASE_DIR         = Path(__file__).resolve().parent
PROJECT_ROOT     = BASE_DIR.parent.parent
CATALOG_FILE     = PROJECT_ROOT / "sirman_catalog_data.json"
PARTS_FILE       = PROJECT_ROOT / "sirman_parts.json"
HEADERS_FILE     = PROJECT_ROOT / "sirman_headers.json"
LOCAL_CACHE_DIR  = PROJECT_ROOT / "public" / "exploded-views"

LOCAL_CACHE_DIR.mkdir(parents=True, exist_ok=True)

SUPABASE_HEADERS = {
    "apikey": SUPABASE_SERVICE,
    "Authorization": f"Bearer {SUPABASE_SERVICE}",
}


# ── Load Sirman Auth Session ─────────────────────────────────────────────────
def get_sirman_session() -> requests.Session:
    if not HEADERS_FILE.exists():
        print("[ERROR] sirman_headers.json not found! Run scrape_with_browser.py once to log in.")
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


# ── List Existing Images on Supabase ──────────────────────────────────────────
def list_supabase_images() -> set[str]:
    print("[1] Listing existing images on Supabase Storage...")
    existing = set()
    offset = 0
    page_size = 1000

    while True:
        url = f"{SUPABASE_URL}/storage/v1/object/list/{SUPABASE_BUCKET}"
        payload = {"limit": page_size, "offset": offset, "prefix": "", "sortBy": {"column": "name", "order": "asc"}}
        r = requests.post(url, headers=SUPABASE_HEADERS, json=payload, timeout=15)
        if r.status_code != 200:
            print(f"  [WARN] Could not list Supabase bucket: HTTP {r.status_code}")
            break
        items = r.json()
        if not items:
            break
        for item in items:
            existing.add(item.get("name", ""))
        if len(items) < page_size:
            break
        offset += page_size

    print(f"  -> Found {len(existing)} images already uploaded on Supabase Storage")
    return existing


# ── Collect Required Diagram Names ────────────────────────────────────────────
def collect_needed_pdf_names() -> dict[str, str]:
    needed = {}

    def add_pdf(pdf_name: str):
        if not pdf_name:
            return
        clean = pdf_name.replace(".pdf", "").replace(".png", "")
        if not clean:
            return
        needed[f"{pdf_name}.png"] = clean
        needed[f"{clean}.png"] = clean

    print("[2] Fetching all pdf_names from Supabase products table...")
    prods = []
    offset = 0
    while True:
        r = requests.get(
            f"{SUPABASE_URL}/rest/v1/products?select=pdf_name,exploded_view_id&limit=1000&offset={offset}",
            headers=SUPABASE_HEADERS
        )
        batch = r.json() if r.status_code == 200 else []
        if not batch:
            break
        prods.extend(batch)
        if len(batch) < 1000:
            break
        offset += 1000

    for prod in prods:
        pdf = prod.get("pdf_name")
        view_id = prod.get("exploded_view_id")
        add_pdf(pdf)
        if view_id:
            add_pdf(f"{view_id}.png")

    return needed


# ── Upload Image Bytes to Supabase ────────────────────────────────────────────
def upload_to_supabase(filename: str, img_bytes: bytes) -> bool:
    url = f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET}/{filename}"
    headers = {**SUPABASE_HEADERS, "Content-Type": "image/png", "x-upsert": "true"}
    try:
        r = requests.post(url, headers=headers, data=img_bytes, timeout=20)
        if r.status_code in (200, 201):
            return True
    except Exception:
        pass
    return False


# ── Download Image via 2-Step Signed URL ──────────────────────────────────────
def download_diagram_image(sirman_session: requests.Session, pdf_clean: str) -> bytes | None:
    # Try signed URL endpoint
    endpoints = [
        f"{API_BASE}/service-dwh/resources/exploded-view/jpeg/{pdf_clean}.png?quality=full",
        f"{API_BASE}/service-dwh/resources/exploded-view/jpeg/{pdf_clean}.pdf.png?quality=full",
    ]
    for url in endpoints:
        try:
            r = sirman_session.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, dict) and "url" in data:
                    signed_url = data["url"]
                    img_res = requests.get(signed_url, timeout=15)
                    if img_res.status_code == 200 and len(img_res.content) > 1000:
                        return img_res.content
        except Exception:
            pass
    return None


def process_item(item_pair, sirman_session, existing_on_supabase):
    target_filename, pdf_clean = item_pair

    if target_filename in existing_on_supabase:
        return "skipped", target_filename

    # Check local cache first
    local_path = LOCAL_CACHE_DIR / target_filename
    img_bytes = None

    if local_path.exists():
        img_bytes = local_path.read_bytes()
    else:
        img_bytes = download_diagram_image(sirman_session, pdf_clean)
        if img_bytes:
            local_path.write_bytes(img_bytes)

    if img_bytes:
        if upload_to_supabase(target_filename, img_bytes):
            existing_on_supabase.add(target_filename)
            return "uploaded", target_filename

    return "failed", target_filename


def main():
    print("=" * 65)
    print("  SIRMAN DIAGRAM IMAGE SYNC - Automatic Downloader & Uploader")
    print("=" * 65)

    existing_on_supabase = list_supabase_images()
    needed = collect_needed_pdf_names()
    print(f"[2] Total unique diagram names collected: {len(needed)}")

    missing = {k: v for k, v in needed.items() if k not in existing_on_supabase}
    already_done = len(needed) - len(missing)

    print(f"\n[3] Status Summary:")
    print(f"  Total diagrams needed:       {len(needed)}")
    print(f"  Already uploaded on Supabase:{already_done} (skipped)")
    print(f"  Missing to download/upload:  {len(missing)}")

    if not missing:
        print("\n[SUCCESS] All diagram images are already 100% on Supabase Storage!")
        return

    sirman_session = get_sirman_session()

    print(f"\n[4] Downloading & Uploading {len(missing)} missing images (10 parallel workers)...")
    uploaded = 0
    failed = 0
    start = time.time()

    items = list(missing.items())
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process_item, item, sirman_session, existing_on_supabase) for item in items]
        for idx, f in enumerate(as_completed(futures), 1):
            status, fname = f.result()
            if status == "uploaded":
                uploaded += 1
            elif status == "failed":
                failed += 1

            if idx % 10 == 0 or idx == len(items):
                elapsed = time.time() - start
                rate = (uploaded + failed) / elapsed if elapsed > 0 else 0
                print(f"  [{idx}/{len(items)}] OK Uploaded: {uploaded} | Failed/Missing: {failed} ({rate:.1f} imgs/s)")

    elapsed = time.time() - start
    print(f"\n{'='*65}")
    print(f"  [DONE] Diagram Image Sync Completed in {elapsed:.1f}s")
    print(f"  Already on Supabase: {already_done}")
    print(f"  Newly Uploaded:      {uploaded}")
    print(f"  Failed / Not Found:  {failed}")
    print(f"{'='*65}")


if __name__ == "__main__":
    main()
