"""
Test English Diagram Blueprint Downloader for NE1846 / NE1856-1846_1.pdf
========================================================================
1. Ensures x-language: en is passed in API headers
2. Tests exact filename case variations for NE1856-1846_1.pdf
3. Downloads the authentic English blueprint diagram image
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

BASE_DIR = Path(__file__).parent
SESSION_FILE = BASE_DIR / "session_state_eu.json"
IMG_DIR = BASE_DIR / "diagram_images"
IMG_DIR.mkdir(exist_ok=True)

captured_headers = {}

async def main():
    print("=" * 65)
    print("  SIRMAN ENGLISH DIAGRAM BLUEPRINT TEST")
    print("=" * 65)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        ctx = await browser.new_context(
            storage_state=str(SESSION_FILE),
            viewport={"width": 1440, "height": 900},
            locale="en-GB",
            timezone_id="Europe/Rome",
            geolocation={"latitude": 45.4642, "longitude": 9.1900},
            permissions=["geolocation"]
        )
        page = await ctx.new_page()

        async def on_req(req):
            if "service-dwh" in req.url:
                hdrs = dict(req.headers)
                if "authorization" in hdrs:
                    captured_headers.update(hdrs)

        page.on("request", on_req)

        await page.goto("https://www.service.sirman.com/home", wait_until="networkidle")
        await asyncio.sleep(2)

        cat_btn = await page.wait_for_selector("text=Catalog")
        if cat_btn:
            await cat_btn.click()
            await asyncio.sleep(3)

        headers = dict(captured_headers)
        headers["x-language"] = "en"
        headers["Accept-Language"] = "en-US,en;q=0.9"

        print(f"Captured headers x-language: {headers.get('x-language')}")

        target_pdf = "NE1856-1846_1.pdf"
        
        # Test filename case variations
        variations = [
            target_pdf.replace(".pdf", ".png"),
            target_pdf.replace(".pdf", ".png").lower(),
            target_pdf.replace(".pdf", ".jpg"),
            target_pdf.replace(".pdf", ".jpg").lower(),
            target_pdf,
            target_pdf.lower()
        ]

        success = False
        for var in variations:
            api_url = f"https://api-service.sirman.com/service-dwh/resources/exploded-view/jpeg/{var}?quality=full"
            resp = await ctx.request.get(api_url, headers=headers)
            print(f"[TEST] {var} -> Status: {resp.status}")
            if resp.status == 200:
                data = await resp.json()
                signed_url = data.get("url")
                if signed_url:
                    img_resp = await ctx.request.get(signed_url)
                    if img_resp.status == 200:
                        img_bytes = await img_resp.body()
                        if len(img_bytes) > 20000:
                            out_file = IMG_DIR / f"{target_pdf}.png"
                            with open(out_file, "wb") as f:
                                f.write(img_bytes)
                            print(f"  [SUCCESS] DOWNLOADED REAL ENGLISH BLUEPRINT: {out_file} ({len(img_bytes)/1024:.1f} KB)")
                            success = True
                            break

        if not success:
            print("[WARN] Testing product tavola endpoint for NE1846...")
            # Product 3210 is NE1846
            tv_resp = await ctx.request.get("https://api-service.sirman.com/service-dwh/products/3210/exploded-views", headers=headers)
            if tv_resp.status == 200:
                tv_data = await tv_resp.json()
                print(f"Tavola Data: {json.dumps(tv_data, indent=2)}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
