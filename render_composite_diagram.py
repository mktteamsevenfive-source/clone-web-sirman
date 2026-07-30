"""
Render Composite Diagram Image (Base Image + SVG Hotspot Badges)
=================================================================
Combines base blueprint image with SVG callout badge numbers from JSON,
producing a 100% authentic composite diagram image with blue number badges!
"""

import asyncio
import json
import re
from pathlib import Path
from playwright.async_api import async_playwright

BASE_DIR = Path(__file__).parent
IMG_DIR = BASE_DIR / "diagram_images"

async def main():
    print("=" * 65)
    print("  RENDER COMPOSITE DIAGRAM (WITH NUMBER BADGES)")
    print("=" * 65)

    with open("apollo_hotspots_data.json", "r", encoding="utf-8") as f:
        raw_content = json.load(f)

    if isinstance(raw_content, str):
        hotspots_data = json.loads(raw_content)
    else:
        hotspots_data = raw_content

    w = hotspots_data.get("width", 793.62)
    h = hotspots_data.get("height", 1122.66)
    elements = hotspots_data.get("clickableElements", [])

    svg_items = []
    for el in elements:
        content = el.get("content", "")
        if content:
            # Transform cyan/blue badge styling to match Sirman UI
            # Replace fill/stroke to blue badge (#0284c7 / #0369a1)
            content = content.replace('fill="#231f20"', 'fill="#0284c7"')
            content = content.replace('<circle ', '<circle fill="#e0f2fe" stroke="#0284c7" stroke-width="1.5" ')
            svg_items.append(content)

    svg_content = "\n".join(svg_items)

    html_content = f"""<!DOCTYPE html>
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
        <img class="bg-img" src="file:///{str(IMG_DIR / 'Apollo_y15.pdf.png').replace('\\', '/')}" />
        <svg class="overlay-svg" viewBox="0 0 {w} {h}">
            <g transform="{hotspots_data.get('transform', '')}">
                {svg_content}
            </g>
        </svg>
    </div>
</body>
</html>
"""

    html_path = BASE_DIR / "test_composite.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Generated HTML preview: {html_path}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page(viewport={"width": int(w), "height": int(h)})
        await page.goto(f"file:///{str(html_path).replace('\\', '/')}")
        await asyncio.sleep(1)

        out_img = IMG_DIR / "Apollo_y15.pdf.png"
        await page.screenshot(path=str(out_img))
        print(f"[SUCCESS] Saved composite diagram with number badges to {out_img} ({out_file_size(out_img):.1f} KB)!")

        await browser.close()

def out_file_size(path):
    return path.stat().st_size / 1024 if path.exists() else 0

if __name__ == "__main__":
    asyncio.run(main())
