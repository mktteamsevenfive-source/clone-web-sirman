"""
refresh_auth_api.py
====================
Login to Sirman via direct API call (no browser needed)
Gets auth token and saves to sirman_headers.json
"""
import sys, json, requests
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
HEADERS_FILE = ROOT_DIR / "sirman_headers.json"

USERNAME = "korralak.sa@sevenfive.co.th"
PASSWORD = "Service@1234"
API_BASE = "https://api-service.sirman.com"
AUTH_BASE = "https://auth.sirman.com"
WEB_BASE  = "https://service.sirman.com"

print("=" * 50)
print("  SIRMAN API AUTH - DIRECT LOGIN")
print("=" * 50)

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": WEB_BASE,
    "Referer": f"{WEB_BASE}/login",
})

# Try multiple known login endpoint patterns for Sirman
login_payloads = [
    # Standard REST
    {
        "url": f"{API_BASE}/service-auth/login",
        "data": {"email": USERNAME, "password": PASSWORD},
    },
    {
        "url": f"{API_BASE}/auth/login",
        "data": {"email": USERNAME, "password": PASSWORD},
    },
    {
        "url": f"{API_BASE}/service-auth/authenticate",
        "data": {"username": USERNAME, "password": PASSWORD},
    },
    {
        "url": f"{AUTH_BASE}/login",
        "data": {"email": USERNAME, "password": PASSWORD},
    },
    {
        "url": f"{WEB_BASE}/api/auth/login",
        "data": {"email": USERNAME, "password": PASSWORD},
    },
]

token = None
for attempt in login_payloads:
    url = attempt["url"]
    print(f"\n[TRY] POST {url}")
    try:
        r = session.post(url, json=attempt["data"], timeout=10)
        print(f"      HTTP {r.status_code}")
        if r.status_code in (200, 201):
            data = r.json()
            print(f"      Response keys: {list(data.keys()) if isinstance(data, dict) else type(data)}")
            # Look for token in response
            token = (data.get("token") or data.get("accessToken") or
                     data.get("access_token") or data.get("Authorization") or
                     data.get("data", {}).get("token") if isinstance(data.get("data"), dict) else None)
            if token:
                print(f"      [SUCCESS] Got token: {token[:40]}...")
                break
        elif r.status_code == 404:
            print("      (endpoint not found)")
        else:
            print(f"      Response: {r.text[:100]}")
    except Exception as e:
        print(f"      Error: {e}")

if token:
    headers = {
        "authorization": f"Bearer {token}",
        "content-type": "application/json",
        "origin": WEB_BASE,
        "referer": f"{WEB_BASE}/",
    }
    with open(HEADERS_FILE, "w", encoding="utf-8") as f:
        json.dump({"headers": headers, "cookies": []}, f, indent=2)
    print(f"\n[SAVED] Token saved to {HEADERS_FILE.name}")

    # Test it
    test = requests.get(f"{API_BASE}/service-dwh/categories", headers=headers, timeout=10)
    print(f"[TEST] GET /categories -> HTTP {test.status_code}")
    if test.status_code == 200:
        print(f"[OK] Token works! Found {len(test.json())} categories")
    else:
        print(f"[FAIL] {test.text[:100]}")
else:
    print("\n[ERROR] Could not get token via API.")
    print("\nTrying to find auth endpoint by inspecting network...")
    
    # Try to get the web app and look for API calls
    r = session.get(f"{WEB_BASE}/login", timeout=10)
    print(f"Login page HTTP: {r.status_code}")
    
    # Look for API base URL in the page source
    import re
    matches = re.findall(r'https://[a-z\-]+\.sirman\.com[/a-z\-]*', r.text)
    unique = list(set(matches))
    if unique:
        print("Found API URLs in page source:")
        for m in unique[:10]:
            print(f"  {m}")
