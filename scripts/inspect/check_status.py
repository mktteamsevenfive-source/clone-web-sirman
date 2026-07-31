import json
import sqlite3
import os

print("=== SCRAPED DATA STATUS ===")

if os.path.exists('sirman_catalog_data.json'):
    with open('sirman_catalog_data.json', encoding='utf-8') as f:
        cat_data = json.load(f)
    print('\nsirman_catalog_data.json:')
    if isinstance(cat_data, dict):
        print('  Categories count:', len(cat_data.get('categories', [])))
        print('  Categories list:', cat_data.get('categories', []))
        prods = cat_data.get('products', [])
        print('  Total Products:', len(prods))

if os.path.exists('sirman_parts.json'):
    with open('sirman_parts.json', encoding='utf-8') as f:
        parts_data = json.load(f)
    print('\nsirman_parts.json:')
    if isinstance(parts_data, dict):
        cats = parts_data.get('categories', {})
        print('  Category keys:', len(cats))
        for k, v in cats.items():
            print(f'    - {k}: {len(v)} entries')
        all_parts = parts_data.get('all_parts', [])
        print('  Total all_parts:', len(all_parts))
        print('  Summary block:', parts_data.get('summary', {}))

if os.path.exists('sirman_catalog.db'):
    conn = sqlite3.connect('sirman_catalog.db')
    c = conn.cursor()
    tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    print('\nsirman_catalog.db tables:', tables)
    for t in tables:
        cnt = c.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
        print(f'  Table {t}: {cnt} rows')
    conn.close()

if os.path.exists('apollo_hotspots_data.json'):
    with open('apollo_hotspots_data.json', encoding='utf-8') as f:
        hs = json.load(f)
    print('\napollo_hotspots_data.json type:', type(hs))
    if isinstance(hs, dict):
        print('  Keys:', len(hs))
    elif isinstance(hs, list):
        print('  Items:', len(hs))
