import json
import sqlite3
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CATALOG_FILE = ROOT_DIR / "sirman_catalog_data.json"
PARTS_FILE = ROOT_DIR / "sirman_parts.json"
SIRMAN_DATA = ROOT_DIR / "sirman_data.json"
DB_FILE = ROOT_DIR / "sirman_catalog.db"

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

print("=== MERGING ALL DATASETS (ORIGINAL + NEW SCRAPED DATA) ===")

master_products = {}  # prod_id -> prod_dict
master_parts = {}     # (product_id, part_code) -> part_dict
category_set = set()

NAME_MAP = {
    "meat processors": "Meat Processors",
    "slicers": "Slicers",
    "bar machines": "Bar Machines",
    "cooking machines": "Cooking Machines",
    "packaging machines": "Packaging Machines",
    "scales": "Scales",
    "ozone generators": "Ozone Generators",
    "dishwashers": "Dishwashers",
    "snack and pizza": "Snack and Pizza",
    "food processors": "Food Processors",
    "consumables": "Consumables & Accessories",
    "consumables and accessories": "Consumables & Accessories",
    "laundry": "Laundry",
    "microwaves ovens": "Microwave Ovens",
}

def norm_cat(cname):
    if not cname:
        return "Other"
    return NAME_MAP.get(cname.lower().strip(), cname.strip().title())

# 1. Read sirman_catalog_data.json
if CATALOG_FILE.exists():
    try:
        with open(CATALOG_FILE, encoding="utf-8") as f:
            d = json.load(f)
        prods = d.get("products", [])
        for p in prods:
            pid = p.get("id")
            if pid:
                p["category_name"] = norm_cat(p.get("category_name"))
                master_products[pid] = p
                category_set.add(p["category_name"])
                for pt in p.get("parts", []):
                    key = (pid, pt.get("code"))
                    master_parts[key] = pt
        print(f"[CATALOG_FILE] Loaded {len(prods)} products")
    except Exception as e:
        print(f"[WARN] Error reading CATALOG_FILE: {e}")

# 2. Read sirman_parts.json
if PARTS_FILE.exists():
    try:
        with open(PARTS_FILE, encoding="utf-8") as f:
            d = json.load(f)
        all_parts = d.get("all_parts", [])
        for pt in all_parts:
            pid = pt.get("product_id")
            code = pt.get("code")
            if pid and code:
                key = (pid, code)
                if key not in master_parts:
                    master_parts[key] = pt

        cats = d.get("categories", {})
        for cname, plist in cats.items():
            clean_c = norm_cat(cname)
            category_set.add(clean_c)
            if isinstance(plist, list):
                for p in plist:
                    pid = p.get("id")
                    if pid and pid not in master_products:
                        p["category_name"] = clean_c
                        master_products[pid] = p
        print(f"[PARTS_FILE] Loaded {len(all_parts)} parts and categories")
    except Exception as e:
        print(f"[WARN] Error reading PARTS_FILE: {e}")

# 3. Read sirman_data.json if exists
if SIRMAN_DATA.exists():
    try:
        with open(SIRMAN_DATA, encoding="utf-8") as f:
            d = json.load(f)
        if isinstance(d, list):
            for p in d:
                pid = p.get("id")
                if pid and pid not in master_products:
                    cname = norm_cat(p.get("category_name") or p.get("category"))
                    p["category_name"] = cname
                    master_products[pid] = p
                    category_set.add(cname)
        print(f"[SIRMAN_DATA] Loaded data from {SIRMAN_DATA.name}")
    except Exception:
        pass

# 4. Read SQLite DB sirman_catalog.db
if DB_FILE.exists():
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        for r in c.execute("SELECT id, code, model, serial, category_id, category_name, description, pdf_name, exploded_view_id, parts_count FROM products").fetchall():
            pid = r[0]
            if pid not in master_products:
                cname = norm_cat(r[5])
                master_products[pid] = {
                    "id": pid,
                    "code": r[1],
                    "model": r[2],
                    "serial": r[3],
                    "category_id": r[4],
                    "category_name": cname,
                    "description": r[6],
                    "pdf_name": r[7],
                    "exploded_view_id": r[8],
                    "parts_count": r[9]
                }
                category_set.add(cname)

        for r in c.execute("SELECT product_id, code, name, price, stock, ref, view_name FROM parts").fetchall():
            pid = r[0]
            code = r[1]
            if pid and code:
                key = (pid, code)
                if key not in master_parts:
                    master_parts[key] = {
                        "product_id": pid,
                        "code": code,
                        "name": r[2],
                        "price": r[3],
                        "stock": r[4],
                        "ref": r[5],
                        "view_name": r[6]
                    }
        conn.close()
        print(f"[SQLITE DB] Merged data from {DB_FILE.name}")
    except Exception as e:
        print(f"[WARN] Error reading DB: {e}")

print(f"\n[MASTER TOTAL] Unique Products: {len(master_products):,} | Unique Parts: {len(master_parts):,} | Categories: {len(category_set)}")

# Write updated sirman_catalog_data.json
prod_list = list(master_products.values())
with open(CATALOG_FILE, "w", encoding="utf-8") as f:
    json.dump({
        "categories": sorted(list(category_set)),
        "products": prod_list
    }, f, ensure_ascii=False, indent=2)

# Write updated sirman_parts.json
cat_map = {}
for p in prod_list:
    cname = p.get("category_name", "Other")
    cat_map.setdefault(cname, []).append(p)

part_list = list(master_parts.values())
with open(PARTS_FILE, "w", encoding="utf-8") as f:
    json.dump({
        "categories": cat_map,
        "all_parts": part_list,
        "summary": {
            "total_categories": len(cat_map),
            "total_products": len(prod_list),
            "total_parts": len(part_list)
        }
    }, f, ensure_ascii=False, indent=2)

# Rebuild SQLite database
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()
c.execute("DROP TABLE IF EXISTS categories")
c.execute("DROP TABLE IF EXISTS products")
c.execute("DROP TABLE IF EXISTS parts")

c.execute("CREATE TABLE categories (id TEXT PRIMARY KEY, name TEXT NOT NULL, count INTEGER DEFAULT 0)")
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

# Populate Categories table
cat_counts = {}
for p in prod_list:
    cname = p.get("category_name", "Other")
    cat_counts[cname] = cat_counts.get(cname, 0) + 1

for cname in sorted(list(category_set)):
    cid = cname.lower().replace(" ", "-").replace("&", "and")
    c.execute("INSERT INTO categories (id, name, count) VALUES (?, ?, ?)", (cid, cname, cat_counts.get(cname, 0)))

# Populate Products table
for p in prod_list:
    pid = p.get("id")
    c.execute("""
        INSERT OR REPLACE INTO products (id, code, model, serial, category_id, category_name, description, pdf_name, exploded_view_id, parts_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        pid,
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

# Populate Parts table
for pt in part_list:
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

print("[SUCCESS] All datasets merged and updated in JSON and SQLite DB!")
