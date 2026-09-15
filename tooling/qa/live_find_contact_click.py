# Real click-through of the 🔍 Find contact link against the running dev stack.
# Site on SITE (default http://localhost:8765), chat app on http://localhost:3000.
# Ask "give me top leads any area", check every lead line has a phone/link/Find contact,
# click one Find contact link, confirm "Deep dive on …" is sent and answered.
# Screenshot: tooling/qa/shots/find-contact.png
import asyncio, os, re, sys
from urllib.parse import unquote
from playwright.async_api import async_playwright
SITE = os.environ.get("SITE", "http://localhost:8765")
SHOT = os.path.join(os.path.dirname(__file__), "shots", "find-contact.png")

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1400, "height": 1000})
        errs = []; pg.on("console", lambda m: m.type == "error" and errs.append(m.text))
        await pg.goto(SITE + "/index.html")
        await pg.locator("[data-chat-toggle]").first.click()
        fr = pg.frame_locator("#chat-panel-frame")
        ta = fr.locator("#chat-input").first
        await ta.wait_for(timeout=60000); await pg.wait_for_timeout(1500)
        await ta.click(); await ta.type("give me top leads any area"); await ta.press("Enter")
        # wait for the answer to finish (Find contact links or phones present, no "stop" button)
        for _ in range(120):
            await pg.wait_for_timeout(2000)
            n = await fr.locator('a[href^="#ask:"]').count()
            stopping = await fr.locator('button[aria-label="Stop"]').count()
            if n and not stopping: break
        pass
        text = await fr.locator("body").inner_text()
        print("find-contact links:", n)
        lines = await fr.locator("ol li").evaluate_all("e=>e.map(x=>x.innerText)")
        if not n: print("BODY:", text[:1500])
        for l in lines: print("  lead:", l[:140])
        bad = [l for l in lines if not re.search(r"📞|\(\d{3}\) \d{3}-\d{4}|Find contact|record|News|Website|Permit|Agenda", l)]
        print("lead lines:", len(lines), "without contact/link:", len(bad))
        if not n: print("no Find contact link in this answer"); sys.exit(2)
        n_msgs_before = 0
        link = fr.locator('a[href^="#ask:"]').first
        want = unquote((await link.get_attribute("href"))[5:])
        print("clicking:", want)
        await pg.screenshot(path=SHOT.replace(".png", "-before.png"))
        await link.click()
        await pg.wait_for_timeout(1500)
        print("site url after click:", pg.url)
        # the click must have sent a user message with that text
        for _ in range(15):
            body = await fr.locator("body").inner_text()
            if want[:30] in body: break   # the new user message (the link itself reads 'Find contact')
            await pg.wait_for_timeout(1000)
        else:
            print("user message sent: NO"); await pg.screenshot(path=SHOT); sys.exit(1)
        print("user message sent: yes")
        for _ in range(120):
            await pg.wait_for_timeout(2000)
            stopping = await fr.locator('button[aria-label="Stop"]').count()
            n_msgs = 2
            body = await fr.locator("body").inner_text()
            after = body[body.rfind(want[:30]) + 30:]
            if not stopping and len(after.strip()) > 120: break
        body = await fr.locator("body").inner_text()
        tail = body[body.rfind(want[:30]):][:600]
        print("answer tail:", tail.replace("\n", " | ")[:600])
        await pg.screenshot(path=SHOT)
        print("errors:", errs[:5])
        await b.close()
        ok = n > 0 and not bad and len(tail) > 120
        print("RESULT:", "PASS" if ok else "FAIL")
        sys.exit(0 if ok else 1)
asyncio.run(main())
