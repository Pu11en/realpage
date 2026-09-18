"""Check for the US lead map + "Deep dive in chat" button.

Serves site/ itself on port 8791 (override with CHECK_MAP_PORT), runs Playwright
against it, then stops the server. Free, offline, under 60 s. Exits non-zero on
any problem.

Contract the site must meet:
- map.html: 0 console/script errors, states shaded from data/lead-map.json
  (`[data-count]` on every state in that file); pointing at the top state shows
  `#map-tip` with its count and top cities; no `[data-dot]` dots, no `#map-card`.
- nav has a "Map" tab and no "Master Table" tab.
- master-table.html redirects to map.html.
- every Early Leads row (#leads-tbody tr) has a `[data-deep-dive]` button.
- property.html?id=<first lead with a building page> has a `[data-deep-dive]` button.
"""
import asyncio, json, os, subprocess, sys, time, urllib.request
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[2]
PORT = int(os.environ.get("CHECK_MAP_PORT", "8791"))
BASE = f"http://localhost:{PORT}"


def wait_up() -> bool:
    for _ in range(40):
        try:
            with urllib.request.urlopen(f"{BASE}/index.html", timeout=2) as r:
                if b"PropertyStack" in r.read():
                    return True
        except Exception:
            pass
        time.sleep(0.25)
    return False


async def run() -> list[str]:
    problems: list[str] = []
    leads = json.loads((ROOT / "site/data/leads.json").read_text())["leads"]
    first_id = next((l["propertyId"] for l in leads if l.get("propertyId")), None)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        page = await (await browser.new_context(viewport={"width": 1440, "height": 900})).new_page()
        errs: list[str] = []
        page.on("pageerror", lambda e: errs.append(f"script error: {str(e)[:150]}"))
        page.on("console", lambda m: m.type == "error" and errs.append(f"console: {m.text[:150]}"))

        # 1. Map page loads, states shaded by count, hover shows count + top cities, no dots/cards.
        cmap = json.loads((ROOT / "site/data/lead-map.json").read_text())["states"]
        resp = await page.goto(f"{BASE}/map.html", wait_until="networkidle", timeout=20000)
        if resp is None or resp.status >= 400:
            problems.append(f"map.html did not load ({resp.status if resp else 'no answer'})")
        else:
            try:
                await page.wait_for_selector(".state[data-count]", timeout=8000)
            except Exception:
                pass
            shaded = await page.locator(".state[data-count]").count()
            if shaded != len(cmap):
                problems.append(f"map.html: {shaded} shaded states, lead-map.json has {len(cmap)}")
            if await page.locator("[data-dot]").count():
                problems.append("map.html: building dots still drawn")
            if await page.locator("#map-card").count():
                problems.append("map.html: proof card still present")
            top_name, top = max(cmap.items(), key=lambda kv: kv[1]["total"])
            st = page.locator(f'.state[data-state="{top_name}"]')
            if await st.count():
                await st.hover()
                tip = await page.locator("#map-tip").inner_text() if await page.locator("#map-tip:visible").count() else ""
                if str(top["total"]) not in tip or top["topCities"][0]["city"] not in tip:
                    problems.append(f"map.html: pointing at {top_name} does not show its count and top cities")
            else:
                problems.append(f"map.html: no state path for {top_name}")
            problems += [f"map.html: {e}" for e in errs]

            # 2. Nav: Map yes, Master Table no.
            nav = await page.locator("nav").inner_text() if await page.locator("nav").count() else ""
            if "Map" not in nav:
                problems.append("nav has no 'Map' tab")
            if "Master Table" in nav:
                problems.append("nav still has a 'Master Table' tab")

        # 3. master-table.html redirects to map.html.
        try:
            await page.goto(f"{BASE}/master-table.html", timeout=15000)
            await page.wait_for_url("**/map.html**", timeout=5000)
        except Exception:
            problems.append(f"master-table.html does not redirect to map.html (ended at {page.url})")

        # 4. Every Early Leads row has a deep-dive button.
        await page.goto(f"{BASE}/index.html", wait_until="networkidle", timeout=20000)
        try:
            await page.wait_for_selector("#leads-tbody tr", timeout=8000)
        except Exception:
            pass
        rows = await page.locator("#leads-tbody tr").count()
        with_btn = await page.locator("#leads-tbody tr:has([data-deep-dive])").count()
        if rows == 0:
            problems.append("Early Leads: no rows found")
        elif with_btn != rows:
            problems.append(f"Early Leads: {rows - with_btn} of {rows} rows have no [data-deep-dive] button")

        # 5. A building page has a deep-dive button.
        if not first_id:
            problems.append("no lead with a propertyId to test property.html")
        else:
            await page.goto(f"{BASE}/property.html?id={first_id}", wait_until="networkidle", timeout=20000)
            try:
                await page.wait_for_selector("[data-deep-dive]", timeout=5000)
            except Exception:
                problems.append(f"property.html?id={first_id}: no [data-deep-dive] button")

        await browser.close()
    return problems


def main() -> int:
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORT), "-d", str(ROOT / "site")],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        if not wait_up():
            print(f"PROBLEM site server never came up on port {PORT} (port busy?)")
            return 1
        problems = asyncio.run(run())
    finally:
        server.terminate()
        server.wait(timeout=5)
    for p in problems:
        print("PROBLEM", p)
    print(f"check_map: {len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
