"""W8 real check (free, no bot calls): with the real Open WebUI running
locally (docker compose -f chatbot/docker-compose.local.yml ... up), load the
site with the panel pointed at it and confirm the panel's own sign-in card
appears on first open -- the signed-out GET /api/v1/auths/ returns 401, which
is exactly what the panel uses to decide (W8).

Usage: python3 tooling/qa/w8_real_check.py [site-port] [chat-url]
"""
import asyncio
import sys

from playwright.async_api import async_playwright

SITE_PORT = sys.argv[1] if len(sys.argv) > 1 else "8765"
CHAT = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:3000"


async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        await context.add_init_script(f"window.PS_CHAT_URL = {CHAT!r};")
        page = await context.new_page()
        await page.goto(f"http://localhost:{SITE_PORT}/master-table.html", wait_until="networkidle")
        await page.locator("[data-chat-toggle]").first.click()

        card = page.locator("#chat-panel-signin-card")
        await card.wait_for(state="visible", timeout=10000)
        assert await card.locator("#chat-panel-signin").is_visible(), "sign-in button not visible"
        await page.screenshot(path="/tmp/qa/w8-real-card-shown.png")
        print("w8 real check: sign-in card shows over the framed (signed-out) Open WebUI — OK")

        # Signed-in admin cookie must hide the card (uses Open WebUI's own
        # signin API; throwaway local-admin account, deleted afterwards).
        import urllib.request, json
        base = CHAT.rstrip("/")
        async def with_cookie():
            token_req = urllib.request.Request(
                base + "/api/v1/auths/signin",
                data=json.dumps({"email": "w8-check@localhost", "password": "w8-check-temp"}).encode(),
                headers={"Content-Type": "application/json"}, method="POST")
            try:
                with urllib.request.urlopen(token_req) as r:
                    token = json.load(r)["token"]
            except urllib.error.HTTPError:
                # signup off / unknown account: skip the signed-in half
                return None
            return token
        token = await with_cookie()
        if token:
            await context.add_cookies([{"name": "token", "value": token, "url": base}])
            await page.evaluate("() => { const f = document.getElementById('chat-panel-frame'); f.setAttribute('src', f.getAttribute('src')); }")
            await card.wait_for(state="hidden", timeout=10000)
            print("w8 real check: card hidden once signed in (cookie) — OK")
        else:
            print("w8 real check: skipped signed-in half (signup disabled, no throwaway account)")

        await browser.close()


asyncio.run(main())
