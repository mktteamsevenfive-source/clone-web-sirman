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

# Get full categories tree
r = session.get(f"{API_BASE}/service-dwh/categories", timeout=10)
if r.status_code == 200:
    cats = r.json()
    print(f"Total Category Nodes in Tree: {len(cats)}")

    # Filter Meat Processors subcategories (id=7 or parentId=7 or category path)
    meat_cats = []
    for c in cats:
        cid = c.get("id")
        cname = c.get("name") or c.get("i18n", {}).get("en")
        pid = c.get("parentId") or c.get("parent_id")
        # Check if contains meat or related
        meat_cats.append((cid, cname, pid))

    print("Sample subcategory nodes:")
    for c in cats[:20]:
        print(" ", c)
