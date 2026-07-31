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

# Test Category 7 (Meat Processors)
r = session.get(f"{API_BASE}/service-dwh/products?category=7&productionFilter=all&page=1&pageSize=100", timeout=10)
print("HTTP Status for Category 7 (Meat Processors):", r.status_code)
if r.status_code == 200:
    res = r.json()
    print("Keys in response:", res.keys())
    print("totalItems:", res.get("totalItems"))
    print("totalPages:", res.get("totalPages"))
    print("items on page 1:", len(res.get("items", [])))

# Test main categories list
cat_res = session.get(f"{API_BASE}/service-dwh/categories", timeout=10)
if cat_res.status_code == 200:
    cats = cat_res.json()
    print(f"\nTotal Category Nodes in Sirman Tree: {len(cats)}")
    print("Top categories:")
    for c in cats:
        c_id = c.get("id")
        c_name = c.get("i18n", {}).get("en") or c.get("name")
        # Query totalItems for each top category
        pr = session.get(f"{API_BASE}/service-dwh/products?category={c_id}&productionFilter=all&page=1&pageSize=1", timeout=5)
        if pr.status_code == 200:
            p_data = pr.json()
            t_items = p_data.get("totalItems") if isinstance(p_data, dict) else "N/A"
            print(f"  Category ID {c_id:4d} | '{c_name}': {t_items} products")
