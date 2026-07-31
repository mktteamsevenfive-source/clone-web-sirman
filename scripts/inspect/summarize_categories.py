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

conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

# Query counts per category from SQLite DB
rows = c.execute("""
    SELECT 
        p.category_name, 
        COUNT(DISTINCT p.id) as product_count, 
        COUNT(pt.id) as parts_count 
    FROM products p 
    LEFT JOIN parts pt ON p.id = pt.product_id 
    GROUP BY p.category_name 
    ORDER BY product_count DESC
""").fetchall()

conn.close()

print(f"{'Category Name':<30} | {'Products':<10} | {'Parts':<12}")
print("-" * 60)

total_prods = 0
total_parts = 0

for cat_name, prod_cnt, part_cnt in rows:
    c_name = cat_name or "Unknown"
    total_prods += prod_cnt
    total_parts += part_cnt
    print(f"{c_name:<30} | {prod_cnt:<10,} | {part_cnt:<12,}")

print("-" * 60)
print(f"{'TOTAL':<30} | {total_prods:<10,} | {total_parts:<12,}")
