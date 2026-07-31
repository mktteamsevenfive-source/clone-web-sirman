"""
Test Real Diagram Capture for NE1840
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

BASE_DIR = Path(__file__).parent
SESSION_FILE = BASE_DIR / "session_state.json"
IMG_DIR = BASE_DIR / "diagram_images"

async def main():
    print("=" * 65)
    print("  TEST REAL DIAGRAM CAPTURE FOR NE1840")
    print("=" * 65)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=150)
        ctx = await browser.new_context(
            storage_state=str(SESSION_FILE),
            viewport={"width": 1440, "height": 900}
        )
        page = await ctx.new_page()

        print("[1] Opening Sirman catalog page...")
        await page.goto("https://www.service.sirman.com/catalog", wait_until="networkidle")
        await asyncio.sleep(2)

        # Search NE1840 in top search bar if present
        print("[2] Searching for NE1840...")
        search_input = await page.query_selector("input[placeholder*='search'], input[placeholder*='Search'], input[type='search']")
        if search_input:
            await search_input.fill("NE1840")
            await search_input.press("Enter")
            await asyncio.sleep(3)
        else:
            # Click Microwave ovens category
            micro = await page.query_selector("text='Microwave ovens', text='Microwave'")
            if micro:
                await micro.click()
                await asyncio.sleep(3)

        # Click NE1840 product row
        ne_el = await page.query_selector("text='NE1840', text='NE 1840'")
        if ne_el:
            print("[3] Clicking NE1840 product...")
            await ne_el.click()
            await asyncio.sleep(4)

        await page.screenshot(path="ne1840_captured_page.png")
        print(f"[4] Current page URL: {page.url}")

        # Check for image/canvas elements
        imgs = await page.query_selector_all("img, canvas, svg")
        print(f"Found {len(imgs)} visual elements on NE1840 page:")
        for idx, img in enumerate(imgs):
            try:
                src = await img.evaluate("el => el.src || el.href || ''")
                box = await img.bounding_box()
                w = box["width"] if box else 0
                h = box["height"] if box else 0
                if w > 200 and h > 200:
                    out_path = IMG_DIR / "NE1880-1840-1540-2740_1.pdf.png"
                    await img.screenshot(path=str(out_path))
                    print(f"  --> CAPTURED REAL DIAGRAM! Saved to {out_path} ({out_path.stat().st_size/1024:.1f} KB)")
                    break
            except Exception as e:
                pass

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
