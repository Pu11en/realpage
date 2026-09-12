"""Quick site check for /gowork (about 30s): every page loads at desktop and phone
size with no script errors, no failed files, and no sideways scrolling on phones.
The full sweep (sweep.py) is still the deep check before going live."""
import asyncio, sys
from playwright.async_api import async_playwright

BASE = sys.argv[1]
PAGES = ["index.html", "master-table.html", "software-share.html", "under-the-hood.html"]
SIZES = {"desktop": (1440, 900), "phone": (390, 844)}

async def main() -> int:
    problems = []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        for size, (w, h) in SIZES.items():
            page = await (await browser.new_context(viewport={"width": w, "height": h})).new_page()
            errs = []
            page.on("pageerror", lambda e: errs.append(f"script error: {str(e)[:150]}"))
            page.on("response", lambda r: r.status >= 400 and errs.append(f"HTTP {r.status}: {r.url[-80:]}"))
            for name in PAGES:
                errs.clear()
                resp = await page.goto(f"{BASE}/{name}", wait_until="networkidle", timeout=30000)
                if resp is None or resp.status >= 400:
                    errs.append(f"page did not load ({resp.status if resp else 'no answer'})")
                if size == "phone" and await page.evaluate(
                    "document.documentElement.scrollWidth > window.innerWidth + 1"
                ):
                    errs.append("scrolls sideways on a phone")
                problems += [f"{name} @ {size}: {e}" for e in errs]
        await browser.close()
    for p in problems:
        print("PROBLEM", p)
    print(f"{len(problems)} problems on {len(PAGES)} pages")
    return 1 if problems else 0

sys.exit(asyncio.run(main()))
