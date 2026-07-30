import json
import requests

# Load categories
d = json.load(open('sirman_data.json', encoding='utf-8'))
cats = d.get('api_responses', {}).get('https://api-service.sirman.com/service-dwh/categories', [])

# Map father -> root category
root_by_cat = {}
by_id = {c['id']: c for c in cats}

def find_root_id(cat_id, visited=None):
    if visited is None:
        visited = set()
    if cat_id in visited or cat_id not in by_id:
        return cat_id
    visited.add(cat_id)
    c = by_id[cat_id]
    father = c.get('father', 0)
    if father == 0 or father not in by_id:
        return cat_id
    return find_root_id(father, visited)

root_map = {}
for c in cats:
    root_map[c['id']] = find_root_id(c['id'])

print(f"Total categories: {len(cats)}")

# Sample root IDs
roots_info = {}
for cid, root_id in root_map.items():
    roots_info.setdefault(root_id, []).append(cid)

for r_id, member_ids in roots_info.items():
    r_name = by_id.get(r_id, {}).get('i18n', {}).get('en') or by_id.get(r_id, {}).get('name')
    print(f"Root {r_id:2d}: {str(r_name):32} -> {len(member_ids):4d} category IDs")
