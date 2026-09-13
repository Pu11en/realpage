# Live click-through against the running dev stack (bash tooling/dev.sh): Early Leads ->
# Deep dive on Vantage At Spring Creek -> prompt in the real chat input; map card links checked.
# Screenshots: /tmp/p5-deepdive.png, /tmp/p5-map.png
import asyncio, urllib.request, ssl
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page(viewport={"width":1400,"height":900})
        errs=[]; pg.on("console", lambda m: m.type=="error" and errs.append(m.text))
        await pg.goto("http://localhost:8765/index.html"); await pg.wait_for_selector("[data-deep-dive]")
        row = pg.locator("tr", has_text="Vantage At Spring Creek").first
        await row.locator("[data-deep-dive]").click()
        print("url after click:", pg.url)
        fr = pg.frame_locator("#chat-panel-frame")
        ta = fr.locator("#chat-input, textarea, [contenteditable=true]").first
        await ta.wait_for(timeout=45000)
        await pg.wait_for_timeout(4000)
        txt = await ta.inner_text() if await ta.get_attribute("contenteditable") else await ta.input_value()
        print("chat input:", repr(txt))
        await pg.screenshot(path="/tmp/p5-deepdive.png")
        await pg.goto("http://localhost:8765/map.html"); await pg.wait_for_selector("[data-dot]")
        n = await pg.locator("[data-dot]").count(); print("dots", n)
        links=set()
        for i in range(n):
            await pg.locator("[data-dot]").nth(i).dispatch_event("click")
            for h in await pg.locator("#map-card a").evaluate_all("e=>e.map(a=>a.href)"): links.add(h)
        await pg.locator("[data-dot]").first.dispatch_event("click")
        await pg.screenshot(path="/tmp/p5-map.png")
        print("errors", errs)
        await b.close()
    bad=[]
    for u in sorted(links):
        try:
            r=urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0 Chrome/120"}),timeout=20); code=r.status
        except urllib.error.HTTPError as e: code=e.code
        except Exception as e: code=str(e)[:60]
        if code!=200: bad.append((code,u))
    print(len(links),"links,", len(bad),"not 200"); [print(" ",c,u) for c,u in bad]
asyncio.run(main())
