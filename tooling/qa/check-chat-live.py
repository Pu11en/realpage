"""Drew's local test: does the PropertyStack panel really answer, with citations?

Runs the REAL panel on the REAL local stack (no stand-in page, no Google popup):
the sign-in cookie/token is seeded exactly the way the popup leaves it after
Google sign-in, then each question is typed into the framed chat and the answer
must contain the key facts Drew already approved on 2026-09-10.

Requirements: the local stack is up
  docker compose -f chatbot/docker-compose.local.yml --env-file chatbot/.env.local -p ps-chat up -d
and the site is being served (check-chat-live.sh starts one for you).

Usage:
  python3 tooling/qa/check-chat-live.py [site-port] [chat-url]
Env:
  PS_CHAT_TOKEN   use this session token instead of minting one from the container

Exit code: 0 = every question answered with the expected facts, 1 = a failure.
"""
import asyncio
import os
import subprocess
import sys
import urllib.request

from playwright.async_api import async_playwright

SITE_PORT = sys.argv[1] if len(sys.argv) > 1 else "8765"
CHAT = (sys.argv[2] if len(sys.argv) > 2 else "http://localhost:3000").rstrip("/")
SITE = f"http://localhost:{SITE_PORT}"
ADMIN_EMAIL = "kidquick360@gmail.com"

# Question -> facts that must appear in the answer (case-insensitive). These are
# the facts Drew checked against the CSVs in chatbot/TEST-ANSWERS-2026-09-10.md.
QUESTIONS = [
    ("Which vendor runs the most buildings?", ["Yardi", "66"]),
    ("Which buildings sold in 2026, and who bought them?", ["Park Residences"]),
    ("What are the top 5 leads right now, and why?", ["390"]),
]


def mint_token() -> str:
    """Ask the running container for a valid session token (test shortcut)."""
    code = (
        "import asyncio\n"
        "from open_webui.utils.auth import create_token\n"
        "from open_webui.models.users import Users\n"
        "async def m():\n"
        f"    u = await Users.get_user_by_email('{ADMIN_EMAIL}')\n"
        "    print(create_token({'id': u.id}))\n"
        "asyncio.run(m())\n"
    )
    out = subprocess.run(
        ["docker", "exec", "ps-chat-open-webui-1", "python3", "-c", code],
        capture_output=True, text=True, timeout=60,
    )
    token = out.stdout.strip().splitlines()[-1] if out.stdout.strip() else ""
    if not token:
        raise SystemExit(
            "Could not mint a sign-in token. Is the stack up?\n"
            "  docker compose -f chatbot/docker-compose.local.yml --env-file chatbot/.env.local -p ps-chat up -d\n"
            f"docker said: {out.stderr.strip()[-400:]}"
        )
    return token


def chat_reachable() -> bool:
    try:
        with urllib.request.urlopen(CHAT + "/api/config", timeout=5):
            return True
    except Exception:
        return False


async def ask(frame, page, question, must_contain):
    box = frame.locator("#chat-input").first
    await box.wait_for(timeout=30000)
    await box.click()
    await box.fill("")
    await box.type(question, delay=10)
    await box.press("Enter")

    # A long table answer can take 20-30s to finish streaming; keep polling
    # until every expected fact has appeared (or the timeout runs out).
    body = frame.locator("body")
    last = ""
    for _ in range(150):  # up to ~2.5 min
        await page.wait_for_timeout(1000)
        last = await body.inner_text()
        lowered = last.lower()
        if all(s.lower() in lowered for s in must_contain):
            break
    return last


async def main():
    if not chat_reachable():
        raise SystemExit(
            f"The chat app at {CHAT} is not answering. Start the stack first:\n"
            "  docker compose -f chatbot/docker-compose.local.yml --env-file chatbot/.env.local -p ps-chat up -d"
        )
    token = os.environ.get("PS_CHAT_TOKEN") or mint_token()

    failures, results = [], []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        ctx = await browser.new_context(viewport={"width": 1440, "height": 900})
        await ctx.add_cookies([{"name": "token", "value": token, "url": CHAT}])
        page = await ctx.new_page()
        # Seed the chat origin's own storage, exactly as the Google popup leaves
        # it, then open the site so the framed panel is already signed in.
        await page.goto(CHAT + "/auth?redirect=%2F", wait_until="domcontentloaded")
        await page.evaluate("t => localStorage.setItem('token', t)", token)

        console_errors = []
        page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)

        await page.goto(SITE + "/master-table.html", wait_until="networkidle")
        await page.locator("[data-chat-toggle]").first.click()
        frame = page.frame_locator("#chat-panel-frame")
        await frame.locator("#chat-input").first.wait_for(timeout=30000)

        for question, must in QUESTIONS:
            text = await ask(frame, page, question, must)
            lowered = text.lower()
            missing = [s for s in must if s.lower() not in lowered]
            ok = not missing
            results.append((question, ok, missing or must))
            if not ok:
                failures.append((question, missing))
            print(f"{'PASS' if ok else 'FAIL'}  {question}")

        # A 'no socket' answer means the panel rendered live (the W8 CORS bug).
        socket_errors = [e for e in console_errors if "socket" in e.lower()]
        await browser.close()

    print()
    print(f"questions: {len(QUESTIONS) - len(failures)}/{len(QUESTIONS)} passed")
    print(f"live-render socket errors: {len(socket_errors)}")
    if failures:
        print("FAILURES:")
        for q, missing in failures:
            print(f"  - {q} (missing: {', '.join(missing)})")
        sys.exit(1)
    print("PASS — the local panel answers every question with the approved facts.")


if __name__ == "__main__":
    asyncio.run(main())
