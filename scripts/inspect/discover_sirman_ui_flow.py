"""
Sirman UI Flow Discovery & Diagram Inspector
==============================================
Navigates the Sirman website step-by-step from Login -> Catalog -> Category -> Product -> Exploded View,
logging every single click, DOM selector, and network request for diagram media.
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

BASE_DIR = Path(__file__).parent
USERNAME = "korralak.sa@sevenfive.co.th"
PASSWORD = "Service@1234"

captured_media = []


async def main():
    print("=" * 65)
    print("  SIRMAN UI FLOW DISCOVERY")
    print("=" * 65)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=150, args=["--start-maximized"])
        ctx = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await ctx.new_page()

        async def on_resp(resp):
            u = resp.url
            ct = resp.headers.get("content-type", "")
            st = resp.status
            if any(k in u.lower() for k in ["pdf", "image", "file", "media", "svg", "exploded", "view", "dwh"]):
                if not any(ign in u for ign in ["hubspot", "google", "analytics", "lucide", "font", "css", "chunk.js"]):
                    info = f"{st} | {ct[:25]} | {u}"
                    captured_media.append(info)
                    print(f"  [MEDIA NET] {info}")

        page.on("response", on_resp)

        # 1. Login
        print("\n[STEP 1] Opening login page...")
        await page.goto("https://www.service.sirman.com/login", wait_until="networkidle")

        login_btn = await page.wait_for_selector("button:has-text('LOGIN'), .login-btn")
        if login_btn:
            await login_btn.click()
            await asyncio.sleep(2)

        user_el = await page.wait_for_selector("#inputEmail, input[type='email']")
        pass_el = await page.wait_for_selector("#inputPassword, input[type='password']")

        await user_el.fill(USERNAME)
        await pass_el.fill(PASSWORD)
        await page.click("button[type='submit'], input[type='submit']")
        await asyncio.sleep(3)

        auth_btn = await page.query_selector("button:has-text('Authorize')")
        if auth_btn:
            await auth_btn.click()
            await asyncio.sleep(4)

        print(f"[INFO] Post-login URL: {page.url}")
        await page.screenshot(path="step1_post_login.png")

        # 2. Go to Catalog
        print("\n[STEP 2] Navigating to Catalog...")
        await page.goto("https://www.service.sirman.com/catalog", wait_until="networkidle")
        await asyncio.sleep(3)
        await page.screenshot(path="step2_catalog.png")

        # Inspect cards / links on catalog
        cards = await page.query_selector_all("a, button, div[class*='card'], div[class*='Item']")
        print(f"Catalog elements count: {len(cards)}")
        for c in cards[:15]:
            try:
                txt = (await c.inner_text()).strip().replace("\n", " ")
                if txt and len(txt) < 80:
                    print(f"  Element: '{txt}'")
            except:
                pass

        # 3. Click first category (e.g. Slicers or Bar machines or Microwaves ovens)
        print("\n[STEP 3] Clicking category...")
        category_clicked = False
        for c in cards:
            try:
                txt = (await c.inner_text()).strip()
                if "Slicers" in txt or "Bar" in txt or "Microwave" in txt:
                    print(f"Clicking category '{txt}'...")
                    await c.click()
                    category_clicked = True
                    await asyncio.sleep(4)
                    break
            except:
                pass

        if not category_clicked:
            print("[WARN] Category card not clicked by text, trying first available card...")
            if cards:
                await cards[0].click()
                await asyncio.sleep(4)

        await page.screenshot(path="step3_category_products.png")
        print(f"Category page URL: {page.url}")

        # Inspect products on category page
        prod_elements = await page.query_selector_all("a, button, tr, div[class*='product'], div[class*='Item'], div[class*='row']")
        print(f"Products page elements count: {len(prod_elements)}")

        # 4. Click first product to open Exploded View
        print("\n[STEP 4] Clicking product to open Exploded View...")
        for p_el in prod_elements[:20]:
            try:
                txt = (await p_el.inner_text()).strip().replace("\n", " ")
                if txt and len(txt) > 3 and len(txt) < 100:
                    if any(kw in txt for kw in ["AGATA", "APOLLO", "MD 1000", "NE", "Exploded", "View"]):
                        print(f"Clicking product element '{txt[:40]}'...")
                        await p_el.click()
                        await asyncio.sleep(5)
                        break
            except:
                pass

        await page.screenshot(path="step4_exploded_view.png")
        print(f"Exploded view URL: {page.url}")

        # Inspect exploded view DOM elements (images, SVG, canvas, iframe)
        media_elements = await page.query_selector_all("img, svg, canvas, iframe, object, embed")
        print(f"\nExploded view media elements count: {len(media_elements)}")
        for m in media_elements:
            try:
                tag = await m.evaluate("el => el.tagName")
                src = await m.evaluate("el => el.src || el.href || el.getAttribute('data') || ''")
                cls = await m.evaluate("el => el.className")
                box = await m.bounding_box()
                w = box["width"] if box else 0
                h = box["height"] if box else 0
                print(f"  Tag: {tag} | Src: {src[:80]} | Class: {cls} | Size: {w}x{h}")
            except:
                pass

        print("\n[STEP 5] All media requests captured during flow:")
        for info in captured_media:
            print(f"  {info}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
