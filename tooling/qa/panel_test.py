"""Playwright checks for the chat panel (PLAN-v6, Part W).

Loads each page with window.PS_CHAT_URL pointed at the stand-in chat app
(tooling/qa/fake-webui/), fails on any console/page error, opens the panel
(W1: Ask button on every page), and checks it survives a page switch.
Later tasks (W3+) add the sign-in-from-inside-the-panel checks.

Usage: python3 tooling/qa/panel_test.py <site-base-url> <chat-base-url>
"""
import asyncio
import os
import sys

from playwright.async_api import async_playwright

PAGES = ["index.html", "master-table.html", "software-share.html", "under-the-hood.html", "property.html?id=1"]
SCREENSHOT_DIR = "/tmp/qa"


async def check_console_errors(page, path, bugs):
    errs = []
    page.on("pageerror", lambda e: errs.append(f"pageerror: {e}"))
    page.on("console", lambda m: m.type == "error" and errs.append(f"console: {m.text}"))
    resp = await page.goto(path, wait_until="networkidle")
    if resp is None or resp.status >= 400:
        bugs.append(f"{path}: failed to load (status {resp.status if resp else 'none'})")
    for e in errs:
        bugs.append(f"{path}: {e}")
    return resp


async def main():
    site = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8766"
    chat = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:3001"
    bugs = []
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch()

        for width, height, tag in [(1440, 900, "desktop"), (390, 844, "phone")]:
            context = await browser.new_context(viewport={"width": width, "height": height})
            await context.add_init_script(f"window.PS_CHAT_URL = {chat!r};")
            for page_path in PAGES:
                page = await context.new_page()
                await check_console_errors(page, f"{site}/{page_path}", bugs)

                ask = page.locator("[data-chat-toggle]").first
                await ask.click()
                panel = page.locator("#chat-panel")
                is_open = await panel.evaluate("(el) => el.classList.contains('open')")
                if not is_open:
                    bugs.append(f"{page_path} ({tag}): Ask button didn't open the panel")

                safe_name = page_path.split("?")[0].replace(".html", "") or "index"
                await page.screenshot(path=f"{SCREENSHOT_DIR}/{tag}-{safe_name}-panel-open.png")
                await page.close()

            # Panel state survives a page switch (sessionStorage), desktop only.
            if tag == "desktop":
                page = await context.new_page()
                await check_console_errors(page, f"{site}/index.html", bugs)
                await page.locator("[data-chat-toggle]").first.click()
                await page.goto(f"{site}/master-table.html", wait_until="networkidle")
                still_open = await page.locator("#chat-panel").evaluate("(el) => el.classList.contains('open')")
                if not still_open:
                    bugs.append("panel did not stay open across a page switch")
                await page.close()

            await context.close()

        await browser.close()

    if bugs:
        print(f"panel_test.py: {len(bugs)} bug(s):")
        for b in bugs:
            print(f" - {b}")
        sys.exit(1)
    print("panel_test.py: clean")


if __name__ == "__main__":
    asyncio.run(main())
