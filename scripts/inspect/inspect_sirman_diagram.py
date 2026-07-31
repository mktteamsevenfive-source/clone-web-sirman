"""
Sirman Exploded View Diagram Network Inspector
===============================================
Intercepts real network requests when you click Exploded View in the browser.
Prints exact image/PDF URLs and headers used by Sirman's website.
"""

import asyncio
from playwright.async_api import async_playwright, Response

async def main():
    print("=" * 65)
    print("  SIRMAN EXPLODED VIEW NETWORK INSPECTOR")
    print("=" * 65)

    captured = []

    async def on_response(response: Response):
        url = response.url
        ct = response.headers.get("content-type", "")
        
        # Look for images, pdfs, diagrams, exploded views
        if any(keyword in url.lower() for keyword in [
            "pdf", "png", "jpg", "jpeg", "svg", "exploded", "files", "view", "dwh"
        ]) and "sirman.com" in url:
            if not any(ign in url for ign in ["hubspot", "google", "analytics", "lucide", "font"]):
                headers = dict(response.request.headers)
                status = response.status
                length = response.headers.get("content-length", "unknown")
                
                info = f"Status: {status} | Type: {ct[:25]} | Length: {length}\n  URL: {url}\n  Headers: Auth={'Authorization' in headers or 'authorization' in headers}"
                captured.append(info)
                print(f"\n[CAPTURED MEDIA REQUEST]\n{info}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=["--start-maximized"])
        ctx = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await ctx.new_page()

        page.on("response", on_response)

        print("\n[STEP 1] Opening service.sirman.com...")
        await page.goto("https://service.sirman.com/catalog", wait_until="domcontentloaded")

        print("\n" + "*" * 65)
        print("  INSTRUCTION:")
        print("  1. Log in to Sirman Service in the browser window.")
        print("  2. Click on ANY category (e.g. Bar machines, Slicers).")
        print("  3. Click on ANY product -> Click 'Exploded View' or view diagram.")
        print("  4. Press ENTER here in terminal after you see the diagram.")
        print("*" * 65 + "\n")

        input("  >> Press ENTER after clicking Exploded View... ")

        print(f"\n[SUMMARY] Captured {len(captured)} relevant network requests.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
