"""
Test Playwright Context Request to download real PDF files
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

BASE_DIR = Path(__file__).parent
PDF_DIR = BASE_DIR / "pdf_diagrams"
PDF_DIR.mkdir(exist_ok=True)

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=["--start-maximized"])
        ctx = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await ctx.new_page()

        print("[1] Opening catalog page...")
        await page.goto("https://service.sirman.com/catalog", wait_until="domcontentloaded")

        print("\n[2] Please LOG IN in the browser window, then press ENTER.")
        input("  >> Press ENTER after logging in... ")

        # Test download with context request
        test_file = "Agat1.pdf"
        
        # Intercept request headers from page to find authorization token
        token = await page.evaluate("() => localStorage.getItem('token') || localStorage.getItem('auth_token') || sessionStorage.getItem('token') || ''")
        print(f"[INFO] LocalStorage Token: {token[:30] if token else 'None'}")

        # Try API endpoint with ctx.request
        urls_to_try = [
            f"https://api-service.sirman.com/service-dwh/files/{test_file}",
            f"https://api-service.sirman.com/service-dwh/exploded-views/677/file",
            f"https://service.sirman.com/pdf/{test_file}"
        ]

        for url in urls_to_try:
            try:
                resp = await ctx.request.get(url)
                body = await resp.body()
                print(f"URL: {url} -> Status: {resp.status}, Content-Type: {resp.headers.get('content-type')}, Size: {len(body)} bytes")
                if resp.status == 200 and len(body) > 5000:
                    with open(PDF_DIR / test_file, "wb") as f:
                        f.write(body)
                    print(f"SUCCESS! Downloaded {test_file} ({len(body)/1024:.1f} KB)")
                    break
            except Exception as e:
                print(f"Error for {url}: {e}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
