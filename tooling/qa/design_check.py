"""Design check for PLAN-app-redesign (about 20s). Every page listed in
tooling/qa/design-pages.txt must use the landing-page look: Plus Jakarta Sans
headings, Inter body text, a light page background, and no leftover dark-theme
greens. Pages are added to that list by the task that restyles them, so the
check grows with the build and passes at every step."""
import asyncio, pathlib, sys
from playwright.async_api import async_playwright

BASE = sys.argv[1]
LIST = pathlib.Path(__file__).with_name("design-pages.txt")
PAGES = [l.strip() for l in LIST.read_text().splitlines() if l.strip() and not l.startswith("#")] if LIST.exists() else []

PROBE = """() => {
  const fam = el => el ? getComputedStyle(el).fontFamily : '';
  const lum = c => { const m = c.match(/[\\d.]+/g); if (!m) return 1;
    const [r,g,b,a] = m.map(Number); if (a === 0) return 1; return (0.2126*r + 0.7152*g + 0.0722*b) / 255; };
  const main = document.querySelector('main, .main, #page-content') || document.body;
  let bg = getComputedStyle(main).backgroundColor, el = main;
  while (el && /rgba\\(0, 0, 0, 0\\)|transparent/.test(bg)) { el = el.parentElement; bg = el ? getComputedStyle(el).backgroundColor : 'rgb(255,255,255)'; }
  const heading = document.querySelector('h1, h2, .wordmark');
  const fontsReady = [...document.fonts].filter(f => f.status === 'loaded').map(f => f.family.replace(/"/g, ''));
  const html = document.documentElement.outerHTML;
  return { body: fam(document.body), heading: fam(heading), hasHeading: !!heading,
           bgLum: lum(bg), fontsReady, oldGreen: /#22c55e|34, ?197, ?94/i.test(html) };
}"""

async def main() -> int:
    if not PAGES:
        print("design check: no restyled pages listed yet (ok)"); return 0
    problems = []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        page = await (await browser.new_context(viewport={"width": 1440, "height": 900})).new_page()
        for name in PAGES:
            await page.goto(f"{BASE}/{name}", wait_until="networkidle")
            await page.evaluate("document.fonts.ready")
            r = await page.evaluate(PROBE)
            if "Inter" not in r["body"]: problems.append(f"{name}: body font is {r['body']!r}, want Inter")
            if r["hasHeading"] and "Plus Jakarta Sans" not in r["heading"]:
                problems.append(f"{name}: heading font is {r['heading']!r}, want Plus Jakarta Sans")
            for fam in ("Inter", "Plus Jakarta Sans"):
                if fam not in r["fontsReady"]: problems.append(f"{name}: font file for {fam} did not load")
            if r["bgLum"] < 0.8: problems.append(f"{name}: page background is dark (brightness {r['bgLum']:.2f})")
            if r["oldGreen"]: problems.append(f"{name}: still uses the old dark-theme green #22c55e")
        await browser.close()
    for p in problems: print("DESIGN:", p)
    print(f"design check: {len(PAGES)} page(s), {len(problems)} problem(s)")
    return 1 if problems else 0

sys.exit(asyncio.run(main()))
