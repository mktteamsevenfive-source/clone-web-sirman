"""
AUTOMATED SIRMAN DIAGRAM SCRAPER & CAPTURER (DOM/Canvas Screenshot Method)
==========================================================================
1. Opens Chromium browser to service.sirman.com/catalog
2. User logs in manually
3. Playwright automatically navigates to each product's exploded view page
4. Captures/saves the high-res diagram image directly from the browser DOM!
"""

import asyncio
import json
import time
from pathlib import Path
from playwright.async_api import async_playwright

BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / "sirman_catalog_data.json"
IMG_DIR = BASE_DIR / "diagram_images"
IMG_DIR.mkdir(exist_ok=True)


async def main():
    print("=" * 65)
    print("  SIRMAN AUTOMATED DIAGRAM CAPTURER (BROWSER DOM METHOD)")
    print("=" * 65)

    if not DATA_FILE.exists():
        print(f"[ERROR] {DATA_FILE} not found.")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        catalog_data = json.load(f)

    products = catalog_data.get("products", [])
    print(f"[INFO] Loaded {len(products)} products.")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=["--start-maximized"])
        ctx = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await ctx.new_page()

        # Intercept image/pdf responses directly from network
        captured_images = {}

        async def on_response(resp):
            u = resp.url
            ct = resp.headers.get("content-type", "")
            if resp.status == 200 and ("image" in ct or "pdf" in ct or "files" in u):
                if not any(ign in u for ign in ["google", "hubspot", "lucide", "font", "logo"]):
                    try:
                        b = await resp.body()
                        if len(b) > 5000:
                            captured_images[u] = b
                    except:
                        pass

        page.on("response", on_response)

        print("\n[STEP 1] Opening catalog page...")
        await page.goto("https://service.sirman.com/catalog", wait_until="domcontentloaded")

        print("\n" + "*" * 65)
        print("  PLEASE LOG IN TO SIRMAN SERVICE IN THE BROWSER WINDOW.")
        print("  AFTER LOGIN IS COMPLETE AND YOU SEE THE CATALOG, PRESS ENTER.")
        print("*" * 65 + "\n")

        input("  >> Press ENTER after logging in... ")

        print("\n[STEP 2] Navigating products to capture real diagram images...")

        success_count = 0

        for idx, p in enumerate(products, 1):
            p_id = p.get("id")
            p_name = p.get("model")
            pdf_name = p.get("pdfName")
            v_id = p.get("explodedViewId")

            if not pdf_name:
                continue

            img_path = IMG_DIR / f"{pdf_name}.png"
            print(f"[{idx}/{len(products)}] {p_name} (ID: {p_id})...", end=" ")

            if img_path.exists() and img_path.stat().st_size > 15000:
                print("Already captured")
                success_count += 1
                continue

            # Clear captured dict
            captured_images.clear()

            # Target URL on Sirman website for exploded view
            target_url = f"https://service.sirman.com/catalog/products/{p_id}"
            if v_id:
                target_url += f"/exploded-views/{v_id}"

            try:
                await page.goto(target_url, wait_until="networkidle", timeout=12000)
                await asyncio.sleep(1.5)
            except Exception:
                pass

            # Try to screenshot the diagram element on page
            saved = False
            diagram_selectors = [
                "canvas",
                "svg[class*='diagram']",
                "[class*='diagram']",
                "[class*='exploded']",
                "img[src*='file']",
                "img[src*='pdf']",
                "iframe",
                ".pdf-viewer"
            ]

            for sel in diagram_selectors:
                try:
                    el = await page.query_selector(sel)
                    if el:
                        box = await el.bounding_box()
                        if box and box["width"] > 100 and box["height"] > 100:
                            await el.screenshot(path=str(img_path))
                            saved = True
                            print(f"Captured screenshot via '{sel}' ({img_path.stat().st_size/1024:.1f} KB)")
                            break
                except Exception:
                    pass

            if not saved and captured_images:
                # Pick largest captured image byte buffer
                largest_url = max(captured_images, key=lambda k: len(captured_images[k]))
                data = captured_images[largest_url]
                with open(img_path, "wb") as imf:
                    imf.write(data)
                saved = True
                print(f"Captured network image ({len(data)/1024:.1f} KB)")

            if not saved:
                # Full page pane screenshot fallback
                try:
                    await page.screenshot(path=str(img_path))
                    saved = True
                    print(f"Captured page screenshot")
                except Exception:
                    print("Failed to capture")

            if saved:
                success_count += 1

        await browser.close()

    print("\n" + "=" * 65)
    print(f"  DIAGRAM CAPTURE COMPLETE: {success_count}/{len(products)} images saved!")
    print(f"  Image folder: {IMG_DIR}")
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(main())
