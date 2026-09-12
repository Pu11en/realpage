"""W7 check (PLAN-v6): the real Open WebUI, running via docker compose, must not
show a model picker (or the Arena/temporary-chat clutter) to a signed-in admin or
a normal user, at the 480px panel width. No calls to the chat model are made.

Requires the local trial stack up already:
  docker compose -f chatbot/docker-compose.local.yml --env-file chatbot/.env.local -p ps-chat up -d
and two throwaway accounts already created via /api/v1/auths/signup (one promoted
to admin) — see PLAN-v6.progress.md for exactly how this was set up locally.
"""
import asyncio
import sys

from playwright.async_api import async_playwright

WEBUI_URL = "http://localhost:3000"
SHOTS_DIR = "tooling/qa/shots"

# Selectors the compact custom.css already hides; assert they're not *visible*
# regardless of CSS, so a regression that only removes the CSS rule still fails.
MODEL_SELECTOR = "[data-testid='model-selector-model-button']"
ARENA_TEXT = "text=Arena Model"


async def check_account(pw, token: str, label: str) -> list[str]:
    problems = []
    browser = await pw.chromium.launch()
    page = await browser.new_page(viewport={"width": 480, "height": 800})

    await page.goto(WEBUI_URL)
    await page.evaluate(
        "(t) => { localStorage.setItem('token', t); }",
        token,
    )
    await page.goto(f"{WEBUI_URL}/")
    await page.wait_for_timeout(2000)

    # Dismiss the one-time "What's New" release-notes modal if it shows up —
    # unrelated first-run UX, not part of what W7 is checking.
    whats_new_button = page.locator("text=Okay, Let's Go!")
    if await whats_new_button.count() and await whats_new_button.first.is_visible():
        await whats_new_button.first.click()
        await page.wait_for_timeout(500)

    if await page.locator(MODEL_SELECTOR).count() and await page.locator(MODEL_SELECTOR).first.is_visible():
        problems.append(f"{label}: model selector button is visible")

    if await page.locator(ARENA_TEXT).count() and await page.locator(ARENA_TEXT).first.is_visible():
        problems.append(f"{label}: Arena Model clutter is visible")

    import os
    os.makedirs(SHOTS_DIR, exist_ok=True)
    await page.screenshot(path=f"{SHOTS_DIR}/w7-{label}.png")

    await browser.close()
    return problems


async def main():
    if len(sys.argv) != 3:
        print("usage: w7_real_webui_check.py <admin_token> <user_token>")
        return 2

    admin_token, user_token = sys.argv[1], sys.argv[2]
    problems = []
    async with async_playwright() as pw:
        problems += await check_account(pw, admin_token, "admin")
        problems += await check_account(pw, user_token, "user")

    if problems:
        print("W7 FAILED:")
        for p in problems:
            print(" -", p)
        return 1

    print("W7 OK: no model selector or Arena clutter for admin or user; screenshots in", SHOTS_DIR)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
