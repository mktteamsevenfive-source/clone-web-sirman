"""
Parse sirman_data.json and generate real app.js data
"""
import json, re, html

with open("sirman_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

api = data.get("api_responses", {})

# Get the full categories list
all_categories_url = "https://api-service.sirman.com/service-dwh/categories"
customer_url = "https://api-service.sirman.com/service-dwh/categories/customer-categories"

all_cats = api.get(all_categories_url, [])
customer_cats = api.get(customer_url, [])

print(f"Total categories: {len(all_cats)}")
print(f"Customer categories: {len(customer_cats)}")

# Filter top-level groups (father=0, type=group)
top_groups = [c for c in all_cats if c.get("father") == 0 and c.get("type") == "group"]
print(f"\nTop-level groups ({len(top_groups)}):")
for g in top_groups:
    en_name = html.unescape(g["i18n"].get("en", g["name"]))
    cat_id = g["id"]
    # Count subcategories
    subcats = [c for c in all_cats if c.get("father") == cat_id]
    print(f"  id={cat_id}: {en_name} ({len(subcats)} subcategories)")

# Get subcategories for each group
print("\n\nDetailed subcategories per group:")
for g in top_groups:
    en_name = html.unescape(g["i18n"].get("en", g["name"]))
    cat_id = g["id"]
    subcats = [c for c in all_cats if c.get("father") == cat_id]
    print(f"\n[{en_name}] (id={cat_id})")
    for s in subcats[:10]:  # show first 10
        sub_en = html.unescape(s["i18n"].get("en", s["name"]))
        print(f"  - id={s['id']}: {sub_en}")
    if len(subcats) > 10:
        print(f"  ... and {len(subcats)-10} more")

# Now generate JS-compatible data
print("\n\n=== GENERATING JS DATA ===\n")
js_categories = []
for g in top_groups:
    en_name = html.unescape(g["i18n"].get("en", g["name"]))
    cat_id = g["id"]
    subcats = [c for c in all_cats if c.get("father") == cat_id]
    
    # Create slug
    slug = re.sub(r'[^a-z0-9]+', '-', en_name.lower()).strip('-')
    
    js_categories.append({
        "id": slug,
        "sirman_id": cat_id,
        "name": en_name,
        "count": len(subcats),
        "subcategories": [
            {
                "id": s["id"],
                "name": html.unescape(s["i18n"].get("en", s["name"])),
            }
            for s in subcats[:20]
        ]
    })

print(json.dumps(js_categories, indent=2, ensure_ascii=False))
