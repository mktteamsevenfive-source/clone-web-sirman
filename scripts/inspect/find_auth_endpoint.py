import sys, requests, re, json
sys.stdout.reconfigure(encoding="utf-8")

s = requests.Session()
s.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"

# Get the main JS bundle
print("Fetching JS bundle...")
r = s.get("https://service.sirman.com/static/js/main.07646396.js", timeout=15)
jtext = r.text
print(f"JS bundle size: {len(jtext):,} chars")

# Find Cognito User Pool and Client ID
cognito_pools = re.findall(r"['\"`](eu-[a-z0-9\-]+)['\"`]", jtext)
cognito_clients = re.findall(r"['\"`]([a-z0-9]{25,32})['\"`]", jtext)
cognito_domains = re.findall(r"['\"`](https?://[a-z0-9\-]+\.auth\.[a-z0-9\-]+\.amazoncognito\.com[^'\"`]*)['\"`]", jtext)
cognito_domains2 = re.findall(r"['\"`](https://[a-z0-9\-]+\.sirman\.com/oauth2[^'\"`]*)['\"`]", jtext)

print(f"\nCognito regions: {list(set(cognito_pools))[:5]}")
print(f"Possible client IDs: {list(set(cognito_clients))[:5]}")
print(f"Cognito domains: {list(set(cognito_domains))[:5]}")
print(f"Sirman OAuth2 URLs: {list(set(cognito_domains2))[:5]}")

# Find userPoolId pattern
pool_ids = re.findall(r"(?:userPoolId|UserPoolId|user_pool_id)['\"\s:]+([a-z0-9_\-]+)", jtext)
client_ids = re.findall(r"(?:clientId|client_id|userPoolWebClientId)['\"\s:]+([a-zA-Z0-9]+)", jtext)
auth_flows = re.findall(r"(?:authenticationFlowType|authFlow)['\"\s:]+([A-Z_]+)", jtext)
auth_domain = re.findall(r"(?:oauth|domain)['\"\s:]+['\"`](https?://[a-z0-9\-\.]+\.sirman\.com[^'\"`]*)['\"`]", jtext)

print(f"\nPool IDs: {list(set(pool_ids))[:5]}")
print(f"Client IDs: {list(set(client_ids))[:5]}")
print(f"Auth flows: {list(set(auth_flows))[:5]}")
print(f"Auth domains: {list(set(auth_domain))[:5]}")
