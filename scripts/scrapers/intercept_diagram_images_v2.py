"""
intercept_diagram_images_v2.py
================================
Optimized strategy:
1. Login to Sirman once
2. For each missing product, navigate to its tavola page
3. Intercept the Sirman API JSON response that contains the signed CloudFront URL
4. Use ctx.request.get() to download the image from CloudFront (browser context has cookies)
5. Upload bytes to Supabase Storage

Why this is faster: We don't wait for the browser to download the full image — we
get the signed URL from the API response JSON, then download directly.
"""
import asyncio
import json
import re
import sys
import time
import requests as req_lib
from playwright.async_api import async_playwright

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SUPABASE_URL     = 'https://ofrerwyoasklgsejlbzr.supabase.co'
SUPABASE_SERVICE = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9mcmVyd3lvYXNrbGdzZWpsYnpyIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NTM2NjY1NSwiZXhwIjoyMTAwOTQyNjU1fQ.shN-wvqCOZi1GtPO3rwCHF51OQ0hf23E_GVn9bt3bHQ'
SUP_HEADERS = {'apikey': SUPABASE_SERVICE, 'Authorization': 'Bearer ' + SUPABASE_SERVICE}
USERNAME = 'korralak.sa@sevenfive.co.th'
PASSWORD = 'Service@1234'


def list_supabase_images() -> set:
    existing = set()
    offset = 0
    while True:
        url = f'{SUPABASE_URL}/storage/v1/object/list/diagram_images'
        r = req_lib.post(url, headers=SUP_HEADERS,
                         json={'limit': 1000, 'offset': offset, 'prefix': '',
                               'sortBy': {'column': 'name', 'order': 'asc'}}, timeout=15)
        if r.status_code != 200:
            break
        items = r.json()
        if not items:
            break
        for item in items:
            existing.add(item.get('name', ''))
        if len(items) < 1000:
            break
        offset += 1000
    return existing


def get_missing_products(existing_images: set) -> list:
    products = []
    offset = 0
    while True:
        r = req_lib.get(
            f'{SUPABASE_URL}/rest/v1/products?select=id,code,model,pdf_name,exploded_view_id&limit=1000&offset={offset}',
            headers=SUP_HEADERS, timeout=15
        )
        batch = r.json()
        if not batch:
            break
        products.extend(batch)
        if len(batch) < 1000:
            break
        offset += 1000

    missing = []
    for p in products:
        pdf = p.get('pdf_name', '')
        view_id = p.get('exploded_view_id', '')
        if not pdf or not view_id:
            continue
        clean = re.sub(r'\.pdf$', '', pdf, flags=re.IGNORECASE).strip()
        clean_safe = clean.replace(' ', '_')
        variants = [f'{pdf}.png', f'{clean}.png', f'{clean_safe}.png']
        if not any(v in existing_images for v in variants):
            missing.append({**p, 'clean': clean, 'clean_safe': clean_safe})
    return missing


def upload_to_supabase(filename: str, data: bytes) -> bool:
    url = f'{SUPABASE_URL}/storage/v1/object/diagram_images/{filename}'
    r = req_lib.post(url,
                     headers={**SUP_HEADERS, 'Content-Type': 'image/png', 'x-upsert': 'true'},
                     data=data, timeout=30)
    return r.status_code in (200, 201)


async def main():
    print('Checking Supabase for missing diagram images...')
    existing = list_supabase_images()
    print(f'  Found {len(existing)} images already on Supabase')
    missing = get_missing_products(existing)
    print(f'  Products needing diagrams: {len(missing)}')

    if not missing:
        print('All done! No missing diagrams.')
        return

    ok = 0
    fail = 0
    total = len(missing)
    start = time.time()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={'width': 1440, 'height': 900})

        # ── Login ────────────────────────────────────────────────────────────
        print('\nLogging in to Sirman...')
        page = await ctx.new_page()
        await page.goto('https://service.sirman.com/catalog', wait_until='domcontentloaded', timeout=30000)
        await asyncio.sleep(2)
        try:
            login_btn = await page.query_selector("button:has-text('LOGIN'), a:has-text('LOGIN')")
            if login_btn and await login_btn.is_visible():
                await page.click("button:has-text('LOGIN'), a:has-text('LOGIN')")
                await asyncio.sleep(3)
        except Exception:
            pass
        email_in = await page.query_selector("#inputEmail, input[type='email']")
        pass_in  = await page.query_selector("#inputPassword, input[type='password']")
        if email_in and pass_in:
            await email_in.fill(USERNAME)
            await pass_in.fill(PASSWORD)
            try:
                await page.click("button[type='submit']")
                await asyncio.sleep(5)
            except Exception:
                pass
        try:
            consent = await page.query_selector("button:has-text('Authorize')")
            if consent and await consent.is_visible():
                await page.click("button:has-text('Authorize')")
                await asyncio.sleep(5)
        except Exception:
            pass
        print(f'  Login URL: {page.url}')
        await page.close()

        # ── Download loop ─────────────────────────────────────────────────────
        print(f'\nDownloading {total} missing diagram images...')
        print('=' * 70)

        for i, prod in enumerate(missing, 1):
            prod_id = prod['id']
            view_id = prod.get('exploded_view_id', '')
            pdf = prod.get('pdf_name', '')
            clean = prod.get('clean', '')
            clean_safe = prod.get('clean_safe', '')
            model = prod.get('model', '')[:45]

            if not view_id:
                fail += 1
                continue

            product_url = f'https://www.service.sirman.com/products/{prod_id}/tavola/{view_id}'

            # Intercept the Sirman API response that contains the signed URL
            signed_url_container = []

            page = await ctx.new_page()

            async def on_response(response, _container=signed_url_container):
                if _container:
                    return
                url = response.url
                # The Sirman API returns a JSON with the signed CloudFront URL
                if ('api-service.sirman.com/service-dwh/resources/exploded-view/jpeg/' in url
                        and response.status == 200):
                    try:
                        data = await response.json()
                        su = data.get('url', '')
                        if su and 'service247' in su:
                            _container.append(su)
                    except Exception:
                        pass

            page.on('response', on_response)

            try:
                await page.goto(product_url, wait_until='domcontentloaded', timeout=25000)
                # Wait up to 25 seconds for the Sirman API to return signed URL
                deadline = time.time() + 25
                while not signed_url_container and time.time() < deadline:
                    await asyncio.sleep(0.5)
            except Exception:
                pass

            await page.close()

            if not signed_url_container:
                fail += 1
                if i <= 20 or i % 50 == 0:
                    print(f'  [{i}/{total}] NO URL  {model}')
                continue

            signed_url = signed_url_container[0]

            # Download image via browser context (has Cognito session cookies)
            img_data = None
            try:
                img_resp = await ctx.request.get(signed_url, timeout=30000)
                if img_resp.status == 200:
                    body = await img_resp.body()
                    if len(body) > 20000:
                        img_data = body
            except Exception:
                pass

            # If browser context fails, try plain HTTP (signed URL may be public)
            if not img_data:
                try:
                    r = req_lib.get(signed_url, timeout=30)
                    if r.status_code == 200 and len(r.content) > 20000:
                        img_data = r.content
                except Exception:
                    pass

            if img_data:
                filenames = list({f'{pdf}.png', f'{clean}.png', f'{clean_safe}.png'})
                uploaded = False
                for fn in filenames:
                    if upload_to_supabase(fn, img_data):
                        uploaded = True
                if uploaded:
                    ok += 1
                    rate = ok / max(time.time() - start, 1)
                    print(f'  [{i}/{total}] OK   {model} ({rate:.2f}/s)')
                else:
                    fail += 1
                    print(f'  [{i}/{total}] UPLOAD FAIL  {model}')
            else:
                fail += 1
                if i <= 20 or i % 50 == 0:
                    print(f'  [{i}/{total}] IMG 403  {model}')

        await browser.close()

    elapsed = time.time() - start
    print('\n' + '=' * 70)
    print(f'  [DONE] Completed in {elapsed:.1f}s')
    print(f'  Successfully Uploaded: {ok}')
    print(f'  Failed / Not Found:    {fail}')
    print('=' * 70)


if __name__ == '__main__':
    asyncio.run(main())
