"""
Test Sirman Auth Redirect & Auto Login
"""

import asyncio
from playwright.async_api import async_playwright

USERNAME = "korralak.sa@sevenfive.co.th"
PASSWORD = "Service@1234"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=200)
        ctx = await browser.new_context()
        page = await ctx.new_page()

        print("[1] Opening https://www.service.sirman.com/login ...")
        await page.goto("https://www.service.sirman.com/login", wait_until="networkidle")

        print("[2] Clicking the red LOGIN button...")
        # Find button with text 'LOGIN'
        login_btn = await page.wait_for_selector("button:has-text('LOGIN'), a:has-text('LOGIN'), .login-btn")
        if login_btn:
            await login_btn.click()

        print("[3] Waiting for redirected Auth page to load...")
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(3000)

        print(f"Redirected URL: {page.url}")

        # Find input fields on auth page
        inputs = await page.query_selector_all("input")
        print(f"Auth Page Inputs count: {len(inputs)}")
        for i in inputs:
            itype = await i.get_attribute("type")
            iname = await i.get_attribute("name")
            iid = await i.get_attribute("id")
            ipth = await i.get_attribute("placeholder")
            print(f"  Input: type={itype}, name={iname}, id={iid}, placeholder={ipth}")

        # Try filling username & password
        user_input = None
        pass_input = None

        for i in inputs:
            itype = (await i.get_attribute("type") or "").lower()
            iname = (await i.get_attribute("name") or "").lower()
            iid = (await i.get_attribute("id") or "").lower()

            if itype == "password" or "pass" in iname or "pass" in iid:
                pass_input = i
            elif itype in ["email", "text", "username"] or any(x in iname or x in iid for x in ["user", "email", "login"]):
                if not user_input:
                    user_input = i

        if not user_input and len(inputs) >= 2:
            user_input = inputs[0]
            pass_input = inputs[1]

        if user_input and pass_input:
            print(f"[4] Filling credentials for {USERNAME}...")
            await user_input.fill(USERNAME)
            await pass_input.fill(PASSWORD)
            await page.wait_for_timeout(1000)

            # Click submit
            submits = await page.query_selector_all("button[type='submit'], input[type='submit'], button:has-text('Sign in'), button:has-text('Log in'), button:has-text('Accedi')")
            if submits:
                print("[5] Submitting login form...")
                await submits[0].click()
            else:
                print("[5] Pressing Enter on password field...")
                await pass_input.press("Enter")

            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(5000)

            print(f"[6] Final URL after login: {page.url}")
        else:
            print("[WARN] Could not find username/password inputs on auth page.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
