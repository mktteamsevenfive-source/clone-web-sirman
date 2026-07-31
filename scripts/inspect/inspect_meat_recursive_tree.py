import json
import html

with open("sirman_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

api = data.get("api_responses", {})
all_cats = api.get("https://api-service.sirman.com/service-dwh/categories", [])

print("=" * 65)
print("RECURSIVE CATEGORY TREE FOR MEAT PROCESSORS (GROUP 7):")
print("=" * 65)

visited = set()

def print_tree(cat_id, depth=0):
    if cat_id in visited or depth > 10:
        return 0
    visited.add(cat_id)

    children = [c for c in all_cats if c.get("father") == cat_id and c.get("id") != cat_id]
    count = len(children)

    for c in children:
        c_id = c.get("id")
        name = html.unescape(c.get("i18n", {}).get("en", c.get("name")))
        c_type = c.get("type")
        indent = "  " * depth
        sub_children = [sc for sc in all_cats if sc.get("father") == c_id and sc.get("id") != c_id]
        print(f"{indent}- [{c_type}] ID={c_id:4d}: {name:<35} (sub: {len(sub_children)})")
        if sub_children:
            count += print_tree(c_id, depth + 1)
    return count

total = print_tree(7)
print("=" * 65)
print(f"Total descendant categories under Meat Processors (Group 7): {total}")
print("=" * 65)
