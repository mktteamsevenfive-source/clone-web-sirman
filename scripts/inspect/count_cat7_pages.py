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

# Count products for Category 7 (Meat Processors) by fetching pages with pageSize=100
page = 1
total_items = 0

print("=== COUNTING ALL PRODUCTS IN CATEGORY 7 (MEAT PROCESSORS) ===")
while True:
    url = f"{API_BASE}/service-dwh/products?category=7&productionFilter=all&page={page}&pageSize=100"
    r = session.get(url, timeout=10)
    if r.status_code == 200:
        data = r.json()
        items = data.get("items", []) if isinstance(data, dict) else []
        if not items:
            print(f"Page {page} returned 0 items. Reached end of catalog.")
            break
        total_items += len(items)
        print(f"Page {page:2d}: +{len(items)} items | Total so far: {total_items}")
        page += 1
    else:
        print(f"Page {page}: HTTP {r.status_code}")
        break

print(f"\n==========================================")
print(f"TOTAL MEAT PROCESSORS PRODUCTS RETURNED BY API: {total_items}")
print(f"==========================================")
