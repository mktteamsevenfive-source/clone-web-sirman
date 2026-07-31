import json

with open('sirman_parts.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=" * 60)
print("SIRMAN_PARTS.JSON CATEGORY STATS:")
print("=" * 60)

for cat_name, cat in data.get('categories', {}).items():
    prods = cat.get('products', [])
    total_parts = sum(len(p.get('parts', [])) for p in prods)
    print(f"Category: '{cat_name}' | Products: {len(prods)} | Parts: {total_parts}")

print("=" * 60)
