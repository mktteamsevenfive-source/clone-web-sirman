import json
import sqlite3
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CATALOG_FILE = ROOT_DIR / "sirman_catalog_data.json"
PARTS_FILE = ROOT_DIR / "sirman_parts.json"
DB_FILE = ROOT_DIR / "sirman_catalog.db"

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

print("=== NORMALIZING CATEGORY NAMES ACROSS DB AND JSON FILES ===")

conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

# Map lower -> Title Case name
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

# Update products category_name in SQLite
for row in c.execute("SELECT DISTINCT category_name FROM products").fetchall():
    old_name = row[0]
    if old_name:
        clean_name = NAME_MAP.get(old_name.lower(), old_name.title())
        c.execute("UPDATE products SET category_name = ? WHERE category_name = ?", (clean_name, old_name))

# Update categories table
c.execute("DELETE FROM categories")
cat_rows = c.execute("""
    SELECT category_name, COUNT(*) FROM products GROUP BY category_name
""").fetchall()

for cname, cnt in cat_rows:
    cid = cname.lower().replace(" ", "-").replace("&", "and")
    c.execute("INSERT INTO categories (id, name, count) VALUES (?, ?, ?)", (cid, cname, cnt))

conn.commit()

# Clean up JSON files as well
if CATALOG_FILE.exists():
    with open(CATALOG_FILE, encoding="utf-8") as f:
        cat_data = json.load(f)
    prods = cat_data.get("products", [])
    unique_cats = set()
    for p in prods:
        cname = p.get("category_name") or "Other"
        clean = NAME_MAP.get(cname.lower(), cname.title())
        p["category_name"] = clean
        unique_cats.add(clean)
    cat_data["categories"] = sorted(list(unique_cats))
    with open(CATALOG_FILE, "w", encoding="utf-8") as f:
        json.dump(cat_data, f, ensure_ascii=False, indent=2)

if PARTS_FILE.exists():
    with open(PARTS_FILE, encoding="utf-8") as f:
        parts_data = json.load(f)
    old_cats = parts_data.get("categories", {})
    new_cats = {}
    for cname, plist in old_cats.items():
        clean = NAME_MAP.get(cname.lower(), cname.title())
        new_cats.setdefault(clean, []).extend(plist)
    parts_data["categories"] = new_cats
    with open(PARTS_FILE, "w", encoding="utf-8") as f:
        json.dump(parts_data, f, ensure_ascii=False, indent=2)

print("Normalization complete!")
