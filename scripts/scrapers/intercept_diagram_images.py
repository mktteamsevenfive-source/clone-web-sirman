"""
intercept_diagram_images.py
============================
Strategy: Login to Sirman, then navigate to each product exploded-view page
and intercept the actual JPEG image response from the network.
This bypasses CloudFront 403 because the browser is fully authenticated.
"""
import asyncio
import json
import requests
import re
import sys
import time
from pathlib import Path
from playwright.async_api import async_playwright

# Fix Unicode output on Windows CP874 terminal
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SUPABASE_URL     = 'https://ofrerwyoasklgsejlbzr.supabase.co'
SUPABASE_SERVICE = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9mcmVyd3lvYXNrbGdzZWpsYnpyIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NTM2NjY1NSwiZXhwIjoyMTAwOTQyNjU1fQ.shN-wvqCOZi1GtPO3rwCHF51OQ0hf23E_GVn9bt3bHQ'
SUP_HEADERS = {'apikey': SUPABASE_SERVICE, 'Authorization': 'Bearer ' + SUPABASE_SERVICE}

USERNAME = 'korralak.sa@sevenfive.co.th'
PASSWORD = 'Service@1234'


def list_supabase_images() -> set:
    """List all images already in Supabase Storage."""
    existing = set()
    offset = 0
    while True:
        url = f'{SUPABASE_URL}/storage/v1/object/list/diagram_images'
        r = requests.post(url, headers=SUP_HEADERS, json={'limit': 1000, 'offset': offset, 'prefix': '', 'sortBy': {'column': 'name', 'order': 'asc'}}, timeout=15)
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
    """Get products from Supabase that have exploded_view_id but no diagram image."""
    products = []
    offset = 0
    while True:
        r = requests.get(
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
    r = requests.post(url, headers={**SUP_HEADERS, 'Content-Type': 'image/png', 'x-upsert': 'true'}, data=data, timeout=30)
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

        # Login flow - using proven approach from debug script
        print('\nLogging in to Sirman...')
        page = await ctx.new_page()
        await page.goto('https://service.sirman.com/catalog', wait_until='domcontentloaded', timeout=30000)
        await asyncio.sleep(2)

        # Click LOGIN button if on landing page (use page.click with selector, not element handle)
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
            await asyncio.sleep(1)
            try:
                await page.click("button[type='submit']")
                await asyncio.sleep(5)
            except Exception:
                pass

        # Handle OAuth consent
        try:
            consent = await page.query_selector("button:has-text('Authorize'), button:has-text('Allow')")
            if consent and await consent.is_visible():
                await page.click("button:has-text('Authorize'), button:has-text('Allow')")
                await asyncio.sleep(5)
        except Exception:
            pass

        current_url = page.url
        print(f'  After login URL: {current_url}')
        await page.close()

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

            # Navigate to the exploded view page and intercept image response
            product_url = f'https://www.service.sirman.com/products/{prod_id}/tavola/{view_id}'

            # Use mutable list (not nonlocal) to avoid closure binding bug in async for-loop
            captured = []

            page = await ctx.new_page()

            async def handle_response(response, _cap=captured):
                if _cap:
                    return
                if 'service-media-prod.service247.net' in response.url and response.status == 200:
                    try:
                        body = await response.body()
                        if len(body) > 20000:
                            _cap.append(body)
                    except Exception:
                        pass

            page.on('response', handle_response)

            try:
                # Use domcontentloaded (not networkidle) - page JS will trigger image load
                await page.goto(product_url, wait_until='domcontentloaded', timeout=20000)
                # Wait for JS to trigger image loading (diagram renders after JS runs)
                await asyncio.sleep(7)
            except Exception:
                pass

            await page.close()
            captured_image = captured[0] if captured else None

            if captured_image:
                filenames = list({f'{pdf}.png', f'{clean}.png', f'{clean_safe}.png'})
                uploaded = False
                for fn in filenames:
                    if upload_to_supabase(fn, captured_image):
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
                    print(f'  [{i}/{total}] NO IMG  {model} | pdf={pdf}')


        await browser.close()

    elapsed = time.time() - start
    print('\n' + '=' * 70)
    print(f'  [DONE] Completed in {elapsed:.1f}s')
    print(f'  Successfully Uploaded: {ok}')
    print(f'  Failed / Not Found:    {fail}')
    print('=' * 70)


if __name__ == '__main__':
    asyncio.run(main())
