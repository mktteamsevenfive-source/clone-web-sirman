"""
Sirman Catalog Web Scraper (Playwright)
=======================================
- Opens service.sirman.com in a real browser
- Waits for the user to log in manually
- Intercepts XHR/Fetch network requests to capture the real API data
- Saves categories + products to sirman_data.json

Usage:
  python scraper.py

Requirements:
  pip install playwright
  playwright install chromium
"""

import asyncio
import json
import sys
from pathlib import Path

try:
    from playwright.async_api import async_playwright, Page
except ImportError:
    print("Playwright not installed. Run: pip install playwright && playwright install chromium")
    sys.exit(1)


OUTPUT_FILE = Path(__file__).parent / "sirman_data.json"
BASE_URL = "https://service.sirman.com"

captured_data = {
    "categories": [],
    "products": {},
    "api_responses": {}
}


def try_parse_json(data: str):
    try:
        return json.loads(data)
    except Exception:
        return None


async def handle_response(response):
    """Intercept network responses and capture catalog/product API data"""
    url = response.url
    
    # Capture any JSON API response that looks like catalog data
    if any(keyword in url for keyword in [
        "catalog", "categor", "product", "machine", "part", "spare",
        "item", "list", "search", "apollo", "/api/"
    ]) and "sirman.com" in url:
        try:
            content_type = response.headers.get("content-type", "")
            if "json" in content_type or "application/json" in content_type:
                body = await response.text()
                parsed = try_parse_json(body)
                if parsed:
                    print(f"[CAPTURED] {url}")
                    print(f"  Keys: {list(parsed.keys()) if isinstance(parsed, dict) else f'List of {len(parsed)} items'}")
                    captured_data["api_responses"][url] = parsed
        except Exception as e:
            pass


async def scrape_dom_categories(page: Page):
    """Scrape category names and links from the rendered DOM"""
    print("\n[INFO] Extracting categories from DOM...")
    
    try:
        await page.wait_for_selector("a[href*='catalog'], [class*='category'], [class*='Category']", timeout=15000)
    except Exception:
        print("[WARN] Category selector timed out, trying generic content...")
    
    categories = await page.evaluate("""() => {
        const results = [];
        const selectors = [
            'a[href*="/catalog/"]',
            '[class*="CategoryCard"]',
            '[class*="category-card"]',
            '[class*="MachineCard"]',
            '[data-testid*="category"]'
        ];
        
        for (const sel of selectors) {
            const elements = document.querySelectorAll(sel);
            elements.forEach(el => {
                const text = el.innerText?.trim();
                const href = el.href || '';
                if (text && text.length > 2 && text.length < 100) {
                    results.push({ name: text, href: href });
                }
            });
            if (results.length > 3) break;
        }
        return results;
    }""")
    
    print(f"[INFO] Found {len(categories)} category links from DOM")
    captured_data["categories"] = categories
    return categories


async def scrape_product_list(page: Page):
    """Scrape product/part items visible in list view"""
    products = await page.evaluate("""() => {
        const rows = [];
        
        const tableRows = document.querySelectorAll('tr');
        tableRows.forEach(row => {
            const cells = row.querySelectorAll('td');
            if (cells.length >= 2) {
                const rowData = {};
                cells.forEach((cell, i) => {
                    const text = cell.innerText?.trim();
                    if (text) rowData[`col_${i}`] = text;
                });
                if (Object.keys(rowData).length > 1) rows.push(rowData);
            }
        });
        
        return rows;
    }""")
    
    return products


async def main():
    print("=" * 60)
    print("  SIRMAN CATALOG SCRAPER  (Playwright Browser)")
    print("=" * 60)
    print("\nThis script will:")
    print("  1. Open service.sirman.com in a Chrome browser window")
    print("  2. Intercept all API calls to capture catalog data")
    print("  3. Ask you to log in manually with your Sirman account")
    print("  4. Navigate through categories to capture part data")
    print("  5. Save everything to sirman_data.json")
    print("\nPress Ctrl+C at any time to stop.")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=200,
            args=["--start-maximized"]
        )
        
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        page = await context.new_page()
        page.on("response", handle_response)
        
        print("\n[INFO] Navigating to service.sirman.com...")
        await page.goto(f"{BASE_URL}/catalog", wait_until="domcontentloaded")
        
        print("\n[IMPORTANT] Browser window is open!")
        print("  -> Please LOG IN to service.sirman.com using your credentials")
        print("  -> After login, the catalog page should load automatically")
        print("")
        input("  >> Press Enter here AFTER you have logged in and the Catalog page is visible...")
        
        print("\n[INFO] Capturing catalog page data...")
        
        # Screenshot
        screenshot_path = Path(__file__).parent / "scraper_screenshot.png"
        await page.screenshot(path=str(screenshot_path), full_page=False)
        print(f"[INFO] Screenshot saved: {screenshot_path}")
        
        captured_data["page_url"] = page.url
        captured_data["page_title"] = await page.title()
        
        # Wait for render
        try:
            await page.wait_for_load_state("networkidle", timeout=10000)
        except:
            pass
        await asyncio.sleep(3)
        
        # Capture categories
        categories = await scrape_dom_categories(page)
        
        # Capture full page text (first 8000 chars)
        page_text = await page.evaluate("() => document.body.innerText")
        captured_data["full_page_text"] = page_text[:8000]
        
        # Get all sidebar category links
        print("\n[INFO] Collecting all catalog links...")
        catalog_links_data = await page.evaluate("""() => {
            const links = Array.from(document.querySelectorAll('a'));
            return links
                .filter(a => a.href && a.href.includes('/catalog'))
                .map(a => ({ href: a.href, text: a.innerText?.trim() }))
                .filter(a => a.text && a.text.length > 1);
        }""")
        captured_data["catalog_links"] = catalog_links_data
        print(f"[INFO] Found {len(catalog_links_data)} catalog links total")
        
        # Visit first 8 category pages
        print("\n[INFO] Visiting category pages to capture product data...")
        visited_hrefs = set()
        
        for link_data in catalog_links_data[:10]:
            href = link_data.get("href", "")
            text = link_data.get("text", "")
            
            # Only visit category pages (not the base /catalog)
            if href in visited_hrefs or href.rstrip("/") == f"{BASE_URL}/catalog":
                continue
            if "/catalog/" not in href:
                continue
            
            visited_hrefs.add(href)
            
            try:
                print(f"[INFO] Visiting: {text[:40]} -> {href}")
                await page.goto(href, wait_until="domcontentloaded")
                
                try:
                    await page.wait_for_load_state("networkidle", timeout=8000)
                except:
                    pass
                await asyncio.sleep(2)
                
                # Capture products on this category page
                products = await scrape_product_list(page)
                
                # Also capture full text of this page
                cat_text = await page.evaluate("() => document.body.innerText")
                
                cat_key = href.split("/catalog/")[-1].split("?")[0] or text
                captured_data["products"][cat_key] = {
                    "name": text,
                    "url": href,
                    "products_table": products,
                    "page_text": cat_text[:3000]
                }
                print(f"  -> Captured {len(products)} product rows")
                
            except Exception as e:
                print(f"[WARN] Error visiting {href}: {e}")
                continue
        
        # Save final data
        print(f"\n[INFO] Saving scraped data to {OUTPUT_FILE}...")
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(captured_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n[SUCCESS] Data saved to: {OUTPUT_FILE}")
        print(f"  Categories found: {len(categories)}")
        print(f"  API responses captured: {len(captured_data.get('api_responses', {}))}")
        print(f"  Product pages scraped: {len(captured_data.get('products', {}))}")
        print(f"  Catalog links found: {len(catalog_links_data)}")
        
        input("\n  >> Press Enter to close the browser and finish...")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
