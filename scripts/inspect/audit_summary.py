import sys, sqlite3
sys.stdout.reconfigure(encoding="utf-8")

conn = sqlite3.connect("sirman_catalog.db")
c = conn.cursor()

sample = c.execute("SELECT id, code, model FROM products WHERE category_name = 'Meat Processors' AND parts_count = 0 LIMIT 10").fetchall()
print("Sample Meat Processors with 0 parts:")
for r in sample:
    print(f"  ID: {r[0]} | Code: {r[1]} | Model: {r[2]}")

conn.close()
