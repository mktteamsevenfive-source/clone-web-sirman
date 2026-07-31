"""
export_to_csv.py
================
Exports all data from Supabase/SQLite into clean CSV files:
- exports/categories.csv
- exports/products.csv
- exports/parts.csv
"""
import sys, sqlite3, csv
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_FILE      = PROJECT_ROOT / "sirman_catalog.db"
EXPORT_DIR   = PROJECT_ROOT / "exports"
EXPORT_DIR.mkdir(exist_ok=True)

conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

# 1. Export Categories
cat_rows = c.execute("SELECT id, name, count FROM categories ORDER BY name").fetchall()
cat_file = EXPORT_DIR / "categories.csv"
with open(cat_file, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["Category ID", "Category Name", "Product Count"])
    writer.writerows(cat_rows)
print(f"[OK] Exported categories -> {cat_file} ({len(cat_rows)} rows)")

# 2. Export Products
prod_rows = c.execute("""
    SELECT id, code, model, serial, category_id, category_name, description, pdf_name, exploded_view_id, parts_count
    FROM products ORDER BY category_name, model
""").fetchall()
prod_file = EXPORT_DIR / "products.csv"
with open(prod_file, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["Product ID", "Code", "Model Name", "Serial", "Category Slug", "Category Name", "Description", "PDF Name", "Exploded View ID", "Parts Count"])
    writer.writerows(prod_rows)
print(f"[OK] Exported products   -> {prod_file} ({len(prod_rows)} rows)")

# 3. Export Parts
parts_rows = c.execute("""
    SELECT p.product_id, pr.model, pr.category_name, p.code, p.name, p.price, p.stock, p.ref, p.view_name
    FROM parts p
    LEFT JOIN products pr ON p.product_id = pr.id
    ORDER BY pr.category_name, pr.model, p.code
""").fetchall()
parts_file = EXPORT_DIR / "parts.csv"
with open(parts_file, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["Product ID", "Product Model", "Category", "Part Code", "Part Name", "Price", "Stock", "Ref Position", "Exploded View Name"])
    writer.writerows(parts_rows)
print(f"[OK] Exported parts      -> {parts_file} ({len(parts_rows)} rows)")

conn.close()
print("\n🎉 ALL CSV EXPORTS COMPLETED!")
