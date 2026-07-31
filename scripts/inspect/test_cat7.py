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

r = session.get(f"{API_BASE}/service-dwh/products?category=7&productionFilter=all&page=1&pageSize=10", timeout=8)
print("HTTP Status:", r.status_code)
if r.status_code == 200:
    d = r.json()
    print("totalItems for Category 7 (Meat Processors):", d.get("totalItems"))
    print("totalPages:", d.get("totalPages"))
    print("Items returned on page 1:", len(d.get("items", [])))
    if d.get("items"):
        print("Sample item:", d["items"][0].get("name") or d["items"][0].get("code"))
