import json
import sqlite3
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CATALOG_FILE = ROOT_DIR / "sirman_catalog_data.json"
DB_FILE = ROOT_DIR / "sirman_catalog.db"

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

print("=== REBUILDING CLEAN SIRMAN_CATALOG_DATA.JSON FROM SQLITE ===")

conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

prods = []
rows = c.execute("SELECT id, code, model, serial, category_id, category_name, description, pdf_name, exploded_view_id, parts_count FROM products").fetchall()

categories = set()

for r in rows:
    pid = r[0]
    cname = r[5] or "Other"
    categories.add(cname)
    
    # Get parts for product
    pts = c.execute("SELECT code, name, price, stock, ref, view_name FROM parts WHERE product_id = ?", (pid,)).fetchall()
    part_objs = []
    for pt in pts:
        part_objs.append({
            "product_id": pid,
            "code": pt[0],
            "name": pt[1],
            "price": pt[2],
            "stock": pt[3],
            "ref": pt[4],
            "view_name": pt[5]
        })

    prods.append({
        "id": pid,
        "code": r[1],
        "model": r[2],
        "serial": r[3],
        "category_id": r[4],
        "category_name": cname,
        "description": r[6],
        "pdf_name": r[7],
        "exploded_view_id": r[8],
        "parts_count": len(part_objs),
        "parts": part_objs
    })

conn.close()

with open(CATALOG_FILE, "w", encoding="utf-8") as f:
    json.dump({
        "categories": sorted(list(categories)),
        "products": prods
    }, f, ensure_ascii=False, indent=2)

print(f"[SUCCESS] Rebuilt clean {CATALOG_FILE.name} with {len(prods)} products and {len(categories)} categories!")
