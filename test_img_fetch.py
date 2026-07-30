import json
import requests

hdrs = json.load(open('sirman_headers.json'))['headers']
cookies = json.load(open('sirman_headers.json'))['cookies']
s = requests.Session()
s.headers.update({k: v for k, v in hdrs.items() if not k.startswith(':')})
s.headers['cookie'] = '; '.join(f"{c['name']}={c['value']}" for c in cookies)

url = 'https://api-service.sirman.com/service-dwh/resources/exploded-view/jpeg/drk_f201810.png?quality=full'
r = s.get(url)
print('JSON response:', r.json())

# Signed URL is inside the response!
data = r.json()
if isinstance(data, dict) and "url" in data:
    signed_url = data["url"]
    print("\nDownloading signed image URL:", signed_url[:80])
    img_res = requests.get(signed_url)
    print("Image download status:", img_res.status_code)
    print("Downloaded image size:", len(img_res.content), "bytes ✅")

