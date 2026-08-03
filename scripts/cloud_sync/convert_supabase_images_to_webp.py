"""
convert_supabase_images_to_webp.py - Convert Supabase Diagram Images to WebP
=============================================================================
1. Scans diagram_images bucket on Supabase Storage for all .png files
2. Downloads each PNG, converts to WebP format (quality 85)
3. Uploads the .webp image to Supabase Storage
4. Deletes original .png file from Supabase Storage upon successful upload
5. Supports multithreading for fast processing
"""

import io
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

try:
    import requests
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "requests"], check=True)
    import requests

try:
    from PIL import Image
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "Pillow"], check=True)
    from PIL import Image

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# ── Credentials & Config ──────────────────────────────────────────────────────
SUPABASE_URL     = "https://ofrerwyoasklgsejlbzr.supabase.co"
SUPABASE_SERVICE = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9mcmVyd3lvYXNrbGdzZWpsYnpyIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NTM2NjY1NSwiZXhwIjoyMTAwOTQyNjU1fQ.shN-wvqCOZi1GtPO3rwCHF51OQ0hf23E_GVn9bt3bHQ"
BUCKET           = "diagram_images"
MAX_WORKERS      = 12
WEBP_QUALITY     = 85

HEADERS = {
    "apikey": SUPABASE_SERVICE,
    "Authorization": f"Bearer {SUPABASE_SERVICE}",
}


def list_bucket_files(bucket_name: str) -> list[dict]:
    """Fetch all object metadata items from a Supabase storage bucket."""
    print(f"[INFO] Fetching object list from Supabase bucket '{bucket_name}'...")
    all_items = []
    offset = 0
    limit = 1000

    while True:
        url = f"{SUPABASE_URL}/storage/v1/object/list/{bucket_name}"
        payload = {"prefix": "", "limit": limit, "offset": offset, "sortBy": {"column": "name", "order": "asc"}}
        r = requests.post(url, headers=HEADERS, json=payload, timeout=30)
        if r.status_code != 200:
            print(f"[ERROR] Failed to list bucket: HTTP {r.status_code} {r.text}")
            break
        items = r.json()
        if not items:
            break
        all_items.extend(items)
        if len(items) < limit:
            break
        offset += limit

    print(f"[INFO] Total items in '{bucket_name}': {len(all_items)}")
    return all_items


def process_single_image(item: dict) -> tuple[bool, int, int, str]:
    """
    Downloads PNG, converts to WebP, uploads WebP, and deletes original PNG.
    Returns (success, original_size, webp_size, filename)
    """
    filename = item.get("name", "")
    if not filename.lower().endswith(".png"):
        return False, 0, 0, filename

    basename = filename[:-4]
    webp_filename = f"{basename}.webp"

    # 1. Download original PNG
    get_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{requests.utils.quote(filename)}"
    try:
        r_dl = requests.get(get_url, timeout=30)
        if r_dl.status_code != 200:
            print(f"  [WARN] Failed to download {filename}: HTTP {r_dl.status_code}")
            return False, 0, 0, filename
        png_bytes = r_dl.content
        orig_size = len(png_bytes)

        # 2. Convert to WebP
        img = Image.open(io.BytesIO(png_bytes))
        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            img = img.convert("RGBA")
        else:
            img = img.convert("RGB")

        buf = io.BytesIO()
        img.save(buf, format="WEBP", lossless=True, method=4)
        webp_bytes = buf.getvalue()
        webp_size = len(webp_bytes)

        # 3. Upload WebP to Supabase Storage
        up_url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{requests.utils.quote(webp_filename)}"
        up_headers = {**HEADERS, "Content-Type": "image/webp", "x-upsert": "true"}
        r_up = requests.post(up_url, headers=up_headers, data=webp_bytes, timeout=30)
        if r_up.status_code not in (200, 201):
            print(f"  [WARN] Upload WebP failed for {webp_filename}: HTTP {r_up.status_code}")
            return False, orig_size, 0, filename

        # 4. Delete original PNG from Supabase Storage
        del_url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{requests.utils.quote(filename)}"
        r_del = requests.delete(del_url, headers=HEADERS, timeout=30)
        if r_del.status_code != 200:
            print(f"  [WARN] Delete original PNG failed for {filename}: HTTP {r_del.status_code}")

        return True, orig_size, webp_size, filename

    except Exception as e:
        print(f"  [ERROR] Exception processing {filename}: {e}")
        return False, 0, 0, filename


def main():
    print("=" * 70)
    print("  SUPABASE STORAGE - PNG TO WEBP CONVERTER")
    print("=" * 70)

    items = list_bucket_files(BUCKET)
    png_items = [item for item in items if item.get("name", "").lower().endswith(".png")]
    total = len(png_items)

    if total == 0:
        print("[INFO] No PNG files found in bucket. All images may already be converted!")
        return

    print(f"\n[INFO] Starting conversion of {total} PNG images using {MAX_WORKERS} threads...\n")

    start_time = time.time()
    completed = 0
    success_count = 0
    total_orig_bytes = 0
    total_webp_bytes = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_single_image, item): item for item in png_items}

        for future in as_completed(futures):
            completed += 1
            ok, orig_sz, webp_sz, name = future.result()

            if ok:
                success_count += 1
                total_orig_bytes += orig_sz
                total_webp_bytes += webp_sz

            if completed % 50 == 0 or completed == total:
                elapsed = time.time() - start_time
                rate = completed / elapsed if elapsed > 0 else 0
                pct = (completed / total) * 100
                orig_mb = total_orig_bytes / (1024 * 1024)
                webp_mb = total_webp_bytes / (1024 * 1024)
                saved_mb = orig_mb - webp_mb
                ratio = (1 - webp_mb / orig_mb) * 100 if orig_mb > 0 else 0

                print(
                    f"[{completed:4d}/{total:4d}] {pct:5.1f}% | OK: {success_count:4d} | "
                    f"Orig: {orig_mb:6.1f}MB -> WebP: {webp_mb:6.1f}MB | Saved: {saved_mb:6.1f}MB (-{ratio:.1f}%) | {rate:.1f} img/s"
                )

    total_time = time.time() - start_time
    orig_mb = total_orig_bytes / (1024 * 1024)
    webp_mb = total_webp_bytes / (1024 * 1024)
    saved_mb = orig_mb - webp_mb
    ratio = (1 - webp_mb / orig_mb) * 100 if orig_mb > 0 else 0

    print("\n" + "=" * 70)
    print("  CONVERSION COMPLETED")
    print("=" * 70)
    print(f"  Total Processed : {completed} / {total} files")
    print(f"  Successful      : {success_count} files")
    print(f"  Original Size   : {orig_mb:.2f} MB")
    print(f"  WebP Size       : {webp_mb:.2f} MB")
    print(f"  Space Saved     : {saved_mb:.2f} MB (-{ratio:.1f}%)")
    print(f"  Time Elapsed    : {total_time:.1f} seconds")
    print("=" * 70)


if __name__ == "__main__":
    main()
