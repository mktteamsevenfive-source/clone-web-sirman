"""
sync_images.py - Smart Image Sync for Sirman Diagrams
======================================================
1. Lists ALL existing images on Supabase Storage (diagram_images bucket)
2. Reads pdf_name for every product from sirman_catalog_data.json / sirman_parts.json
3. Only downloads images that are NOT yet on Supabase (skip duplicates)
4. Opens browser to capture auth headers + intercept real image URLs from Sirman
5. Uploads new images directly to Supabase Storage
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path

try:
    import requests as req_lib
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "requests"], check=True)
    import requests as req_lib

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("Run: pip install playwright && playwright install chromium")
    sys.exit(1)

# ── Config ──────────────────────────────────────────────────────────────────
SUPABASE_URL     = "https://ofrerwyoasklgsejlbzr.supabase.co"
SUPABASE_ANON    = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9mcmVyd3lvYXNrbGdzZWpsYnpyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODUzNjY2NTUsImV4cCI6MjEwMDk0MjY1NX0.LksXP_vyz_vPJthhX2T6Nyto1xPsfacvqtXW-s2ClTU"
SUPABASE_BUCKET  = "diagram_images"
CATALOG_FILE     = Path(__file__).parent / "sirman_catalog_data.json"
PARTS_FILE       = Path(__file__).parent / "sirman_parts.json"
HEADERS_FILE     = Path(__file__).parent / "sirman_headers.json"
LOCAL_CACHE_DIR  = Path(__file__).parent / "public" / "exploded-views"
API_BASE         = "https://api-service.sirman.com"

LOCAL_CACHE_DIR.mkdir(parents=True, exist_ok=True)

SUPABASE_HEADERS = {
    "apikey": SUPABASE_ANON,
    "Authorization": f"Bearer {SUPABASE_ANON}",
}


# ── Step 1: List existing images on Supabase ─────────────────────────────────
def list_supabase_images() -> set[str]:
    """Returns a set of filenames already in the Supabase bucket."""
    print("[1] Listing existing images on Supabase Storage...")
    existing = set()
    offset = 0
    page_size = 1000

    while True:
        url = f"{SUPABASE_URL}/storage/v1/object/list/{SUPABASE_BUCKET}"
        payload = {"limit": page_size, "offset": offset, "prefix": "", "sortBy": {"column": "name", "order": "asc"}}
        r = req_lib.post(url, headers=SUPABASE_HEADERS, json=payload, timeout=15)
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

    print(f"  -> {len(existing)} images already on Supabase")
    return existing


# ── Step 2: Collect all pdf_names needed ─────────────────────────────────────
def collect_needed_pdf_names() -> dict[str, str]:
    """Returns dict: {supabase_filename -> pdf_name (without .png)} for ALL products."""
    needed: dict[str, str] = {}

    def add_pdf(pdf_name: str):
        if not pdf_name:
            return
        supabase_name = f"{pdf_name}.png" if not pdf_name.endswith(".png") else pdf_name
        needed[supabase_name] = pdf_name

    # From sirman_catalog_data.json
    if CATALOG_FILE.exists():
        data = json.load(open(CATALOG_FILE, encoding="utf-8"))
        for prod in data.get("products", []):
            add_pdf(prod.get("pdf_name", ""))
        print(f"  -> {len(needed)} unique diagram names from sirman_catalog_data.json")

    # From sirman_parts.json (in case catalog is empty or different)
    if PARTS_FILE.exists():
        data = json.load(open(PARTS_FILE, encoding="utf-8"))
        for cat_name, cat_prods in data.get("categories", {}).items():
            for prod in cat_prods:
                add_pdf(prod.get("pdf_name", ""))
        print(f"  -> {len(needed)} unique diagram names total (after merging both files)")

    return needed


# ── Step 3: Upload image bytes to Supabase Storage ───────────────────────────
def upload_to_supabase(filename: str, img_bytes: bytes) -> bool:
    url = f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET}/{filename}"
    headers = {**SUPABASE_HEADERS, "Content-Type": "image/png", "x-upsert": "false"}
    try:
        r = req_lib.post(url, headers=headers, data=img_bytes, timeout=20)
        if r.status_code in (200, 201):
            return True
        print(f"  [WARN] Upload failed {filename}: HTTP {r.status_code} {r.text[:80]}")
    except Exception as e:
        print(f"  [ERR] Upload error: {e}")
    return False


# ── Step 4: Try to find and download image using saved Sirman session ─────────
def try_download_from_sirman(pdf_name: str, sirman_session: req_lib.Session) -> bytes | None:
    """Try multiple URL patterns to find the actual image on Sirman servers."""
    candidates = [
        f"{API_BASE}/service-dwh/media/exploded-views/{pdf_name}.png",
        f"{API_BASE}/service-dwh/media/exploded-views/{pdf_name}",
        f"{API_BASE}/service-dwh/media/{pdf_name}.png",
        f"https://service.sirman.com/media/exploded-views/{pdf_name}.png",
        f"https://service.sirman.com/media/{pdf_name}.png",
    ]
    for url in candidates:
        try:
            r = sirman_session.get(url, timeout=15)
            if r.status_code == 200 and len(r.content) > 1000:
                return r.content
        except Exception:
            pass
    return None


# ── Step 5: Load Sirman session headers ──────────────────────────────────────
async def get_sirman_session() -> req_lib.Session:
    """Load saved headers or open browser to capture new ones."""
    if HEADERS_FILE.exists():
        try:
            data = json.load(open(HEADERS_FILE, encoding="utf-8"))
            hdrs = data.get("headers", {})
            cookies = data.get("cookies", [])
            if hdrs:
                session = req_lib.Session()
                clean = {k: v for k, v in hdrs.items() if not k.startswith(":")}
                session.headers.update(clean)
                cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
                if cookie_str:
                    session.headers["cookie"] = cookie_str
                print("[INFO] Reusing saved Sirman auth headers from sirman_headers.json")
                return session
        except Exception:
            pass

    # Need to capture new session
    print("[INFO] No saved headers found. Opening browser to capture new session...")
    print("  -> Login to Sirman, click any category, then press Enter")
    
    captured_hdrs: dict = {}
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=["--start-maximized"])
        ctx = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await ctx.new_page()

        async def on_request(req):
            if "api-service.sirman.com/service-dwh/products" in req.url and "category=" in req.url:
                captured_hdrs.update({k: v for k, v in dict(req.headers).items()
                                       if not k.startswith(":")})

        page.on("request", on_request)
        await page.goto("https://service.sirman.com/catalog", wait_until="domcontentloaded")
        input("  >> Press Enter after you logged in and see products ...")
        cookies = await ctx.cookies()
        await browser.close()

    session = req_lib.Session()
    clean = {k: v for k, v in captured_hdrs.items() if not k.startswith(":")}
    session.headers.update(clean)
    cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
    if cookie_str:
        session.headers["cookie"] = cookie_str

    # Save for reuse
    with open(HEADERS_FILE, "w", encoding="utf-8") as f:
        json.dump({"headers": captured_hdrs, "cookies": cookies}, f, indent=2)

    return session


# ── Main ─────────────────────────────────────────────────────────────────────
async def main():
    print("=" * 65)
    print("  SIRMAN IMAGE SYNC - Smart Skip Already-Uploaded Images")
    print("=" * 65)

    # Step 1: What's already on Supabase?
    existing_on_supabase = list_supabase_images()

    # Step 2: What do we need?
    print("\n[2] Collecting required diagram names from product data...")
    needed = collect_needed_pdf_names()
    
    # Step 3: Calculate missing
    missing = {fname: pdf for fname, pdf in needed.items()
               if fname not in existing_on_supabase and pdf}
    already_done = len(needed) - len(missing)
    
    print(f"\n[3] Summary:")
    print(f"  Total diagrams needed:         {len(needed)}")
    print(f"  Already on Supabase (skip):    {already_done}")
    print(f"  Need to download + upload:     {len(missing)}")

    if not missing:
        print("\n[SUCCESS] All images are already on Supabase! Nothing to do.")
        return

    # Step 4: Get Sirman session
    print("\n[4] Getting Sirman authenticated session...")
    sirman_session = await get_sirman_session()

    # Step 5: Download missing + upload to Supabase
    print(f"\n[5] Downloading {len(missing)} missing images and uploading to Supabase...")
    uploaded = 0
    failed = 0
    start = time.time()

    for idx, (supabase_fname, pdf_name) in enumerate(missing.items(), 1):
        # Try local cache first
        local_path = LOCAL_CACHE_DIR / supabase_fname
        img_bytes = None

        if local_path.exists():
            img_bytes = local_path.read_bytes()
            print(f"  [{idx}/{len(missing)}] {pdf_name} -> from local cache")
        else:
            img_bytes = try_download_from_sirman(pdf_name, sirman_session)
            if img_bytes:
                # Save to local cache too
                local_path.write_bytes(img_bytes)

        if img_bytes:
            if upload_to_supabase(supabase_fname, img_bytes):
                uploaded += 1
                elapsed = time.time() - start
                print(f"  [{idx}/{len(missing)}] ✅ {supabase_fname} uploaded ({elapsed:.0f}s | {uploaded} done)")
            else:
                failed += 1
        else:
            failed += 1
            if idx % 20 == 0 or idx <= 5:
                print(f"  [{idx}/{len(missing)}] ⚠️  {pdf_name} - not found on Sirman servers")

    elapsed = time.time() - start
    print(f"\n{'='*65}")
    print(f"  [DONE] Image Sync Complete in {elapsed:.1f}s")
    print(f"  Already existed on Supabase: {already_done}")
    print(f"  Newly uploaded:              {uploaded}")
    print(f"  Not found / failed:          {failed}")
    print(f"{'='*65}")


if __name__ == "__main__":
    asyncio.run(main())
