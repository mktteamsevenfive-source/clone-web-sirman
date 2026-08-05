import json
import subprocess
import requests
import sys
import time
from pathlib import Path

SUPABASE_URL = "https://ofrerwyoasklgsejlbzr.supabase.co"
SUPABASE_SERVICE = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9mcmVyd3lvYXNrbGdzZWpsYnpyIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NTM2NjY1NSwiZXhwIjoyMTAwOTQyNjU1fQ.shN-wvqCOZi1GtPO3rwCHF51OQ0hf23E_GVn9bt3bHQ"

HEADERS = {
    "apikey": SUPABASE_SERVICE,
    "Authorization": f"Bearer {SUPABASE_SERVICE}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates"
}

def upload_parts_batch(parts_list):
    total = len(parts_list)
    if total == 0:
        return 0
    
    batch_size = 1000
    uploaded = 0
    for i in range(0, total, batch_size):
        batch = parts_list[i:i+batch_size]
        url = f"{SUPABASE_URL}/rest/v1/parts"
        r = requests.post(url, headers=HEADERS, json=batch, timeout=60)
        if r.status_code in (200, 201):
            uploaded += len(batch)
            print(f"  Uploaded batch [{i+len(batch)}/{total}] OK")
        else:
            print(f"  [WARN] Batch HTTP {r.status_code}: {r.text[:120]}")
    return uploaded

def phase1_sync_git_parts():
    print("=" * 65)
    print("  PHASE 1: Sync 69,000+ Parts from Git Backup to Supabase")
    print("=" * 65)
    
    cmd = ["git", "show", "9b70030:sirman_parts.json"]
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=".", encoding="utf-8", errors="ignore")
    if res.returncode != 0 or not res.stdout:
        print(f"[ERROR] Failed to read git commit 9b70030: {res.stderr}")
        return 0

    data = json.loads(res.stdout)
    raw_parts = data.get("all_parts", [])
    print(f"[INFO] Loaded {len(raw_parts)} raw parts from Git commit 9b70030")

    parts_rows = []
    seen_keys = set()

    for pt in raw_parts:
        if not isinstance(pt, dict):
            continue
        prod_id = pt.get("_product_id") or pt.get("product_id")
        code = str(pt.get("id") or pt.get("code") or pt.get("partCode") or "").strip()
        if not prod_id or not code:
            continue
        
        prod_id = int(prod_id)
        key = f"{prod_id}:{code}"
        if key in seen_keys:
            continue
        seen_keys.add(key)

        pt_name = ""
        i18n = pt.get("i18n")
        if isinstance(i18n, dict):
            pt_name = i18n.get("en") or i18n.get("it") or ""
        if not pt_name:
            pt_name = pt.get("name") or pt.get("description") or "Part"

        parts_rows.append({
            "product_id": prod_id,
            "code": code,
            "name": str(pt_name).strip(),
            "price": float(pt.get("price") or 0.0),
            "stock": int(pt.get("dispTot") or pt.get("stock") or 0),
            "ref": str(pt.get("explodedViewRef") or pt.get("ref") or pt.get("position") or "").strip(),
            "view_name": str(pt.get("_view_name") or pt.get("view_name") or "").strip()
        })

    print(f"[INFO] Prepared {len(parts_rows)} unique part rows for upload.")
    uploaded = upload_parts_batch(parts_rows)
    print(f"[SUCCESS] Phase 1 complete: {uploaded} parts uploaded to Supabase!\n")
    return uploaded

if __name__ == "__main__":
    phase1_sync_git_parts()
