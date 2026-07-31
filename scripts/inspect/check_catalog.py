import sys, json
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(".")
d = json.load(open(ROOT / "sirman_catalog_data.json", encoding="utf-8"))
prods = d["products"]
print(f"Total products: {len(prods)}")

# Sample
print("\nSample products:")
for p in prods[:3]:
    print(f"  id={p.get('id')} model={p.get('model','')} category_id={p.get('category_id','')} category_name={p.get('category_name','')}")

# Check categories distribution
cat_ids = {}
for p in prods:
    cid = str(p.get("category_id", ""))
    cat_ids[cid] = cat_ids.get(cid, 0) + 1

print("\nCategory ID distribution (unique category_id values):")
for cid, cnt in sorted(cat_ids.items(), key=lambda x: -x[1]):
    print(f"  '{cid}' => {cnt} products")
