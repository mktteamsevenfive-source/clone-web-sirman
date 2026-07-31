"""
find_image_urls.py - Live Diagram Image URL Interceptor
=========================================================
Monitors browser requests in REAL-TIME and prints image/diagram URLs.
Does not close until you close the browser window.
"""

import asyncio
from playwright.async_api import async_playwright

async def main():
    print("=" * 65)
    print("  SIRMAN DIAGRAM IMAGE INTERCEPTOR (Live Listener)")
    print("=" * 65)
    print("  1. LOGIN in the browser window")
    print("  2. Click on ANY machine model")
    print("  3. Click to open the Exploded View / Diagram")
    print("  4. Watch the terminal output below for real-time image URLs!")
    print("=" * 65)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=["--start-maximized"])
        ctx = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await ctx.new_page()

        def on_response(res):
            url = res.url
            ct = res.headers.get("content-type", "").lower()
            if any(ext in url.lower() for ext in [".png", ".jpg", ".svg", ".pdf", "exploded", "media", "diagram"]) or "image" in ct:
                if not any(ignore in url for ignore in ["hubspot", "google", "favicon", "login-image", "analytics"]):
                    print(f"\n[FOUND IMAGE URL] -> {url}")

        page.on("response", on_response)
        await page.goto("https://service.sirman.com/catalog", wait_until="domcontentloaded")

        # Keep browser open until user closes it
        print("\n[LISTENING...] Browser is open. Interact with the website now.")
        try:
            while len(browser.contexts) > 0 and len(page.context.pages) > 0:
                await asyncio.sleep(1)
        except Exception:
            pass

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[STOPPED]")
