import json
import html

with open("sirman_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

api = data.get("api_responses", {})
all_cats = api.get("https://api-service.sirman.com/service-dwh/categories", [])

print("=" * 65)
print(f"TOTAL CATEGORIES IN RAW SIRMAN_DATA.JSON: {len(all_cats)}")
print("=" * 65)

top_groups = [c for c in all_cats if c.get("father") == 0 and c.get("type") == "group"]

for g in top_groups:
    en_name = html.unescape(g.get("i18n", {}).get("en", g.get("name")))
    cat_id = g.get("id")
    subcats = [c for c in all_cats if c.get("father") == cat_id]
    print(f"Group ID {cat_id:2d}: '{en_name:<30}' -> Total Subcategories/Models: {len(subcats)}")

print("=" * 65)
