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

# Test top 13 main categories from Sirman UI
main_cats = [
    (7, "Meat processors"),
    (6, "Slicers"),
    (4, "Bar machines"),
    (31, "Cooking machines"),
    (5, "Packaging machines"),
    (51, "Scales"),
    (52, "Ozone generators"),
    (61, "Dishwashers"),
    (2, "Snack and pizza"),
    (3, "Food processors"),
    (27, "Consumables"),
    (28, "Laundry"),
    (18, "Microwaves ovens"),
]

print("=== REAL API PRODUCT COUNTS FROM SIRMAN ===")
total_all = 0
for cid, cname in main_cats:
    r = session.get(f"{API_BASE}/service-dwh/products?category={cid}&productionFilter=all&page=1&pageSize=1", timeout=8)
    if r.status_code == 200:
        d = r.json()
        cnt = d.get("totalItems", 0)
        pages = d.get("totalPages", 0)
        total_all += cnt
        print(f"  Category ID {cid:2d} | {cname:<25}: {cnt:,} products ({pages} pages)")
    else:
        print(f"  Category ID {cid:2d} | {cname:<25}: HTTP {r.status_code}")

print(f"\nTOTAL PRODUCTS ACROSS MAIN CATEGORIES: {total_all:,}")
