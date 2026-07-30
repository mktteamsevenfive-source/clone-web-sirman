"""
Test Direct Sirman Diagram JPEG/PNG API Endpoint
=================================================
Fetches diagram images directly using Sirman's official endpoint:
https://api-service.sirman.com/service-dwh/resources/exploded-view/jpeg/{name}?quality=full
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

BASE_DIR = Path(__file__).parent
SESSION_FILE = BASE_DIR / "session_state_eu.json"
IMG_DIR = BASE_DIR / "diagram_images"
IMG_DIR.mkdir(exist_ok=True)

async def main():
    print("=" * 65)
    print("  SIRMAN DIRECT DIAGRAM IMAGE ENDPOINT TEST")
    print("=" * 65)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        ctx = await browser.new_context(
            storage_state=str(SESSION_FILE),
            viewport={"width": 1440, "height": 900}
        )
        page = await ctx.new_page()

        # Capture headers from initial request
        headers = {}
        async def on_req(req):
            if "service-dwh" in req.url:
                hdrs = dict(req.headers)
                if "authorization" in hdrs:
                    headers.update(hdrs)

        page.on("request", on_req)

        print("[1] Opening /home to obtain fresh DWH headers...")
        await page.goto("https://www.service.sirman.com/home", wait_until="networkidle")
        await asyncio.sleep(2)

        print(f"[2] Captured headers count: {len(headers)}")
        print(f"  Authorization: {headers.get('authorization', '')[:35]}...")
        print(f"  x-customer-code: {headers.get('x-customer-code')}")
        print(f"  x-company: {headers.get('x-company')}")

        test_names = [
            "ne1880-1840-1540-2740_1.png",
            "agat1.png",
            "agat1-ce.png",
            "apollo_y15.png",
            "drk_f201810.png"
        ]

        for tname in test_names:
            url = f"https://api-service.sirman.com/service-dwh/resources/exploded-view/jpeg/{tname}?quality=full"
            resp = await ctx.request.get(url, headers=headers)
            body = await resp.body()
            print(f"[TEST] {tname} -> Status: {resp.status}, Content-Type: {resp.headers.get('content-type')}, Size: {len(body)/1024:.1f} KB")

            if resp.status == 200 and len(body) > 3000:
                # Save to diagram_images
                # Map back to pdfName
                pdf_key = tname.replace(".png", ".pdf")
                out_file = IMG_DIR / f"{pdf_key}.png"
                with open(out_file, "wb") as f:
                    f.write(body)
                print(f"  --> SUCCESSFULLY DOWNLOADED & SAVED REAL DIAGRAM: {out_file} ({len(body)/1024:.1f} KB)")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
