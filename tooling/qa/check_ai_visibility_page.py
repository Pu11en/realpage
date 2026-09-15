"""Page check for the AI Visibility tab (PLAN-ai-visibility-v2 T5). Offline, no Gemini, no key.

Copies site/ to a temp folder, adds practice Gemini runs to its history (built from the saved
fixtures, word-list tone), serves it on a spare port (CHECK_AIVIS_PORT, default 8794) and loads
the page at desktop and phone size with Playwright. Checked twice: with two Gemini runs (trend
lines + lawsuit sections) and with one ("one run so far"). The real site/ is never touched.
"""
import asyncio, copy, json, os, shutil, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "tooling/ai-visibility/fixtures"
sys.path[:0] = [str(ROOT / "site/data"), str(ROOT / "tooling/ai-visibility")]
import ai_visibility_lawsuit as law  # noqa: E402
import build_ai_visibility as bav  # noqa: E402

PORT = int(os.environ.get("CHECK_AIVIS_PORT", "8794"))
BASE = f"http://localhost:{PORT}"


def add_practice_runs(hist: Path, dates: list[str]) -> None:
    report = json.loads((FIX / "report-gemini.json").read_text())
    run = FIX / "lawsuit-run"
    lawsuit_report = json.loads((run / "report.json").read_text())
    for i, date in enumerate(dates):
        r = copy.deepcopy(report)
        r["generatedAt"] = f"{date}T12:00:00.000Z"
        data = bav.build(r, demo=False)
        for m in data["models"]:  # make the second run differ so lines slope
            m["mentionPct"] = max(0, (m["mentionPct"] or 0) - 10 * i)
        names = {m["model"]: m["name"] for m in data["models"]}
        found = law.lawsuit_data(lawsuit_report, run, None, bav.previous_entry(date, hist), names)
        bav.save_history(bav.history_entry(data, lawsuit_data=found), hist)


async def check_page(pw, problems: list[str], tag: str, runs: int) -> None:
    browser = await pw.chromium.launch()
    for vw, vh, size in ((1440, 900, "desktop"), (390, 844, "phone")):
        page = await (await browser.new_context(viewport={"width": vw, "height": vh})).new_page()
        errs: list[str] = []
        page.on("pageerror", lambda e: errs.append(f"script error: {str(e)[:150]}"))
        page.on("console", lambda m: m.type == "error" and errs.append(f"console: {m.text[:150]}"))
        await page.goto(f"{BASE}/ai-visibility.html", wait_until="networkidle", timeout=20000)
        where = f"[{tag}, {size}]"
        try:
            await page.wait_for_selector("#last-run", timeout=8000)
        except Exception:
            problems.append(f"{where} no 'last run' line"); await page.close(); continue
        last = await page.inner_text("#last-run")
        if "Last run" not in last or "Gemini" not in last:
            problems.append(f"{where} last-run line reads: {last!r}")
        for key in ("mentionPct", "topPickPct", "lawsuitPct"):
            if await page.locator(f'[data-trend="{key}"] circle').count() < 2:
                problems.append(f"{where} trend chart {key} has too few points")
        if await page.locator('[data-trend="mentionPct"] polyline').count() != (2 if runs > 1 else 0):
            problems.append(f"{where} wrong number of Gemini lines in the mentioned chart")
        legend = await page.inner_text('[data-trend="mentionPct"] .legend')
        if "Sept 12 baseline" not in legend or "Gemini + Google Search" not in legend:
            problems.append(f"{where} legend missing baseline or Gemini: {legend!r}")
        if (await page.locator("#one-run").count() == 1) != (runs == 1):
            problems.append(f"{where} 'one run so far' shown wrongly")
        if await page.locator("#lawsuit-sources .src-row.us").count() != 1:
            problems.append(f"{where} realpage.com not highlighted in the source list")
        if await page.locator("#lawsuit-tone .tone-bar span").count() < 1:
            problems.append(f"{where} tone bar empty")
        quotes = page.locator("#lawsuit-quotes .quote")
        if await quotes.count() < 3 or await page.locator("#lawsuit-quotes a[href]").count() < 1:
            problems.append(f"{where} quote wall missing quotes or links")
        if runs > 1 and "▲" not in await page.inner_text("#lawsuit-sources") and "same" not in await page.inner_text("#lawsuit-sources"):
            problems.append(f"{where} no change vs last run in the source list")
        if await page.locator("text=What to do next").count() < 1:
            problems.append(f"{where} to-do list is gone")
        wide = await page.evaluate("document.documentElement.scrollWidth - window.innerWidth")
        if size == "phone" and wide > 40:
            problems.append(f"{where} page is {wide}px wider than the phone screen")
        problems.extend(f"{where} {e}" for e in errs)
        await page.close()
    await browser.close()


def serve(site: Path):
    proc = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT), "-d", str(site)],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(40):
        try:
            urllib.request.urlopen(f"{BASE}/ai-visibility.html", timeout=2)
            return proc
        except Exception:
            time.sleep(0.25)
    proc.kill()
    sys.exit(f"site did not start on port {PORT}")


def main() -> None:
    problems: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        for tag, dates in (("one Gemini run", ["2026-09-20"]), ("two Gemini runs", ["2026-09-20", "2026-09-27"])):
            site = Path(tmp) / tag.replace(" ", "-")
            shutil.copytree(ROOT / "site", site)
            add_practice_runs(site / "data/ai-visibility-history", dates)
            proc = serve(site)
            try:
                asyncio.run(async_playwright_run(problems, tag, len(dates)))
            finally:
                proc.terminate(); proc.wait()
    if problems:
        print("AI Visibility page check FAILED:"); print("\n".join(f"- {p}" for p in problems)); sys.exit(1)
    print("AI Visibility page check passed (trends, lawsuit sources, tone, quotes; desktop + phone)")


async def async_playwright_run(problems, tag, runs):
    async with async_playwright() as pw:
        await check_page(pw, problems, tag, runs)


if __name__ == "__main__":
    main()
