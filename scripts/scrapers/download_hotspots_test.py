import json
import requests
from pathlib import Path

BASE_DIR = Path(__file__).parent
CATALOG_FILE = BASE_DIR / "sirman_catalog_data.json"
HOTSPOTS_DIR = BASE_DIR / "public" / "hotspots"
HOTSPOTS_DIR.mkdir(parents=True, exist_ok=True)

hdrs = json.load(open('sirman_headers.json'))['headers']
cookies = json.load(open('sirman_headers.json'))['cookies']
s = requests.Session()
s.headers.update({k: v for k, v in hdrs.items() if not k.startswith(':')})
s.headers['cookie'] = '; '.join(f"{c['name']}={c['value']}" for c in cookies)

data = json.load(open(CATALOG_FILE, encoding="utf-8"))
prods = data.get("products", [])

print(f"Testing hotspot download for {len(prods)} products...")
found = 0

for p in prods[:10]:
    pdf_name = p.get("pdf_name")
    if not pdf_name:
        continue
    clean_name = pdf_name.replace(".pdf", "").replace(".png", "")
    url = f"https://api-service.sirman.com/service-dwh/resources/exploded-view/json/{clean_name}.json/content"
    
    try:
        r = s.get(url, timeout=8)
        if r.status_code == 200:
            raw = r.json()
            parsed = json.loads(raw) if isinstance(raw, str) else raw
            clickables = parsed.get("clickableElements", [])
            print(f"  OK {clean_name}: {len(clickables)} hotspots found (width={parsed.get('width')}, height={parsed.get('height')})")
            
            # Save local hotspot JSON
            out_file = HOTSPOTS_DIR / f"{clean_name}.json"
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(parsed, f, ensure_ascii=False)
            found += 1
        else:
            print(f"  ERR {clean_name}: HTTP {r.status_code}")
    except Exception as e:
        print(f"  ERR {clean_name}: Error {e}")


print(f"\nDownloaded {found} hotspot JSON files to public/hotspots/")
