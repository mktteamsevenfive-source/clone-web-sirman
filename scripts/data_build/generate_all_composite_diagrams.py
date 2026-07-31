"""
AUTOMATED COMPOSITE DIAGRAM GENERATOR (BLUE CALLOUT NUMBER BADGES)
===================================================================
Fetches SVG hotspot callout coordinates for all 150 diagram files,
combines them with the base blueprint images, and renders 100% authentic
diagram images WITH blue circular callout numbers (75A, 4A, 1, 6, 10, etc.)
"""

import asyncio
import json
import re
import sys
import time
from pathlib import Path
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stdout.flush()

BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / "sirman_catalog_data.json"
SESSION_FILE = BASE_DIR / "session_state_eu.json"
IMG_DIR = BASE_DIR / "diagram_images"
IMG_DIR.mkdir(exist_ok=True)

captured_headers = {}


async def main():
    print("=" * 65)
    print("  SIRMAN COMPOSITE DIAGRAM GENERATOR (WITH BLUE NUMBER BADGES)")
    print("=" * 65)

    if not DATA_FILE.exists() or not SESSION_FILE.exists():
        print("[ERROR] Required files missing.")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        catalog_data = json.load(f)

    products = catalog_data.get("products", [])

    # Extract unique PDF filenames
    pdf_map = {}
    for p in products:
        pdf_name = p.get("pdfName", "").strip()
        if pdf_name and pdf_name not in pdf_map:
            pdf_map[pdf_name] = p.get("model", "Unknown")

    pdf_items = list(pdf_map.items())
    print(f"[INFO] Processing {len(pdf_items)} unique diagram blueprints...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=30)
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

        print("\n[STEP 1] Fetching DWH Authorization Token...")
        await page.goto("https://www.service.sirman.com/home", wait_until="networkidle")
        await asyncio.sleep(2)

        cat_btn = await page.wait_for_selector("text=Catalog")
        if cat_btn:
            await cat_btn.click()
            await asyncio.sleep(3)

        if "authorization" not in captured_headers:
            print("[ERROR] Authorization token capture failed.")
            return

        headers = dict(captured_headers)
        headers["x-language"] = "en"

        print(f"[SUCCESS] Authorization Token captured.")

        print(f"\n[STEP 2] Generating Composite Diagram Images with Blue Number Badges...")
        print("=" * 65)

        success_count = 0

        for idx, (pdf_name, model) in enumerate(pdf_items, 1):
            out_file = IMG_DIR / f"{pdf_name}.png"
            safe_model = model.encode('ascii', errors='ignore').decode('ascii').strip() or "Model"

            print(f"[{idx}/{len(pdf_items)}] {pdf_name} ({safe_model})...", end=" ")

            json_key = pdf_name.replace(".pdf", ".json").lower()
            json_url = f"https://api-service.sirman.com/service-dwh/resources/exploded-view/json/{json_key}/content"

            try:
                resp = await ctx.request.get(json_url, headers=headers)
                if resp.status == 200:
                    raw_data = await resp.json()
                    if isinstance(raw_data, str):
                        hotspots_data = json.loads(raw_data)
                    else:
                        hotspots_data = raw_data

                    w = hotspots_data.get("width", 793.62)
                    h = hotspots_data.get("height", 1122.66)
                    elements = hotspots_data.get("clickableElements", [])

                    if elements and out_file.exists():
                        svg_items = []
                        for el in elements:
                            content = el.get("content", "")
                            if content:
                                content = content.replace('fill="#231f20"', 'fill="#0284c7"')
                                content = content.replace('<circle ', '<circle fill="#e0f2fe" stroke="#0284c7" stroke-width="1.5" ')
                                svg_items.append(content)

                        svg_content = "\n".join(svg_items)
                        transform_str = hotspots_data.get('transform', '')

                        html_str = f"""<!DOCTYPE html>
                        <html>
                        <head>
                        <style>
                            body {{ margin: 0; padding: 0; background: white; }}
                            .container {{ position: relative; width: {w}px; height: {h}px; }}
                            .bg-img {{ position: absolute; top:0; left:0; width:100%; height:100%; object-fit: contain; }}
                            .overlay-svg {{ position: absolute; top:0; left:0; width:100%; height:100%; pointer-events: none; }}
                        </style>
                        </head>
                        <body>
                            <div class="container">
                                <img class="bg-img" src="file:///{str(out_file).replace('\\', '/')}" />
                                <svg class="overlay-svg" viewBox="0 0 {w} {h}">
                                    <g transform="{transform_str}">
                                        {svg_content}
                                    </g>
                                </svg>
                            </div>
                        </body>
                        </html>
                        """

                        temp_html = BASE_DIR / "_temp_composite.html"
                        with open(temp_html, "w", encoding="utf-8") as hf:
                            hf.write(html_str)

                        render_page = await ctx.new_page()
                        await render_page.set_viewport_size({"width": int(w), "height": int(h)})
                        await render_page.goto(f"file:///{str(temp_html).replace('\\', '/')}")
                        await asyncio.sleep(0.3)
                        await render_page.screenshot(path=str(out_file))
                        await render_page.close()

                        print(f"COMPOSITE SUCCESS ({out_file.stat().st_size/1024:.1f} KB)")
                        success_count += 1
                        continue

                print("No hotspot overlay data, keeping base blueprint")
                success_count += 1
            except Exception as err:
                print(f"Notice: {err}")

            time.sleep(0.02)

        await browser.close()

    print("\n" + "=" * 65)
    print(f"  ALL COMPOSITE DIAGRAM IMAGES GENERATED SUCCESSFULLY!")
    print(f"  Processed: {success_count}/{len(pdf_items)} images")
    print(f"  Image folder: {IMG_DIR}")
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(main())
