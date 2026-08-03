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

    # 2. Upload Files (convert to Lossless WebP)
    from PIL import Image
    import io

    image_files = list(IMG_DIR.glob("*.png")) + list(IMG_DIR.glob("*.webp"))
    print(f"\n[2/2] Uploading {len(image_files)} Diagram Images (converting PNG to Lossless WebP)...")

    uploaded_count = 0
    skipped_count = 0

    for idx, img_path in enumerate(image_files, 1):
        raw_name = img_path.stem
        webp_name = f"{raw_name}.webp"
        safe_key = webp_name.encode('ascii', errors='ignore').decode('ascii').replace(' ', '_')
        if not safe_key or safe_key.startswith('.'):
            safe_key = f"diagram_{idx}.webp"

        print(f"  [{idx}/{len(image_files)}] Converting & Uploading {img_path.name} as {safe_key}...", end=" ")

        try:
            with open(img_path, "rb") as f:
                file_bytes = f.read()

            if img_path.suffix.lower() == ".png":
                img = Image.open(io.BytesIO(file_bytes))
                if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                    img = img.convert("RGBA")
                else:
                    img = img.convert("RGB")
                buf = io.BytesIO()
                img.save(buf, format="WEBP", lossless=True, method=4)
                file_bytes = buf.getvalue()

            res = supabase.storage.from_(BUCKET_NAME).upload(
                path=safe_key,
                file=file_bytes,
                file_options={"content-type": "image/webp", "x-upsert": "true"}
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
