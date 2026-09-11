import asyncio, json, random, re, sys, urllib.request as u
from playwright.async_api import async_playwright
B = sys.argv[1] if len(sys.argv) > 1 else "https://propertystack-production.up.railway.app"
CHAT = "--chat" in sys.argv
OUT = "/tmp/qa"
PAGES = ["index.html", "master-table.html", "software-share.html", "under-the-hood.html"]
WIDTHS = {"desktop": (1440, 900), "tablet": (820, 1180), "phone": (390, 844)}
bugs = []
def bug(page, width, steps, what, shot=""):
    key = (page, width, what[:120])
    if key not in {(b["page"], b["width"], b["what"][:120]) for b in bugs}:
        bugs.append(dict(page=page, width=width, steps=steps, what=what, shot=shot))

CHECK_JS = r"""() => {
  const out = {hscroll: document.documentElement.scrollWidth > window.innerWidth + 1, sw: document.documentElement.scrollWidth, bad: [], clipped: [], offscreen: []};
  const txt = document.body.innerText;
  for (const m of txt.matchAll(/.{0,40}(\bNaN\b|\bundefined\b|\bnull\b|\[object Object\]|Infinity).{0,40}/g)) out.bad.push(m[0].replace(/\n/g,' '));
  const vw = window.innerWidth;
  for (const el of document.querySelectorAll('body *')) {
    if (!el.offsetParent && getComputedStyle(el).position !== 'fixed') continue;
    let sc = false; for (let a = el.parentElement; a; a = a.parentElement) { const o = getComputedStyle(a).overflowX; if (o === 'auto' || o === 'scroll') { sc = true; break; } }
    if (sc) continue;
    const cs = getComputedStyle(el), r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    const hasText = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    if (hasText && (cs.overflow === 'hidden' || cs.overflowX === 'hidden' || cs.textOverflow === 'ellipsis') && el.scrollWidth > el.clientWidth + 1)
      out.clipped.push(el.tagName + '.' + el.className + ': ' + el.innerText.slice(0, 50));
    if (hasText && r.right > vw + 1 && cs.position !== 'fixed' && !el.closest('[style*="overflow"]'))
      out.offscreen.push(el.tagName + '.' + el.className + ' right=' + Math.round(r.right) + ': ' + el.innerText.slice(0, 50));
  }
  out.clipped = out.clipped.slice(0, 8); out.offscreen = out.offscreen.slice(0, 8); out.bad = [...new Set(out.bad)].slice(0, 8);
  return out;
}"""

async def main():
    data = json.load(u.urlopen(B + "/data/properties.json"))
    ids = [p["id"] for p in data["properties"]] + [p["id"] for p in data.get("upcoming", [])]
    async with async_playwright() as pw:
        br = await pw.chromium.launch()
        async def newpage(w, h, label):
            ctx = await br.new_context(viewport={"width": w, "height": h}, accept_downloads=True)
            pg = await ctx.new_page()
            pg._qa = {"errs": []}
            pg.on("pageerror", lambda e: pg._qa["errs"].append("pageerror: " + str(e)[:200]))
            pg.on("console", lambda m: m.type == "error" and pg._qa["errs"].append("console: " + m.text[:200]))
            pg.on("requestfailed", lambda r: pg._qa["errs"].append(f"requestfailed: {r.url[:120]} {r.failure}"))
            pg.on("response", lambda r: r.status >= 400 and pg._qa["errs"].append(f"HTTP {r.status}: {r.url[:120]}"))
            return pg
        async def check(pg, page, width, steps, shot=None):
            await pg.wait_for_timeout(250)
            c = await pg.evaluate(CHECK_JS)
            if shot: await pg.screenshot(path=f"{OUT}/{shot}.png", full_page=False)
            s = f"{shot}.png" if shot else ""
            if c["hscroll"] and width == "phone": bug(page, width, steps, f"horizontal scroll on phone (scrollWidth {c['sw']})", s)
            for b in c["bad"]: bug(page, width, steps, f"bad value in text: '{b}'", s)
            for b in c["clipped"]: bug(page, width, steps, f"clipped text: {b}", s)
            if width != "desktop":
                for b in c["offscreen"]: bug(page, width, steps, f"text past right edge: {b}", s)
            for e in pg._qa["errs"]: bug(page, width, steps, e, s)
            pg._qa["errs"].clear()

        async def go(pg, url, wait_until="networkidle"):
            for attempt in range(3):
                try:
                    await pg.wait_for_timeout(100)
                    return await pg.goto(url, wait_until=wait_until)
                except Exception as e:
                    if attempt == 2: bug(url.split("/")[-1].split("?")[0], "?", f"goto {url}", f"navigation failed: {str(e)[:80]}")
        links = set()
        for wname, (w, h) in WIDTHS.items():
            pg = await newpage(w, h, wname)
            for page in PAGES:
                tag = f"{wname}-{page.split('.')[0]}"
                await go(pg, f"{B}/{page}", "networkidle")
                await pg.screenshot(path=f"{OUT}/{tag}-full.png", full_page=True)
                await check(pg, page, wname, "load page", tag)
                for a in await pg.locator("a[href]").all():
                    links.add((page, await a.get_attribute("href")))
                # every select option
                for sel in await pg.locator("select").all():
                    sid = await sel.get_attribute("id") or "?"
                    if not await sel.is_visible(): continue
                    opts = await sel.locator("option").evaluate_all("os => os.map(o => o.value)")
                    for v in opts:
                        await sel.select_option(v)
                        await pg.wait_for_timeout(150)
                        if pg.url.split("/")[-1].split("?")[0] != page:
                            await go(pg, f"{B}/{page}", "networkidle")
                            sel = pg.locator(f"#{sid}")
                        await check(pg, page, wname, f"select #{sid} = {v!r}")
                    if opts: await pg.locator(f"#{sid}").select_option(opts[0])
                    if sid == "view-as-select":
                        await pg.evaluate("localStorage.clear()")
                        await go(pg, f"{B}/{page}", "networkidle")
                # checkboxes
                for cb in await pg.locator("input[type=checkbox]").all():
                    if await cb.is_visible():
                        await cb.click(); await check(pg, page, wname, "toggle checkbox"); await cb.click()
                # search
                if await pg.locator("#f-search").count():
                    for q in ["Legacy", "zzzznotfound", ""]:
                        await pg.fill("#f-search", q); await check(pg, page, wname, f"search {q!r}", f"{tag}-search-{q or 'clear'}" if q == "zzzznotfound" else None)
                # export
                if await pg.locator("#export-csv").count():
                    async with pg.expect_download() as dl:
                        await pg.click("#export-csv")
                    d = await dl.value; path = await d.path(); txt = open(path, encoding="utf-8").read()
                    n = txt.count("\n")
                    if n < 200 or "undefined" in txt or "NaN" in txt: bug(page, wname, "click Export CSV", f"CSV looks wrong: {n} lines")
                # sortable headers
                for th in await pg.locator("th").all():
                    if await th.is_visible() and (await th.evaluate("e => getComputedStyle(e).cursor")) == "pointer":
                        await th.click(); await check(pg, page, wname, f"click header {await th.inner_text()}")
                # every visible non-chat button
                for i, btn in enumerate(await pg.locator("button:visible").all()):
                    bid = await btn.get_attribute("id") or ""
                    cls = await btn.get_attribute("class") or ""
                    if "chat" in bid or "chat" in cls or bid == "export-csv": continue
                    before = await pg.evaluate("document.body.innerHTML.length + location.href")
                    await btn.click(); await pg.wait_for_timeout(300)
                    after = await pg.evaluate("document.body.innerHTML.length + location.href")
                    if before == after: bug(page, wname, f"click button '{(await btn.inner_text())[:30]}'", "button click did nothing visible")
                    await go(pg, f"{B}/{page}", "networkidle")
                # clickable rows: first, middle, last
                rows = pg.locator("tbody tr")
                n = await rows.count()
                for idx in sorted({0, n // 2, n - 1}) if n else []:
                    r = rows.nth(idx)
                    clickable = await r.evaluate("e => getComputedStyle(e).cursor === 'pointer' || e.classList.contains('clickable') || !!e.dataset.vendor")
                    if not clickable: continue
                    await r.click(); await pg.wait_for_load_state("networkidle")
                    t = await pg.locator("#page-content").inner_text()
                    if pg.url.split("?")[0].endswith(page): bug(page, wname, f"click row {idx}", "clickable row did not navigate")
                    elif "property not found" in t.lower(): bug(page, wname, f"click row {idx}", f"row goes to not-found page {pg.url}")
                    await check(pg, page, wname, f"click row {idx} -> {pg.url.split('/')[-1]}")
                    await go(pg, f"{B}/{page}", "networkidle")
            # nav links on each width
            for key in ["index.html", "master-table.html", "software-share.html", "under-the-hood.html"]:
                await go(pg, f"{B}/index.html", "networkidle")
                await pg.locator(f".sidebar nav a[href='{key}']").click(); await pg.wait_for_load_state("networkidle")
                if not pg.url.endswith(key): bug("nav", wname, f"click nav {key}", f"went to {pg.url}")
            # 5 random property pages incl. upcoming
            rnd = random.Random(7)
            sample = rnd.sample([p["id"] for p in data["properties"]], 3) + rnd.sample([p["id"] for p in data.get("upcoming", [])], 2)
            for k, pid in enumerate(sample):
                await go(pg, f"{B}/property.html?id={pid}", "networkidle")
                shot = f"{wname}-property-{k}"
                await pg.screenshot(path=f"{OUT}/{shot}-full.png", full_page=True)
                await check(pg, "property.html", wname, f"open property.html?id={pid}", shot)
                for a in await pg.locator("a[href]").all(): links.add(("property.html", await a.get_attribute("href")))
                # back link
                back = pg.locator("a:has-text('Back')")
                if await back.count():
                    await back.first.click(); await pg.wait_for_load_state("networkidle")
                    if "property.html" in pg.url: bug("property.html", wname, "click Back", "Back link did not leave page")
            if wname == "phone" and CHAT or wname == "phone":
                await go(pg, f"{B}/master-table.html", "networkidle")
                if not await pg.locator("#chat-fab").is_visible(): bug("master-table.html", wname, "load", "Ask button missing on phone")
                else:
                    await pg.click("#chat-fab"); await pg.screenshot(path=f"{OUT}/phone-chat-open.png")
                    await check(pg, "master-table.html", wname, "tap Ask button", "phone-chat-open")
                    await pg.click("#chat-close")
                    if await pg.locator("#chat-panel").is_visible(): bug("master-table.html", wname, "tap close", "chat did not close")
            await pg.context.close()

        # all property ids resolve, desktop
        pg = await newpage(1440, 900, "desktop")
        for pid in ids:
            await go(pg, f"{B}/property.html?id={pid}", "domcontentloaded")
            await pg.wait_for_selector("#page-content h1, #page-content h2", timeout=10000)
            t = await pg.locator("#page-content").inner_text()
            if "property not found" in t.lower(): bug("property.html", "desktop", f"open id={pid}", "property page says not found")
            await check(pg, "property.html", "desktop", f"open property.html?id={pid}")

        # links
        seen = set()
        for page, href in links:
            if not href or href.startswith(("#", "mailto:", "tel:", "javascript")) or href in seen: continue
            seen.add(href)
            url = href if href.startswith("http") else f"{B}/{href.lstrip('/')}"
            try:
                req = u.Request(url, method="GET", headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/126"})
                code = u.urlopen(req, timeout=15).status
            except Exception as e:
                code = getattr(e, "code", str(e)[:60])
            if not (isinstance(code, int) and 200 <= code < 400) and "CERTIFICATE_VERIFY_FAILED" not in str(code) and not (isinstance(code, int) and code in (401, 403, 405, 429) and href.startswith("http")):
                bug(page, "all", f"link {href}", f"link returns {code}")

        if CHAT:
            pg = await newpage(1440, 900, "desktop")
            await go(pg, f"{B}/master-table.html", "networkidle")
            for i, q in enumerate(["Which buildings in Richardson use RealPage?", "which of those are biggest?", "and what year was the biggest one built?"]):
                await pg.fill("#chat-input", q); await pg.press("#chat-input", "Enter")
                await pg.wait_for_function(f"document.querySelectorAll('.msg.bot,.msg.error').length > {i}", timeout=150000)
                a = await pg.locator(".msg.bot,.msg.error").last.inner_text()
                print(f"CHAT A{i+1}:", a[:300].replace("\n", " | "))
                if "error" in (await pg.locator(".msg.bot,.msg.error").last.get_attribute("class")): bug("master-table.html", "desktop", f"chat: {q}", "chat returned error: " + a[:100])
            await pg.screenshot(path=f"{OUT}/desktop-chat-3turn.png")
            await check(pg, "master-table.html", "desktop", "3-turn chat", "desktop-chat-3turn")
        await br.close()
    json.dump(bugs, open(f"{OUT}/bugs.json", "w"), indent=1)
    print(len(bugs), "bugs")
    for b in bugs: print(f"- [{b['page']} @ {b['width']}] {b['what']}  (steps: {b['steps']})")
asyncio.run(main())
