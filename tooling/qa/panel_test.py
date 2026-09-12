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

        # W4: hardening checks (rapid double-click, close/reopen doesn't
        # reload, ESC closes on desktop, Chat tab active while open).
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        await context.add_init_script(f"window.PS_CHAT_URL = {chat!r};")
        page = await context.new_page()
        await check_console_errors(page, f"{site}/index.html", bugs)

        ask = page.locator("[data-chat-toggle]").first
        await ask.click()
        await ask.click()
        frame_count = await page.locator("#chat-panel-frame").count()
        if frame_count != 1:
            bugs.append(f"rapid double-click created {frame_count} chat frames, expected 1")
        still_open = await page.locator("#chat-panel").evaluate("(el) => el.classList.contains('open')")
        if still_open:
            bugs.append("rapid double-click (open, close) left the panel open")

        # Reopen and sign in (fake-webui starts signed out) so the chat view
        # is visible, then type a message, close, reopen: the frame must not
        # reload (message stays), proving close/open doesn't reset it.
        await ask.click()
        signin_btn = page.locator("#chat-panel-signin")
        await signin_btn.wait_for(state="visible", timeout=5000)
        async with context.expect_page() as popup_info:
            await signin_btn.click()
        popup = await popup_info.value
        await popup.wait_for_load_state()
        async with popup.expect_event("close"):
            await popup.locator("#signin").click()
        chat_frame = page.frame_locator("#chat-panel-frame")
        await chat_frame.locator("#msg-input").wait_for(state="visible", timeout=5000)
        await chat_frame.locator("#msg-input").fill("hello from panel_test")
        await chat_frame.locator("#send").click()
        await page.locator("#chat-panel-close").click()
        await ask.click()
        messages_text = await chat_frame.locator("#messages").inner_text()
        if "hello from panel_test" not in messages_text:
            bugs.append("closing and reopening the panel reloaded the chat frame (message was lost)")

        # ESC closes the panel on desktop.
        await page.keyboard.press("Escape")
        closed_after_esc = not await page.locator("#chat-panel").evaluate("(el) => el.classList.contains('open')")
        if not closed_after_esc:
            bugs.append("ESC did not close the panel on desktop")
        nav_chat_active = await page.locator(".nav-chat").evaluate("(el) => el.classList.contains('active')")
        if nav_chat_active:
            bugs.append("Chat nav link stayed active after ESC closed the panel")

        await page.close()
        await context.close()

        # W3: sign-in from inside the panel. The stand-in's login screen posts
        # its auth state to the panel, which shows its own "Sign in with
        # Google" button (Google refuses to load inside a frame), opens the
        # chat app as a popup, and reloads the framed copy once it closes.
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        await context.add_init_script(f"window.PS_CHAT_URL = {chat!r};")
        page = await context.new_page()
        await check_console_errors(page, f"{site}/index.html", bugs)
        await page.locator("[data-chat-toggle]").first.click()

        signin_btn = page.locator("#chat-panel-signin")
        try:
            await signin_btn.wait_for(state="visible", timeout=5000)
        except Exception:
            bugs.append("sign-in: panel didn't show the Sign in with Google button for a signed-out frame")

        if await signin_btn.is_visible():
            async with context.expect_page() as popup_info:
                await signin_btn.click()
            popup = await popup_info.value
            await popup.wait_for_load_state()
            async with popup.expect_event("close"):
                await popup.locator("#signin").click()

            frame_shows_chat = False
            for _ in range(20):
                frame_el = page.frame_locator("#chat-panel-frame")
                try:
                    if await frame_el.locator("#chat").is_visible(timeout=500):
                        frame_shows_chat = True
                        break
                except Exception:
                    pass
                await page.wait_for_timeout(300)
            if not frame_shows_chat:
                bugs.append("sign-in: frame didn't show the chat after the popup closed")

            signin_hidden = not await signin_btn.is_visible()
            if not signin_hidden:
                bugs.append("sign-in: panel kept showing the Sign in button after signing in")

        await page.close()
        await context.close()

        # W6: docked on desktop/tablet -- the panel must not float over the
        # page content. Check that the shell's bounding box doesn't overlap
        # the panel's, and there's no horizontal scrollbar, at 1440 and 1024.
        for width, height in [(1440, 900), (1024, 900)]:
            context = await browser.new_context(viewport={"width": width, "height": height})
            await context.add_init_script(f"window.PS_CHAT_URL = {chat!r};")
            for page_path in PAGES:
                page = await context.new_page()
                await check_console_errors(page, f"{site}/{page_path}", bugs)
                await page.locator("[data-chat-toggle]").first.click()
                await page.wait_for_timeout(400)

                shell_box = await page.locator(".shell").bounding_box()
                panel_box = await page.locator("#chat-panel").bounding_box()
                if shell_box and panel_box:
                    shell_right = shell_box["x"] + shell_box["width"]
                    panel_left = panel_box["x"]
                    if shell_right > panel_left + 0.5:
                        bugs.append(
                            f"{page_path} ({width}px): page content (right edge {shell_right:.0f}) "
                            f"overlaps the docked panel (left edge {panel_left:.0f})"
                        )

                has_hscroll = await page.evaluate(
                    "() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1"
                )
                if has_hscroll:
                    bugs.append(f"{page_path} ({width}px): horizontal scroll appeared with the panel docked")

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
