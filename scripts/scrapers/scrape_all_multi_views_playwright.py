"""
scrape_all_multi_views_playwright.py
======================================
Scrapes all 4,052 products for multi-diagram exploded views (Table 1, Table 2...)
using Playwright session context and saves public/product_views.json.
"""
import asyncio
import json
import requests
from pathlib import Path
from playwright.async_api import async_playwright

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
OUTPUT_FILE = ROOT_DIR / "public" / "product_views.json"

USERNAME = "korralak.sa@sevenfive.co.th"
PASSWORD = "Service@1234"

SUPABASE_URL = "https://ofrerwyoasklgsejlbzr.supabase.co"
SUPABASE_SERVICE = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9mcmVyd3lvYXNrbGdzZWpsYnpyIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NTM2NjY1NSwiZXhwIjoyMTAwOTQyNjU1fQ.shN-wvqCOZi1GtPO3rwCHF51OQ0hf23E_GVn9bt3bHQ"
SUP_HEADERS = {"apikey": SUPABASE_SERVICE, "Authorization": f"Bearer {SUPABASE_SERVICE}"}

async def main():
    print("=" * 65)
    print("  SCRAPING MULTI-DIAGRAM EXPLODED VIEWS VIA PLAYWRIGHT SESSION")
    print("=" * 65)

    # 1. Fetch all products from Supabase DB with pagination
    print("[1] Fetching all products from Supabase DB...")
    products = []
    offset = 0
    while True:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/products?select=id,code,model,pdf_name,exploded_view_id&limit=1000&offset={offset}", headers=SUP_HEADERS)
        batch = r.json()
        if not batch:
            break
        products.extend(batch)
        if len(batch) < 1000:
            break
        offset += 1000

    print(f"  Fetched {len(products)} total products from Supabase DB")

    product_views_map = {}
    multi_count = 0

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await ctx.new_page()

        print("[2] Logging into Sirman portal...")
        await page.goto("https://www.service.sirman.com/login", wait_until="domcontentloaded")
        await asyncio.sleep(2)

        email_in = await page.query_selector("#inputEmail, input[type='email']")
        if not email_in:
            login_btn = await page.query_selector("button:has-text('LOGIN'), .login-btn, a:has-text('LOGIN')")
            if login_btn and await login_btn.is_visible():
                try:
                    await login_btn.click()
                    await asyncio.sleep(3)
                except Exception:
                    pass
            email_in = await page.query_selector("#inputEmail, input[type='email']")

        pass_in = await page.query_selector("#inputPassword, input[type='password']")
        if email_in and pass_in:
            await email_in.fill(USERNAME)
            await pass_in.fill(PASSWORD)
            submit_btn = await page.query_selector("button[type='submit']")
            if submit_btn:
                await submit_btn.click()
                await asyncio.sleep(4)

        try:
            auth_btn = await page.query_selector("button:has-text('Authorize')")
            if auth_btn and await auth_btn.is_visible():
                await auth_btn.click()
                await asyncio.sleep(4)
        except Exception:
            pass

        print(f"  Logged in! Current URL: {page.url}")

        print("[3] Batch querying exploded views for all products...")

        batch_size = 50
        for i in range(0, len(products), batch_size):
            batch = products[i:i+batch_size]
            pids = [p["id"] for p in batch]

            results = await page.evaluate("""
                async (pids) => {
                    const map = {};
                    await Promise.all(pids.map(async (pid) => {
                        try {
                            const res = await fetch(`https://api-service.sirman.com/service-dwh/products/${pid}/exploded-views`);
                            if (res.ok) {
                                const data = await res.json();
                                if (data && data.length > 0) {
                                    map[pid] = data.map(v => ({
                                        id: v.id,
                                        order: v.order,
                                        name: v.name,
                                        pdfName: v.pdfName,
                                        type: v.type
                                    }));
                                }
                            }
                        } catch (e) {}
                    }));
                    return map;
                }
            """, pids)

            for pid_str, views in results.items():
                if views:
                    product_views_map[str(pid_str)] = views
                    if len(views) > 1:
                        multi_count += 1

            if (i + batch_size) % 500 == 0 or (i + batch_size) >= len(products):
                print(f"  Processed {min(i+batch_size, len(products))} / {len(products)} products... (Found {len(product_views_map)} with views, {multi_count} with >1 table)")

        await browser.close()

    print(f"\n[4] Complete!")
    print(f"  Total Products Processed: {len(products)}")
    print(f"  Products with Diagram Views: {len(product_views_map)}")
    print(f"  Products with MULTIPLE Diagram Views (>1): {multi_count}")

    # Write local public/product_views.json
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(product_views_map, f, indent=2, ensure_ascii=False)
    print(f"  Saved local file {OUTPUT_FILE}")

    # Upload to Supabase Storage
    up_url = f"{SUPABASE_URL}/storage/v1/object/diagram_hotspots/product_views.json"
    headers = {**SUP_HEADERS, "Content-Type": "application/json", "x-upsert": "true"}
    r = requests.post(up_url, headers=headers, data=json.dumps(product_views_map).encode('utf-8'))
    print(f"  [SUPABASE UPLOAD] product_views.json status: {r.status_code}")

if __name__ == "__main__":
    asyncio.run(main())
