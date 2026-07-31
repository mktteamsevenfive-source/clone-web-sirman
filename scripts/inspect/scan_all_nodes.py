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

cats = session.get(f"{API_BASE}/service-dwh/categories", timeout=10).json()

# Build map father -> children
by_father = {}
for c in cats:
    f_id = c.get("father", 0)
    by_father.setdefault(f_id, []).append(c)

print(f"Top-level groups (father=0): {len(by_father.get(0, []))}")
for top in by_father.get(0, []):
    top_id = top.get("id")
    top_name = top.get("i18n", {}).get("en") or top.get("name")
    children = by_father.get(top_id, [])
    print(f"Top Group [{top_id:2d}] '{top_name}' -> {len(children)} direct children")

# Test querying product count for any category node across all 1282 nodes
nodes_with_products = []
total_found = 0

for c in cats:
    cid = c.get("id")
    cname = c.get("i18n", {}).get("en") or c.get("name")
    r = session.get(f"{API_BASE}/service-dwh/products?category={cid}&productionFilter=all&page=1&pageSize=1", timeout=5)
    if r.status_code == 200:
        d = r.json()
        cnt = d.get("totalItems", 0)
        if cnt > 0:
            nodes_with_products.append((cid, cname, cnt))
            total_found += cnt
            print(f"  [FOUND] Cat ID {cid:4d} | '{cname}': {cnt} products")

print(f"\n==========================================")
print(f"TOTAL NODES WITH PRODUCTS: {len(nodes_with_products)} / {len(cats)}")
print(f"TOTAL PRODUCTS SUM: {total_found}")
print(f"==========================================")
