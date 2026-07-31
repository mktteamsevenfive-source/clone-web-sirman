"""
Download Real High-Resolution Sirman Diagram Image
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

BASE_DIR = Path(__file__).parent
SESSION_FILE = BASE_DIR / "session_state_eu.json"
IMG_DIR = BASE_DIR / "diagram_images"
IMG_DIR.mkdir(exist_ok=True)

captured_headers = {}

async def main():
    print("=" * 65)
    print("  TEST DOWNLOADING REAL NE1840 DIAGRAM IMAGE")
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

        # Query API for image CloudFront URL
        api_url = "https://api-service.sirman.com/service-dwh/resources/exploded-view/jpeg/ne1880-1840-1540-2740_1.png?quality=full"
        resp = await ctx.request.get(api_url, headers=captured_headers)
        data = await resp.json()

        signed_url = data.get("url")
        print(f"CloudFront Signed URL: {signed_url[:80]}...")

        if signed_url:
            # Download the signed image
            img_resp = await ctx.request.get(signed_url)
            img_bytes = await img_resp.body()
            
            out_file = IMG_DIR / "NE1880-1840-1540-2740_1.pdf.png"
            with open(out_file, "wb") as f:
                f.write(img_bytes)

            print(f"[SUCCESS] DOWNLOADED REAL DIAGRAM IMAGE! ({len(img_bytes)/1024:.1f} KB)")
            print(f"Saved file to: {out_file}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
