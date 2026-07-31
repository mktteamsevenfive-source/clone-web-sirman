"""
clean_and_reexport.py
======================
1. Removes 69,035 orphan parts from SQLite database
2. Exports clean CSV files to exports/sirman_parts_clean.csv and exports/sirman_products.csv
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

# 1. Clean orphan parts from SQLite
c.execute("DELETE FROM parts WHERE product_id IS NULL OR product_id = 0 OR code IS NULL OR code = ''")
deleted = c.rowcount
conn.commit()
print(f"[CLEAN] Removed {deleted:,} orphan parts (without product_id or code) from SQLite database.")

valid_parts_cnt = c.execute("SELECT COUNT(*) FROM parts").fetchone()[0]
print(f"[VALID PARTS] Total valid parts linked to products: {valid_parts_cnt:,}")

# Helper to write CSV safely
def write_csv_safe(file_path, header, rows):
    try:
        with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)
        print(f"[OK] Exported -> {file_path} ({len(rows):,} rows)")
    except PermissionError:
        alt_path = file_path.parent / f"v2_{file_path.name}"
        with open(alt_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)
        print(f"[OK] (Original file locked by Excel) Exported to -> {alt_path} ({len(rows):,} rows)")

# 2. Export Categories
cat_rows = c.execute("SELECT id, name, count FROM categories ORDER BY name").fetchall()
write_csv_safe(EXPORT_DIR / "categories.csv", ["Category ID", "Category Name", "Product Count"], cat_rows)

# 3. Export Products
prod_rows = c.execute("""
    SELECT id, code, model, serial, category_id, category_name, description, pdf_name, exploded_view_id, parts_count
    FROM products ORDER BY category_name, model
""").fetchall()
write_csv_safe(EXPORT_DIR / "products.csv", ["Product ID", "Code", "Model Name", "Serial", "Category Slug", "Category Name", "Description", "PDF Name", "Exploded View ID", "Parts Count"], prod_rows)

# 4. Export Parts (INNER JOIN ensures 100% valid product metadata)
parts_rows = c.execute("""
    SELECT p.product_id, pr.model, pr.category_name, p.code, p.name, p.price, p.stock, p.ref, p.view_name
    FROM parts p
    INNER JOIN products pr ON p.product_id = pr.id
    ORDER BY pr.category_name, pr.model, p.code
""").fetchall()
write_csv_safe(EXPORT_DIR / "sirman_parts_clean.csv", ["Product ID", "Product Model", "Category", "Part Code", "Part Name", "Price", "Stock", "Ref Position", "Exploded View Name"], parts_rows)
write_csv_safe(EXPORT_DIR / "parts.csv", ["Product ID", "Product Model", "Category", "Part Code", "Part Name", "Price", "Stock", "Ref Position", "Exploded View Name"], parts_rows)

conn.close()
print("\n🎉 CLEAN CSV EXPORT COMPLETED SUCCESSFULLY!")
