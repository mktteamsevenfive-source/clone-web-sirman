import json
import requests

try:
    with open('sirman_headers.json', encoding='utf-8') as f:
        data = json.load(f)

    hdrs = data.get('headers', {})
    cookies = data.get('cookies', [])

    session = requests.Session()
    clean = {k: v for k, v in hdrs.items() if not k.startswith(':')}
    session.headers.update(clean)
    cookie_str = '; '.join(f"{c['name']}={c['value']}" for c in cookies)
    if cookie_str:
        session.headers['cookie'] = cookie_str

    r = session.get('https://api-service.sirman.com/service-dwh/categories', timeout=8)
    print('HTTP Status:', r.status_code)
    if r.status_code == 200:
        cats = r.json()
        print('Categories returned:', len(cats))
        print('Sample categories:', [c.get('name') or c.get('i18n', {}).get('en') for c in cats[:5]])
    else:
        print('Response:', r.text[:200])
except Exception as e:
    print('Error:', e)
