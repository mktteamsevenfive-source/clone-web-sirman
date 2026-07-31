"""
SIRMAN CATALOG SQLITE DATABASE BUILDER
======================================
Builds SQLite database `sirman_catalog.db` with indexed tables:
1. categories (id, sirman_id, name, count, icon)
2. products (id, code, model, serial, category_id, category_name, description, pdf_name, exploded_view_id, parts_count)
3. parts (id, product_id, code, name, price, stock, ref, view_name)
"""

import json
import os
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / "sirman_catalog_data.json"
FINAL_DB_FILE = BASE_DIR / "sirman_catalog.db"


def build_database():
    print("=" * 65)
    print("  BUILDING SIRMAN SQLITE DATABASE (sirman_catalog.db)")
    print("=" * 65)

    if not DATA_FILE.exists():
        print(f"[ERROR] Source JSON file missing: {DATA_FILE}")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        catalog_data = json.load(f)

    categories = catalog_data.get("categories", [])
    products = catalog_data.get("products", [])

    temp_dir = Path(tempfile.gettempdir())
    temp_db = temp_dir / "temp_sirman_catalog.db"

    if temp_db.exists():
        try:
            temp_db.unlink()
        except Exception:
            pass

    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()

    print("\n[STEP 1] Creating database schema & indexes...")
    
    cursor.execute("""
        CREATE TABLE categories (
            id TEXT PRIMARY KEY,
            sirman_id INTEGER,
            name TEXT NOT NULL,
            count INTEGER DEFAULT 0,
            icon TEXT
        );
    """)

    cursor.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            code TEXT NOT NULL,
            model TEXT NOT NULL,
            serial TEXT,
            category_id TEXT NOT NULL,
            category_name TEXT NOT NULL,
            description TEXT,
            pdf_name TEXT,
            exploded_view_id TEXT,
            parts_count INTEGER DEFAULT 0,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        );
    """)

    cursor.execute("""
        CREATE TABLE parts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            code TEXT NOT NULL,
            name TEXT NOT NULL,
            price REAL DEFAULT 0.0,
            stock INTEGER DEFAULT 0,
            ref TEXT,
            view_name TEXT,
            FOREIGN KEY (product_id) REFERENCES products(id)
        );
    """)

    # High Performance Indexes
    cursor.execute("CREATE INDEX idx_products_category ON products(category_id);")
    cursor.execute("CREATE INDEX idx_products_model ON products(model);")
    cursor.execute("CREATE INDEX idx_parts_product ON parts(product_id);")
    cursor.execute("CREATE INDEX idx_parts_code ON parts(code);")

    conn.commit()

    print("[STEP 2] Inserting Categories...")
    for cat in categories:
        cursor.execute("""
            INSERT INTO categories (id, sirman_id, name, count, icon)
            VALUES (?, ?, ?, ?, ?)
        """, (cat["id"], cat.get("sirman_id"), cat["name"], cat.get("count", 0), cat.get("icon", "")))

    conn.commit()
    print(f"  --> Inserted {len(categories)} categories.")

    print("\n[STEP 3] Inserting Products & Spare Parts...")
    total_parts_inserted = 0

    for p in products:
        p_id = p["id"]
        cursor.execute("""
            INSERT INTO products (id, code, model, serial, category_id, category_name, description, pdf_name, exploded_view_id, parts_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            p_id,
            p["code"],
            p["model"],
            p.get("serial", ""),
            p["categoryId"],
            p["category"],
            p.get("description", ""),
            p.get("pdfName", ""),
            str(p.get("explodedViewId", "")),
            p.get("partsCount", 0)
        ))

        parts_to_insert = []
        for part in p.get("parts", []):
            parts_to_insert.append((
                p_id,
                part.get("code", ""),
                part.get("name", ""),
                float(part.get("price", 0.0)),
                int(part.get("stock", 0)),
                str(part.get("ref", "")),
                part.get("view_name", "")
            ))

        if parts_to_insert:
            cursor.executemany("""
                INSERT INTO parts (product_id, code, name, price, stock, ref, view_name)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, parts_to_insert)
            total_parts_inserted += len(parts_to_insert)

    conn.commit()
    conn.close()

    # Copy to workspace destination
    if FINAL_DB_FILE.exists():
        try:
            FINAL_DB_FILE.unlink()
        except Exception:
            pass

    shutil.copy2(str(temp_db), str(FINAL_DB_FILE))

    db_size_mb = FINAL_DB_FILE.stat().st_size / (1024 * 1024)

    print("\n" + "=" * 65)
    print("  SQLITE DATABASE CREATED SUCCESSFULLY!")
    print(f"  Database file : {FINAL_DB_FILE}")
    print(f"  File Size     : {db_size_mb:.2f} MB")
    print(f"  Categories    : {len(categories)}")
    print(f"  Products      : {len(products)}")
    print(f"  Spare Parts   : {total_parts_inserted}")
    print("=" * 65)


if __name__ == "__main__":
    build_database()
