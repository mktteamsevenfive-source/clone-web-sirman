import json

d = json.load(open('sirman_data.json', encoding='utf-8'))
cats = d.get('api_responses', {}).get('https://api-service.sirman.com/service-dwh/categories', [])

by_father = {}
for c in cats:
    by_father.setdefault(c.get('father', 0), []).append(c)

roots = by_father.get(0, [])
print(f"Total categories in API: {len(cats)}")
print(f"Root categories (father=0): {len(roots)}")
print("-" * 65)

def count_all_descendants(cat_id, visited=None):
    if visited is None:
        visited = set()
    if cat_id in visited:
        return 0
    visited.add(cat_id)
    subs = by_father.get(cat_id, [])
    total = len(subs)
    for s in subs:
        total += count_all_descendants(s['id'], visited)
    return total

def get_all_leaf_ids(cat_id, visited=None):
    if visited is None:
        visited = set()
    if cat_id in visited:
        return []
    visited.add(cat_id)
    subs = by_father.get(cat_id, [])
    if not subs:
        return [cat_id]
    res = []
    for s in subs:
        res.extend(get_all_leaf_ids(s['id'], visited))
    return res


all_category_ids = [c['id'] for c in cats]
print(f"Total unique Category IDs to scrape: {len(all_category_ids)}")

for r in roots:
    name = r.get('i18n', {}).get('en') or r.get('name')
    desc_count = count_all_descendants(r['id'])
    leaf_count = len(get_all_leaf_ids(r['id']))
    print(f"Root {r['id']:2d}: {name:<32} | Subcategories: {desc_count:4d} | Leaf categories: {leaf_count:4d}")
