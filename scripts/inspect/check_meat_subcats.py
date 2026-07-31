import json
import requests
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
HEADERS_FILE = ROOT_DIR / "sirman_headers.json"
API_BASE = "https://api-service.sirman.com"

with open(HEADERS_FILE, encoding="utf-8") as f:
    data = json.load(f)

hdrs = data.get("headers", {})
cookies = data.get("cookies", [])

session = requests.Session()
clean = {k: v for k, v in hdrs.items() if not k.startswith(":")}
session.headers.update(clean)
cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
if cookie_str:
    session.headers["cookie"] = cookie_str

# Get full categories
cats = session.get(f"{API_BASE}/service-dwh/categories", timeout=10).json()

print(f"Total categories: {len(cats)}")

# Find all children of father=7 (Meat Processors)
meat_subcats = [c for c in cats if c.get("father") == 7 or c.get("id") == 7]
print(f"Subcategories under Meat Processors (father=7): {len(meat_subcats)}")

total_meat_prods = 0
for sc in meat_subcats:
    sc_id = sc.get("id")
    sc_name = sc.get("i18n", {}).get("en") or sc.get("name")
    r = session.get(f"{API_BASE}/service-dwh/products?category={sc_id}&productionFilter=all&page=1&pageSize=1", timeout=5)
    if r.status_code == 200:
        d = r.json()
        cnt = d.get("totalItems", 0)
        total_meat_prods += cnt
        if cnt > 0:
            print(f"  Subcat ID {sc_id:4d} | '{sc_name}': {cnt} products")

print(f"\nTOTAL MEAT PROCESSORS PRODUCTS ACROSS SUBCATEGORIES: {total_meat_prods}")
