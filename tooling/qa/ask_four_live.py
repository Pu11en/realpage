"""A5 check: ask the four graded questions in the real local panel and save the answers.

Needs the local stack up (bash tooling/dev.sh). Writes answers to the path given as
argv[1] (default /tmp/ask4.json) and prints them.
"""
import asyncio, os, sys, json, re, subprocess
from playwright.async_api import async_playwright

CHAT = "http://localhost:3000"; SITE = "http://localhost:8765"
OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/ask4.json"
QUESTIONS = [
    "Any new apartment buildings opening in Austin that haven't picked software yet?",
    "Show me buildings that just sold in Dallas–Fort Worth",
    "Where is RealPage losing customers to Entrata?",
    "What's going on with the RealPage lawsuit?",
]

def mint():
    code = ("import asyncio\nfrom open_webui.utils.auth import create_token\nfrom open_webui.models.users import Users\n"
            "async def m():\n    u = await Users.get_user_by_email('kidquick360@gmail.com')\n    print(create_token({'id': u.id}))\nasyncio.run(m())\n")
    out = subprocess.run(["docker", "exec", "ps-chat-open-webui-1", "python3", "-c", code], capture_output=True, text=True, timeout=60)
    return out.stdout.strip().splitlines()[-1] if out.stdout.strip() else ""

async def main():
    token = mint()
    answers = []
    async with async_playwright() as pw:
        b = await pw.chromium.launch(); ctx = await b.new_context(viewport={"width": 1440, "height": 900})
        if token: await ctx.add_cookies([{"name": "token", "value": token, "url": CHAT}])
        page = await ctx.new_page()
        await page.goto(CHAT + "/auth?redirect=%2F", wait_until="domcontentloaded")
        if token: await page.evaluate("t => localStorage.setItem('token', t)", token)
        await page.goto(SITE + "/master-table.html", wait_until="networkidle")
        await page.locator("[data-chat-toggle]").first.click()
        frame = page.frame_locator("#chat-panel-frame")
        box = frame.locator("#chat-input").first; await box.wait_for(timeout=30000)
        only = [int(x) for x in os.environ.get("QS", "").split(",") if x]
        for i, q in enumerate(QUESTIONS):
            if only and i not in only: continue
            await box.click(); await box.fill(""); await box.type(q, delay=5); await box.press("Enter")
            body = frame.locator("body")
            before = await body.inner_text()
            prev = before; stable = 0
            for _ in range(300):
                await page.wait_for_timeout(1000)
                txt = await body.inner_text()
                stable = stable + 1 if txt == prev else 0
                prev = txt
                if stable >= 10 and len(txt) > len(before) + 60: break
            html = await body.inner_html()
            links = re.findall(r'href="([^"]+)"', html)
            # keep only what was added by this answer
            i = 0
            while i < min(len(before), len(prev)) and before[i] == prev[i]: i += 1
            prev = prev[i:].strip()
            answers.append({"q": q, "answer": prev, "links": links})
            print("===", q, "\n", prev, "\nLINKS:", links, flush=True)
            json.dump(answers, open(OUT, "w"), indent=1)
        await b.close()

asyncio.run(main())
