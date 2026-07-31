import json
import requests
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
HEADERS_FILE = ROOT_DIR / "sirman_headers.json"
ACTIVE_NODES_FILE = ROOT_DIR / "active_category_nodes.json"
API_BASE = "https://api-service.sirman.com"

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

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

# Get all 1282 category nodes
print("[1] Fetching category tree from Sirman API...")
r = session.get(f"{API_BASE}/service-dwh/categories", timeout=10)
cats = r.json()
print(f"[INFO] Received {len(cats)} category nodes.")

active_nodes = []
lock = time.time()

def check_node(c):
    cid = c.get("id")
    cname = c.get("i18n", {}).get("en") or c.get("name")
    try:
        res = session.get(f"{API_BASE}/service-dwh/products?category={cid}&productionFilter=all&page=1&pageSize=1", timeout=8)
        if res.status_code == 200:
            d = res.json()
            if isinstance(d, dict):
                cnt = d.get("totalItems", 0)
                if cnt > 0:
                    return {
                        "id": cid,
                        "name": cname,
                        "father": c.get("father", 0),
                        "type": c.get("type", ""),
                        "totalItems": cnt,
                        "totalPages": d.get("totalPages", 1)
                    }
    except Exception:
        pass
    return None

print(f"[2] Parallel scanning {len(cats)} nodes with 25 workers...")
start = time.time()

with ThreadPoolExecutor(max_workers=25) as executor:
    futures = [executor.submit(check_node, c) for c in cats]
    for future in as_completed(futures):
        res = future.result()
        if res:
            active_nodes.append(res)
            print(f"  [FOUND] Node ID {res['id']:4d} | '{res['name']}': {res['totalItems']} products ({res['totalPages']} pages)")

elapsed = round(time.time() - start, 2)
total_prods = sum(n["totalItems"] for n in active_nodes)

print("\n==========================================")
print(f"  SCAN COMPLETED IN {elapsed}s")
print(f"  Active Category Nodes with Products: {len(active_nodes)}")
print(f"  Total Products Found across all Nodes: {total_prods:,}")
print("==========================================")

with open(ACTIVE_NODES_FILE, "w", encoding="utf-8") as f:
    json.dump(active_nodes, f, ensure_ascii=False, indent=2)

print(f"Saved active category nodes map to {ACTIVE_NODES_FILE.name}")
