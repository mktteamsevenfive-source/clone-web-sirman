import json
import requests

hdrs = json.load(open('sirman_headers.json'))['headers']
cookies = json.load(open('sirman_headers.json'))['cookies']
s = requests.Session()
s.headers.update({k: v for k, v in hdrs.items() if not k.startswith(':')})
s.headers['cookie'] = '; '.join(f"{c['name']}={c['value']}" for c in cookies)

url = 'https://api-service.sirman.com/service-dwh/resources/exploded-view/json/drk_f201810.json/content'
r = s.get(url)

raw_val = r.json()
if isinstance(raw_val, str):
    parsed = json.loads(raw_val)
else:
    parsed = raw_val

print("Width:", parsed.get("width"))
print("Height:", parsed.get("height"))
print("Transform:", parsed.get("transform"))

clickable = parsed.get("clickableElements", [])
print(f"Total Clickable Hotspots: {len(clickable)}")
if clickable:
    print("\nSample Hotspot 0:")
    print(json.dumps(clickable[0], indent=2))
    print("\nSample Hotspot 1:")
    print(json.dumps(clickable[1] if len(clickable) > 1 else clickable[0], indent=2))
