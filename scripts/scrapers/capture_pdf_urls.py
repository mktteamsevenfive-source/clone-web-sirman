"""
Sirman Network Inspector - Capture Exact PDF/Image URLs
=========================================================
Opens Playwright, waits for login, navigates to an exploded view,
and prints all network URLs related to PDFs, images, or media files.
"""

import asyncio
from playwright.async_api import async_playwright

async def main():
    print("=" * 65)
    print("  SIRMAN NETWORK INSPECTOR - Find PDF / Image URLs")
    print("=" * 65)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=["--start-maximized"])
        ctx = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await ctx.new_page()

        # Listen to ALL requests & responses
        async def handle_route(response):
            url = response.url
            ct = response.headers.get("content-type", "")
            if any(ext in url.lower() for ext in [".pdf", ".png", ".jpg", "exploded", "files", "view", "dwh"]) or "pdf" in ct or "image" in ct:
                if not any(ign in url for ign in ["google", "hubspot", "analytics", "lucide", "fonts"]):
                    print(f"  [NET] {response.status} | {ct[:30]} | {url[:100]}")

        page.on("response", handle_route)

        print("\n[1] Opening service.sirman.com...")
        await page.goto("https://service.sirman.com/catalog", wait_until="domcontentloaded")

        print("\n[2] Please LOG IN to Sirman in the browser, then CLICK ON ANY PRODUCT -> EXPLODED VIEW.")
        print("    Press ENTER in terminal after you see the diagram on screen.")

        input("\n  >> Press ENTER after viewing an exploded view diagram... ")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
