#!/usr/bin/env python3
"""Generate PropertyStack wireframe images with Blotato credits.

Self-contained (stdlib only). Reads BLOTATO_API_KEY from the
blotato-automations repo's .env (read-only -- nothing there is modified)
and calls the "Instagram Carousel Slideshow" template, which is the one
live Blotato template that takes a raw per-slide text prompt with no
required reference image (verified via GET /v2/videos/templates on
2026-09-10). Everything this script produces stays in this folder.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE_URL = "https://backend.blotato.com"
TEMPLATE_ID = "53cfec04-2500-41cf-8cc1-ba670d2c341a"  # Instagram Carousel Slideshow
BLOTATO_ENV = Path("/home/drewp/main-projects/blotato-automations/.env")
OUT_DIR = Path(__file__).resolve().parent / "images"
TERMINAL_STATUSES = {"done", "creation-from-template-failed", "insufficient-credits"}


def load_api_key() -> str:
    for line in BLOTATO_ENV.read_text().splitlines():
        line = line.strip()
        if line.startswith("BLOTATO_API_KEY="):
            return line.partition("=")[2].strip()
    raise SystemExit("BLOTATO_API_KEY not found in blotato-automations/.env")


def _request(method: str, path: str, api_key: str, body: dict | None = None) -> dict:
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode() if body is not None else None
    headers = {"blotato-api-key": api_key, "accept": "application/json"}
    if data is not None:
        headers["content-type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as e:
        raise SystemExit(f"HTTP {e.code}: {e.read().decode(errors='replace')}")
    return json.loads(raw) if raw else {}


FRAMES = [
    ("frame-01-early-leads", (
        "High-fidelity desktop web app dashboard UI mockup named PropertyStack, "
        "clean enterprise SaaS style. Navy blue top nav bar: wordmark left, four "
        "tabs centered (Early Leads bold/active, Master Table, Software Share, "
        "Under the Hood), an Area dropdown and a View As toggle on the right. "
        "Below: a row of four light-gray stat cards with big bold navy numbers "
        "and small labels reading Leads, New this week, Units in play, Opening "
        "next 12 mo. Below that: a filter bar with a search box and four small "
        "dropdowns plus a toggle switch. Below that: a wide ranked table, rows "
        "showing a rank number, a 0-100 score with a thin teal bar, a property "
        "name, city, unit count, a colored signal pill (Upcoming: Permit issued), "
        "a software pill (RealPage, Yardi, or gray Not chosen yet), and a short "
        "one-line note with tiny gray source tags. White background, teal accent "
        "color, bold modern sans-serif headers, lighter sans-serif body text, "
        "generous whitespace, flat UI design, not photorealistic."
    )),
    ("frame-02-master-table", (
        "High-fidelity desktop web app dashboard UI mockup named PropertyStack, "
        "clean enterprise SaaS style. Navy blue top nav bar: wordmark left, four "
        "tabs centered (Master Table bold/active), Area dropdown and View As "
        "toggle right. Below: a row of four light-gray stat cards with big bold "
        "navy numbers and labels reading Apartments, Total units, Software "
        "identified, Top software. Below that: a filter bar with a search box "
        "and dropdowns for city, software, year built, units. Below that: a "
        "wide data table with columns Community, City, Units, Year built, "
        "Owner, a small colored Software pill per row, a small link icon, an "
        "Export CSV button top right. Under the table: a horizontal funnel "
        "strip of five connected boxes with arrows and numbers labeled In area, "
        "Website found, Checked, Identified, Unknown. White background, teal "
        "accent, bold modern sans-serif headers, lighter sans-serif table text, "
        "flat UI design, not photorealistic."
    )),
    ("frame-03-software-share", (
        "High-fidelity desktop web app dashboard UI mockup named PropertyStack, "
        "clean enterprise SaaS style. Navy blue top nav bar: wordmark left, four "
        "tabs centered (Software Share bold/active), Area dropdown and View As "
        "toggle right. Below: two square chart cards side by side on light gray "
        "backgrounds, left one a colorful donut chart titled Share by "
        "properties, right one a colorful bar chart titled Share by units, each "
        "vendor a distinct muted color. Below the charts: a table with columns "
        "Software, Properties, Units, Percent, Change since last run, with "
        "small colored software pills matching the chart colors and small green "
        "or red change arrows. White background, teal accents, bold modern "
        "sans-serif headers, lighter sans-serif table text, flat UI design, "
        "not photorealistic."
    )),
    ("frame-04-property-detail", (
        "High-fidelity desktop web app detail page UI mockup named PropertyStack, "
        "clean enterprise SaaS style. Navy blue top nav bar with wordmark, four "
        "tabs, Area dropdown and View As toggle. Below: a header block with a "
        "large bold property title and a smaller line of address and stats "
        "text. Below that: three light-gray cards side by side: one showing a "
        "software pill, a proof link, and a confidence badge; one showing a "
        "small horizontal stage timeline with dots and date labels; one showing "
        "a large bold navy score number, small teal breakdown bars, and a short "
        "paragraph of body text. Below the cards: a simple bulleted source "
        "list. At the bottom: a button and a small square map placeholder with "
        "a teal pin icon. White background, teal accents, bold modern "
        "sans-serif headers, lighter sans-serif body text, flat UI design, "
        "not photorealistic."
    )),
    ("frame-05-under-the-hood", (
        "High-fidelity desktop web app dashboard UI mockup named PropertyStack, "
        "clean enterprise SaaS style. Navy blue top nav bar: wordmark left, four "
        "tabs centered (Under the Hood bold/active), Area dropdown and View As "
        "toggle right. Below: a horizontal pipeline diagram of five light-gray "
        "rounded boxes connected by teal arrows, each box labeled with a step "
        "name (find apartments, find website, detect software, build table, "
        "leads) and a bold number underneath. Below that: a run history table "
        "with several columns and rows. Below that: two cards side by side, one "
        "showing a large bold fraction like 27 of 30 with a small teal upward "
        "sparkline, one showing a small teal and gray stacked bar with a dollar "
        "amount. At the bottom: a muted gray review queue table. White "
        "background, teal accents, bold modern sans-serif headers, lighter "
        "sans-serif table text, flat UI design, not photorealistic."
    )),
]


def main() -> None:
    api_key = load_api_key()
    OUT_DIR.mkdir(exist_ok=True)

    credits_before = _request("GET", "/v2/credits", api_key)
    print("credits before:", credits_before["creditsRemaining"])

    slide_prompts = [prompt for _name, prompt in FRAMES]
    body = {
        "templateId": TEMPLATE_ID,
        "inputs": {
            "slidePrompts": slide_prompts,
            "model": "nano-banana-2",
            "aspectRatio": "16:9",
        },
        "render": True,
        "title": "propertystack-wireframes-v1",
    }
    submission = _request("POST", "/v2/videos/from-templates", api_key, body)
    job_id = submission["item"]["id"]
    print("job id:", job_id)
    (OUT_DIR / "submission.json").write_text(json.dumps(submission, indent=2))

    deadline = time.time() + 240
    last = submission["item"]
    while last.get("status") not in TERMINAL_STATUSES and time.time() < deadline:
        time.sleep(5)
        polled = _request("GET", f"/v2/videos/creations/{job_id}", api_key)
        last = polled["item"]
        print("status:", last.get("status"))
    (OUT_DIR / "final-status.json").write_text(json.dumps(last, indent=2))

    credits_after = _request("GET", "/v2/credits", api_key)
    print("credits after:", credits_after["creditsRemaining"])
    print("credits spent:", credits_before["creditsRemaining"] - credits_after["creditsRemaining"])

    if last.get("status") != "done":
        print("NOT DONE:", last.get("error"))
        sys.exit(1)

    image_urls = last.get("imageUrls") or []
    print("image urls returned:", len(image_urls))
    for (name, _prompt), url in zip(FRAMES, image_urls):
        ext = Path(url).suffix or ".jpg"
        dest = OUT_DIR / f"{name}{ext}"
        urllib.request.urlretrieve(url, dest)
        print("saved", dest)


if __name__ == "__main__":
    main()
