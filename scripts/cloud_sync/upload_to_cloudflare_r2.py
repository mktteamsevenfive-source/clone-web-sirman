"""
CLOUDFLARE R2 UPLOADER FOR DIAGRAM IMAGES
==========================================
Uploads 150 PNG diagram images (79.76 MB total) from local diagram_images/
folder to Cloudflare R2 S3-Compatible Object Storage.

Requirements:
  pip install boto3

Usage:
  python upload_to_cloudflare_r2.py <ACCOUNT_ID> <ACCESS_KEY_ID> <SECRET_ACCESS_KEY> <BUCKET_NAME>
"""

import os
import sys
import time
from pathlib import Path

try:
    import boto3
except ImportError:
    import subprocess
    print("Installing boto3 library...")
    subprocess.run([sys.executable, "-m", "pip", "install", "boto3"], check=True)
    import boto3

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).parent
IMG_DIR = BASE_DIR / "diagram_images"

ACCOUNT_ID = sys.argv[1] if len(sys.argv) > 1 else os.getenv("R2_ACCOUNT_ID", "")
ACCESS_KEY_ID = sys.argv[2] if len(sys.argv) > 2 else os.getenv("R2_ACCESS_KEY_ID", "")
SECRET_ACCESS_KEY = sys.argv[3] if len(sys.argv) > 3 else os.getenv("R2_SECRET_ACCESS_KEY", "")
BUCKET_NAME = sys.argv[4] if len(sys.argv) > 4 else os.getenv("R2_BUCKET_NAME", "sirman-diagrams")

def main():
    print("=" * 65)
    print("  SIRMAN DIAGRAM IMAGES -> CLOUDFLARE R2 UPLOADER")
    print("=" * 65)

    if not ACCOUNT_ID or not ACCESS_KEY_ID or not SECRET_ACCESS_KEY:
        print("[NOTICE] Cloudflare R2 Credentials required:")
        print("  python upload_to_cloudflare_r2.py <ACCOUNT_ID> <ACCESS_KEY_ID> <SECRET_ACCESS_KEY> [BUCKET_NAME]")
        print("\nGet your credentials from Cloudflare Dashboard -> R2 -> Manage R2 API Tokens.")
        return

    if not IMG_DIR.exists():
        print(f"[ERROR] Directory {IMG_DIR} not found.")
        return

    # Initialize S3 Client targeting Cloudflare R2 Endpoint
    r2_endpoint = f"https://{ACCOUNT_ID}.r2.cloudflarestorage.com"
    s3_client = boto3.client(
        "s3",
        endpoint_url=r2_endpoint,
        aws_access_key_id=ACCESS_KEY_ID,
        aws_secret_access_key=SECRET_ACCESS_KEY,
        region_name="auto"
    )

    # Check or Create Bucket
    print(f"\n[1/2] Checking Cloudflare R2 Bucket '{BUCKET_NAME}'...")
    try:
        s3_client.head_bucket(Bucket=BUCKET_NAME)
        print("  [OK] Bucket exists.")
    except Exception:
        try:
            print(f"  Creating bucket '{BUCKET_NAME}'...")
            s3_client.create_bucket(Bucket=BUCKET_NAME)
            print("  [OK] Bucket created successfully.")
        except Exception as err:
            print(f"  [Notice] {err}")

    # Upload Images
    png_files = list(IMG_DIR.glob("*.png"))
    print(f"\n[2/2] Uploading {len(png_files)} PNG files to Cloudflare R2...")

    uploaded_count = 0
    for idx, img_path in enumerate(png_files, 1):
        file_name = img_path.name
        r2_key = f"diagram_images/{file_name}"
        print(f"  [{idx}/{len(png_files)}] Uploading {file_name}...", end=" ")

        try:
            s3_client.upload_file(
                Filename=str(img_path),
                Bucket=BUCKET_NAME,
                Key=r2_key,
                ExtraArgs={"ContentType": "image/png"}
            )
            uploaded_count += 1
            print("Done [OK]")
        except Exception as e:
            print(f"Err: {e}")

        time.sleep(0.05)

    print("\n" + "=" * 65)
    print("  [SUCCESS] CLOUDFLARE R2 UPLOAD COMPLETED!")
    print(f"  Uploaded: {uploaded_count}/{len(png_files)} images.")
    print("=" * 65)

if __name__ == "__main__":
    main()
