"""
SUPABASE STORAGE UPLOADER FOR DIAGRAM IMAGES
==============================================
Uploads all 150 PNG diagram images (79.76 MB total) from local diagram_images/
folder into Supabase Storage Bucket 'diagram_images'.
"""

import os
import sys
import time
from pathlib import Path

try:
    from supabase import create_client, Client
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "supabase"], check=True)
    from supabase import create_client, Client

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).parent
IMG_DIR = BASE_DIR / "diagram_images"
BUCKET_NAME = "diagram_images"

SUPABASE_URL = sys.argv[1] if len(sys.argv) > 1 else os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = sys.argv[2] if len(sys.argv) > 2 else os.getenv("SUPABASE_SERVICE_KEY", "")

def main():
    print("=" * 65)
    print("  SIRMAN DIAGRAM IMAGES -> SUPABASE STORAGE UPLOADER")
    print("=" * 65)

    if not IMG_DIR.exists():
        print(f"[ERROR] Directory {IMG_DIR} not found.")
        return

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # 1. Ensure Bucket Exists
    print(f"\n[1/2] Checking Bucket '{BUCKET_NAME}'...")
    try:
        buckets = supabase.storage.list_buckets()
        bucket_names = [b.name for b in buckets] if buckets else []
        if BUCKET_NAME not in bucket_names:
            print(f"  Creating public bucket '{BUCKET_NAME}'...")
            supabase.storage.create_bucket(BUCKET_NAME, options={"public": True})
            print("  [OK] Bucket created.")
        else:
            print("  [OK] Bucket already exists.")
    except Exception as e:
        print(f"  [Notice] Bucket check: {e}")

    # 2. Upload PNG Files
    png_files = list(IMG_DIR.glob("*.png"))
    print(f"\n[2/2] Uploading {len(png_files)} PNG Diagram Images (79.76 MB total)...")

    uploaded_count = 0
    skipped_count = 0

    for idx, img_path in enumerate(png_files, 1):
        file_name = img_path.name
        # Sanitize filename for S3/Supabase key safety
        safe_key = file_name.encode('ascii', errors='ignore').decode('ascii').replace(' ', '_')
        if not safe_key or safe_key.startswith('.'):
            safe_key = f"diagram_{idx}.png"

        print(f"  [{idx}/{len(png_files)}] Uploading {file_name} as {safe_key} ({img_path.stat().st_size / 1024:.1f} KB)...", end=" ")

        try:
            with open(img_path, "rb") as f:
                file_bytes = f.read()

            res = supabase.storage.from_(BUCKET_NAME).upload(
                path=safe_key,
                file=file_bytes,
                file_options={"content-type": "image/png", "x-upsert": "true"}
            )
            uploaded_count += 1
            print("Done [OK]")
        except Exception as err:
            err_str = str(err)
            if "AlreadyExists" in err_str or "duplicate" in err_str:
                skipped_count += 1
                print("Already exists [SKIPPED]")
            else:
                print(f"Err: {err}")

        time.sleep(0.05)

    print("\n" + "=" * 65)
    print("  [SUCCESS] DIAGRAM IMAGES UPLOAD COMPLETED!")
    print(f"  Uploaded: {uploaded_count}/{len(png_files)}")
    print(f"  Public Base URL: {SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/")
    print("=" * 65)

if __name__ == "__main__":
    main()
