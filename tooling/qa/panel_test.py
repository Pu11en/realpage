"""Playwright checks for the chat panel (PLAN-v6, Part W).

Stub for W0: loads each page with window.PS_CHAT_URL pointed at the stand-in
chat app (tooling/qa/fake-webui/) and fails on any console error or page
error. Later tasks (W1+) add the actual panel-open/sign-in/reload checks.

Usage: python3 tooling/qa/panel_test.py <site-base-url> <chat-base-url>
"""
import asyncio
import sys

from playwright.async_api import async_playwright

PAGES = ["index.html", "master-table.html", "software-share.html", "under-the-hood.html", "property.html?id=1"]


async def main():
    site = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8766"
    chat = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:3001"
    bugs = []

    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        await context.add_init_script(f"window.PS_CHAT_URL = {chat!r};")
        for page_path in PAGES:
            page = await context.new_page()
            errs = []
            page.on("pageerror", lambda e: errs.append(f"pageerror: {e}"))
            page.on("console", lambda m: m.type == "error" and errs.append(f"console: {m.text}"))
            resp = await page.goto(f"{site}/{page_path}", wait_until="networkidle")
            if resp is None or resp.status >= 400:
                bugs.append(f"{page_path}: failed to load (status {resp.status if resp else 'none'})")
            for e in errs:
                bugs.append(f"{page_path}: {e}")
            await page.close()
        await browser.close()

    if bugs:
        print(f"panel_test.py: {len(bugs)} bug(s):")
        for b in bugs:
            print(f" - {b}")
        sys.exit(1)
    print("panel_test.py: clean")


if __name__ == "__main__":
    asyncio.run(main())
