import json
import html
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

with open("sirman_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

api = data.get("api_responses", {})
all_cats = api.get("https://api-service.sirman.com/service-dwh/categories", [])

# Find all categories under Group 7 (Meat Processors)
# Filter only type="subcat" or leaf items
group_7_subcats = [c for c in all_cats if c.get("father") == 7]

print("=" * 65)
print(f"DIRECT SUBCATEGORIES UNDER MEAT PROCESSORS (GROUP 7): {len(group_7_subcats)}")
print("=" * 65)

all_meat_models = []

for sc in group_7_subcats:
    sc_id = sc.get("id")
    sc_name = html.unescape(sc.get("i18n", {}).get("en", sc.get("name")))
    
    # Get children under sc_id
    children = [c for c in all_cats if c.get("father") == sc_id]
    if not children:
        all_meat_models.append(sc)
        print(f"  [Model] ID={sc_id:4d} | {sc_name}")
    else:
        print(f"  [Category] ID={sc_id:4d} | {sc_name} ({len(children)} models)")
        for child in children:
            child_name = html.unescape(child.get("i18n", {}).get("en", child.get("name")))
            all_meat_models.append(child)
            print(f"      ---> [Model] ID={child.get('id'):4d} | {child_name}")

print("=" * 65)
print(f"TOTAL MEAT PROCESSORS MODELS FOUND IN SIRMAN_DATA.JSON: {len(all_meat_models)}")
print("=" * 65)
