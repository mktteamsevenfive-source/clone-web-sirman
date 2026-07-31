import json
import sqlite3
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CATALOG_FILE = ROOT_DIR / "sirman_catalog_data.json"
PARTS_FILE = ROOT_DIR / "sirman_parts.json"
DB_FILE = ROOT_DIR / "sirman_catalog.db"

def sync():
    print("=== SYNCING SQLITE DB WITH JSON DATA ===")
    
    with open(CATALOG_FILE, encoding="utf-8") as f:
        cat_data = json.load(f)
    
    with open(PARTS_FILE, encoding="utf-8") as f:
        parts_data = json.load(f)

    prods = cat_data.get("products", [])
    cats = cat_data.get("categories", [])
    all_parts = parts_data.get("all_parts", [])

    print(f"Loaded {len(cats)} categories, {len(prods)} products, {len(all_parts)} parts.")

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("DROP TABLE IF EXISTS categories")
    c.execute("DROP TABLE IF EXISTS products")
    c.execute("DROP TABLE IF EXISTS parts")

    c.execute("""
        CREATE TABLE categories (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            count INTEGER DEFAULT 0
        )
    """)

    c.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            code TEXT NOT NULL,
            model TEXT NOT NULL,
            serial TEXT,
            category_id TEXT,
            category_name TEXT,
            description TEXT,
            pdf_name TEXT,
            exploded_view_id TEXT,
            parts_count INTEGER DEFAULT 0
        )
    """)

    c.execute("""
        CREATE TABLE parts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            code TEXT NOT NULL,
            name TEXT NOT NULL,
            price REAL DEFAULT 0.0,
            stock INTEGER DEFAULT 0,
            ref TEXT,
            view_name TEXT
        )
    """)

    # Populate categories
    cat_counts = {}
    for p in prods:
        cname = p.get("category_name") or "Other"
        cat_counts[cname] = cat_counts.get(cname, 0) + 1

    for cname in cats:
        cid = cname.lower().replace(" ", "-")
        c.execute("INSERT INTO categories (id, name, count) VALUES (?, ?, ?)",
                  (cid, cname, cat_counts.get(cname, 0)))

    # Populate products
    for p in prods:
        p_id = p.get("id")
        if not p_id:
            continue
        c.execute("""
            INSERT INTO products
            (id, code, model, serial, category_id, category_name, description, pdf_name, exploded_view_id, parts_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            p_id,
            p.get("code", ""),
            p.get("model") or p.get("name", ""),
            p.get("serial", ""),
            p.get("category_id", ""),
            p.get("category_name", ""),
            p.get("description", ""),
            p.get("pdf_name", ""),
            p.get("exploded_view_id", ""),
            p.get("parts_count", 0)
        ))

    # Populate parts
    for pt in all_parts:
        c.execute("""
            INSERT INTO parts (product_id, code, name, price, stock, ref, view_name)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            pt.get("product_id"),
            pt.get("code", ""),
            pt.get("name", ""),
            pt.get("price", 0.0),
            pt.get("stock", 0),
            pt.get("ref", ""),
            pt.get("view_name", "")
        ))

    conn.commit()
    conn.close()
    print("Database sync complete!")

if __name__ == "__main__":
    sync()
