"""
SUPABASE MIGRATION SCRIPT FOR SIRMAN CATALOG
=============================================
Migrates all Categories (13), Products (208), and Parts (13,149) 
from local sirman_catalog.db to Supabase PostgreSQL Database.

Usage:
  python upload_to_supabase.py <SUPABASE_URL> <SUPABASE_SERVICE_KEY>
"""

import os
import sqlite3
import sys
from pathlib import Path

try:
    from supabase import create_client, Client
except ImportError:
    import subprocess
    print("Installing supabase library...")
    subprocess.run([sys.executable, "-m", "pip", "install", "supabase"], check=True)
    from supabase import create_client, Client

BASE_DIR = Path(__file__).parent
DB_FILE = BASE_DIR / "sirman_catalog.db"

SUPABASE_URL = sys.argv[1] if len(sys.argv) > 1 else os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = sys.argv[2] if len(sys.argv) > 2 else os.getenv("SUPABASE_SERVICE_KEY", "")

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

def main():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("=" * 65)
        print("  ERROR: Supabase Credentials Required!")
        print("=" * 65)
        print("Usage:")
        print("  python upload_to_supabase.py <SUPABASE_URL> <SUPABASE_SERVICE_KEY>")
        print("\nExample:")
        print("  python upload_to_supabase.py https://xyz.supabase.co eyJhbGciOi...")
        return

    print("=" * 65)
    print("  SIRMAN CATALOG -> SUPABASE MIGRATOR")
    print("=" * 65)

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    conn = sqlite3.connect(str(DB_FILE))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Migrate Categories
    print("\n[1/3] Uploading Categories...")
    cursor.execute("SELECT * FROM categories")
    cats = [dict(r) for r in cursor.fetchall()]
    res = supabase.table("categories").upsert(cats).execute()
    print(f"  [OK] Uploaded {len(cats)} categories.")

    # 2. Migrate Products
    print("\n[2/3] Uploading Products...")
    cursor.execute("SELECT * FROM products")
    prods = [dict(r) for r in cursor.fetchall()]
    # Batch upsert in chunks of 100
    batch_size = 100
    for i in range(0, len(prods), batch_size):
        chunk = prods[i:i + batch_size]
        supabase.table("products").upsert(chunk).execute()
        print(f"  Progress: {min(i + batch_size, len(prods))}/{len(prods)} products...")
    print(f"  [OK] Uploaded all {len(prods)} products.")

    # 3. Migrate Parts
    print("\n[3/3] Uploading Spare Parts (13,149 items)...")
    cursor.execute("SELECT product_id, code, name, price, stock, ref, view_name FROM parts")
    parts = [dict(r) for r in cursor.fetchall()]
    
    parts_batch_size = 500
    for i in range(0, len(parts), parts_batch_size):
        chunk = parts[i:i + parts_batch_size]
        supabase.table("parts").upsert(chunk).execute()
        print(f"  Progress: {min(i + parts_batch_size, len(parts))}/{len(parts)} parts...")
    print(f"  [OK] Uploaded all {len(parts)} spare parts.")

    print("\n" + "=" * 65)
    print("  [SUCCESS] MIGRATION COMPLETED SUCCESSFULLY TO SUPABASE!")
    print("=" * 65)

if __name__ == "__main__":
    main()
