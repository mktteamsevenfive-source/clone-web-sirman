import sqlite3
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DB_FILE = ROOT_DIR / "sirman_catalog.db"

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

# Case-insensitive grouping
rows = c.execute("""
    SELECT 
        CASE 
            WHEN LOWER(p.category_name) = 'meat processors' THEN 'Meat Processors'
            WHEN LOWER(p.category_name) = 'slicers' THEN 'Slicers'
            WHEN LOWER(p.category_name) = 'food processors' THEN 'Food Processors'
            WHEN LOWER(p.category_name) = 'snack and pizza' THEN 'Snack and Pizza'
            WHEN LOWER(p.category_name) = 'bar machines' THEN 'Bar Machines'
            WHEN LOWER(p.category_name) = 'cooking machines' THEN 'Cooking Machines'
            WHEN LOWER(p.category_name) = 'packaging machines' THEN 'Packaging Machines'
            WHEN LOWER(p.category_name) = 'microwaves ovens' THEN 'Microwave Ovens'
            WHEN LOWER(p.category_name) = 'consumables' THEN 'Consumables & Accessories'
            WHEN LOWER(p.category_name) = 'ozone generators' THEN 'Ozone Generators'
            WHEN LOWER(p.category_name) = 'dishwashers' THEN 'Dishwashers'
            WHEN LOWER(p.category_name) = 'laundry' THEN 'Laundry'
            WHEN LOWER(p.category_name) = 'scales' THEN 'Scales'
            ELSE p.category_name
        END AS clean_cat,
        COUNT(DISTINCT p.id) as product_count,
        COUNT(pt.id) as parts_count
    FROM products p
    LEFT JOIN parts pt ON p.id = pt.product_id
    GROUP BY clean_cat
    ORDER BY product_count DESC
""").fetchall()

conn.close()

print(f"{'ลำดับ':<4} | {'ชื่อหมวดหมู่ (Category Name)':<32} | {'จำนวนสินค้า (Products)':<22} | {'จำนวนอะไหล่ (Parts)':<20}")
print("-" * 88)

total_prods = 0
total_parts = 0

for i, (cname, prod_cnt, part_cnt) in enumerate(rows, 1):
    total_prods += prod_cnt
    total_parts += part_cnt
    print(f"{i:<4} | {cname:<32} | {prod_cnt:<22,} | {part_cnt:<20,}")

print("-" * 88)
print(f"{'รวม':<4} | {'ยอดรวมทั้งหมด (TOTAL)':<32} | {total_prods:<22,} | {total_parts:<20,}")
