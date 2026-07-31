"""
Inspect Real Diagram Canvas & Image Data
=========================================
Navigates directly to /products/3208/tavola/13751?serial=NE1840 using authenticated session,
waits for canvas rendering, and exports canvas dataURL to PNG image!
"""

import asyncio
import base64
from pathlib import Path
from playwright.async_api import async_playwright

BASE_DIR = Path(__file__).parent
SESSION_FILE = BASE_DIR / "session_state_eu.json"
IMG_DIR = BASE_DIR / "diagram_images"
IMG_DIR.mkdir(exist_ok=True)

async def main():
    print("=" * 65)
    print("  SIRMAN CANVAS & DIAGRAM EXPORTER")
    print("=" * 65)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=100)
        ctx = await browser.new_context(
            storage_state=str(SESSION_FILE),
            viewport={"width": 1440, "height": 900},
            locale="en-GB",
            timezone_id="Europe/Rome",
            geolocation={"latitude": 45.4642, "longitude": 9.1900},
            permissions=["geolocation"]
        )
        page = await ctx.new_page()

        # Intercept ALL responses
        async def on_resp(resp):
            u = resp.url
            ct = resp.headers.get("content-type", "")
            st = resp.status
            if any(x in u.lower() for x in ["pdf", "image", "file", "tavola", "draw", "exploded", "svg", "dwh"]):
                if not any(ign in u for ign in ["google", "hubspot", "lucide", "font"]):
                    try:
                        b = await resp.body()
                        print(f"  [NET] {st} | {ct[:20]} | {len(b)/1024:.1f} KB | {u}")
                        if "image" in ct or "pdf" in ct or b.startswith(b"%PDF") or b.startswith(b"\x89PNG"):
                            out = IMG_DIR / "NE1880-1840-1540-2740_1.pdf.png"
                            with open(out, "wb") as f:
                                f.write(b)
                            print(f"  --> Saved network image to {out} ({len(b)/1024:.1f} KB)")
                    except:
                        pass

        page.on("response", on_resp)

        print("[1] Opening /home ...")
        await page.goto("https://www.service.sirman.com/home", wait_until="networkidle")
        await asyncio.sleep(2)

        print("[2] Navigating to NE1840 Tavola page...")
        await page.goto("https://www.service.sirman.com/products/3208/tavola/13751?serial=NE1840", wait_until="networkidle")
        
        print("[3] Waiting 6 seconds for canvas diagram to render...")
        await asyncio.sleep(6)

        # Method A: Extract Canvas toDataURL
        print("[4] Attempting canvas.toDataURL() extraction...")
        canvas_data = await page.evaluate("""() => {
            const canvases = document.querySelectorAll('canvas');
            for (const c of canvases) {
                if (c.width > 200 && c.height > 200) {
                    return c.toDataURL('image/png');
                }
            }
            return '';
        }""")

        if canvas_data and canvas_data.startswith("data:image"):
            b64_str = canvas_data.split(",")[1]
            img_bytes = base64.b64decode(b64_str)
            out_file = IMG_DIR / "NE1880-1840-1540-2740_1.pdf.png"
            with open(out_file, "wb") as f:
                f.write(img_bytes)
            print(f"  [SUCCESS] Extracted Canvas Diagram to {out_file} ({len(img_bytes)/1024:.1f} KB)")
        else:
            print("  [WARN] Canvas element dataURL empty")

        # Method B: Screenshot canvas viewport element
        print("[5] Attempting element screenshot of diagram container...")
        container = await page.query_selector("canvas, [class*='canvas'], [class*='diagram'], [class*='viewport']")
        if container:
            box = await container.bounding_box()
            if box and box["width"] > 200:
                ss_file = IMG_DIR / "NE1880-1840-1540-2740_1.pdf.png"
                await container.screenshot(path=str(ss_file))
                print(f"  [SUCCESS] Screenshot of container saved to {ss_file} ({ss_file.stat().st_size/1024:.1f} KB)")

        await page.screenshot(path="ne1840_final_canvas_screen.png")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
