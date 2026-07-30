import json
import requests

hdrs = json.load(open('sirman_headers.json'))['headers']
cookies = json.load(open('sirman_headers.json'))['cookies']
s = requests.Session()
s.headers.update({k: v for k, v in hdrs.items() if not k.startswith(':')})
s.headers['cookie'] = '; '.join(f"{c['name']}={c['value']}" for c in cookies)

urls = [
    'https://api-service.sirman.com/service-dwh/catalogs',
    'https://api-service.sirman.com/service-dwh/categories',
    'https://api-service.sirman.com/service-dwh/products?productionFilter=discontinued&page=1&pageSize=100',
    'https://api-service.sirman.com/service-dwh/products?productionFilter=current&page=1&pageSize=100',
    'https://api-service.sirman.com/service-dwh/products?productionFilter=all&page=1&pageSize=100',
    'https://api-service.sirman.com/service-dwh/parts?page=1&pageSize=100',
]

for url in urls:
    try:
        r = s.get(url, timeout=8)
        print(f"URL: {url}")
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            val = r.json()
            if isinstance(val, dict):
                print(f"  Keys: {list(val.keys())}")
                if "totalItems" in val:
                    print(f"  totalItems: {val['totalItems']}, totalPages: {val.get('totalPages')}")
            elif isinstance(val, list):
                print(f"  List length: {len(val)}")
        print("-" * 50)
    except Exception as e:
        print(f"Error: {e}")
