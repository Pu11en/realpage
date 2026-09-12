#!/usr/bin/env python3
"""Generate PropertyStack wireframe images v2 -- two style variants per
frame (top-nav table vs. sidebar), prompts grounded in competitor research
(BuiltWith/Datanyze tech-detection tables, Yardi Matrix/CoStar real-estate
dashboards, Apollo/HubSpot lead-scoring pills). Short labels instead of
full sentences to reduce AI text garbling. Self-contained, stdlib only.
"""
from __future__ import annotations

import json
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
    raise SystemExit("BLOTATO_API_KEY not found")


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
    ("frame-01-early-leads-v2a", (
        "Desktop web app dashboard UI mockup, PropertyStack property-technology "
        "intelligence tool, enterprise SaaS style like Apollo.io and BuiltWith "
        "LeadsEye. Navy blue top nav bar, bold white word PropertyStack on the "
        "left, exactly four short white tab words: Leads, Table, Share, Hood, a "
        "small dropdown and toggle on the right. Below: four white stat cards "
        "with huge bold navy numbers and one short gray label word each. Below: "
        "a thin search bar and three small dropdown filters. Below: a wide "
        "white table, each row has a small colored circle score badge (red, "
        "yellow, or green) with a two-digit number inside, a bold apartment "
        "community name, a city, a unit count, a small colored signal pill with "
        "one short word, a small colored vendor pill with one short vendor "
        "name, and a short two-word gray note. Clean flat UI, generous white "
        "space, no photorealism."
    )),
    ("frame-01-early-leads-v2b", (
        "Desktop web app dashboard UI mockup, PropertyStack property-technology "
        "intelligence tool, real-estate analytics style like Yardi Matrix and "
        "CoStar. A dark navy vertical sidebar on the left with bold white word "
        "PropertyStack at top and four short white menu words stacked "
        "vertically: Leads, Table, Share, Hood. Main area on white background: "
        "a row of four small stat cards with bold navy numbers and short gray "
        "labels. Below: a wide white ranked list, each row has a colored "
        "circle score badge with a two-digit number, a bold apartment "
        "community name, city, unit count, a colored signal pill, a colored "
        "vendor pill, and a short two-word note. Enterprise blue and teal "
        "palette, clean flat UI, generous white space, no photorealism."
    )),
    ("frame-02-master-table-v2a", (
        "Desktop web app dashboard UI mockup, PropertyStack property-technology "
        "intelligence tool, enterprise SaaS style like BuiltWith and Yardi "
        "Matrix. Navy blue top nav bar, bold white word PropertyStack left, "
        "four short white tab words: Leads, Table, Share, Hood, small dropdown "
        "and toggle right. Below: four white stat cards, huge bold navy "
        "numbers, one short gray label word each. Below: search bar and three "
        "small dropdown filters, a small teal Export button top right. Below: "
        "a wide white table with a bold left name column, columns for city, "
        "unit count, year, owner, and a small colored vendor pill per row "
        "(distinct solid color per vendor). Below the table: five small gray "
        "boxes connected by thin teal arrows, each with one bold number, "
        "forming a funnel. Clean flat enterprise UI, generous white space, "
        "no photorealism."
    )),
    ("frame-02-master-table-v2b", (
        "Desktop web app dashboard UI mockup, PropertyStack property-technology "
        "intelligence tool, real-estate analytics style like Yardi Matrix and "
        "CoStar. Dark navy vertical sidebar on left with bold white word "
        "PropertyStack at top, four stacked white menu words: Leads, Table, "
        "Share, Hood, plus small filter checkboxes below the menu. Main area "
        "white background: four small stat cards top, a wide table below with "
        "bold apartment names in the left column, city, units, year, owner, "
        "and a small colored vendor pill per row, small teal Export button top "
        "right. Enterprise blue and teal palette, clean flat UI, no "
        "photorealism."
    )),
    ("frame-03-software-share-v2a", (
        "Desktop web app dashboard UI mockup, PropertyStack property-technology "
        "intelligence tool, enterprise SaaS analytics style. Navy blue top nav "
        "bar, bold white word PropertyStack left, four short white tab words: "
        "Leads, Table, Share, Hood, small dropdown and toggle right. Below: two "
        "white chart cards side by side, left a colorful donut chart titled "
        "Share by properties, right a colorful bar chart titled Share by "
        "units, each chart segment a distinct solid color. Below: a table with "
        "a bold vendor-name left column with a small colored dot matching its "
        "chart color, then columns for property count, unit count, percent, "
        "and a small green or red arrow. Clean flat enterprise UI, generous "
        "white space, no photorealism."
    )),
    ("frame-03-software-share-v2b", (
        "Desktop web app dashboard UI mockup, PropertyStack property-technology "
        "intelligence tool, real-estate analytics style. Dark navy vertical "
        "sidebar on left with bold white word PropertyStack at top and four "
        "stacked white menu words: Leads, Table, Share, Hood. Main area white "
        "background: one large horizontal bar chart titled Market share by "
        "software, bars sorted longest to shortest, each bar a distinct solid "
        "color with a vendor name label on the left and a percent number on "
        "the right. Below: a small donut chart card and a small white table "
        "with vendor rows and colored dots. Enterprise blue and teal palette, "
        "clean flat UI, no photorealism."
    )),
    ("frame-04-property-detail-v2a", (
        "Desktop web app detail page UI mockup for one residential apartment "
        "community (not an office building, not a CRM), PropertyStack "
        "property-technology intelligence tool, enterprise SaaS style. Navy "
        "blue top nav bar with bold white word PropertyStack left, four short "
        "white tab words, small dropdown and toggle right. Below: a large bold "
        "apartment community name as page title, a smaller gray line with "
        "city, unit count, and year built. Below: three white cards side by "
        "side: first card has one colored vendor pill (a property management "
        "software brand) and a small green Confidence High badge; second card "
        "has a small horizontal timeline row of five gray dots with one short "
        "word under each dot (Zoning, Permit, Construction, Leasing, Open); "
        "third card has one huge bold navy score number and three thin colored "
        "bars. Below the cards: a short bulleted list of three source words. "
        "At bottom: a small teal button and a small square gray map with a "
        "teal pin. Clean flat enterprise UI, no photorealism."
    )),
    ("frame-04-property-detail-v2b", (
        "Desktop web app detail page UI mockup for one residential apartment "
        "community (not an office building, not a CRM), PropertyStack "
        "property-technology intelligence tool, real-estate analytics style. "
        "Dark navy vertical sidebar on left with bold white word PropertyStack "
        "at top and four stacked white menu words. Main area white background: "
        "large bold apartment community name at top with city and unit count "
        "below it, then three side by side white cards: one with a colored "
        "vendor pill (property management software brand) and a Confidence "
        "badge, one with a small five-dot horizontal stage timeline, one with "
        "a huge bold score number and three thin colored bars. Below: a small "
        "square gray map with a teal pin and a short bulleted source list. "
        "Enterprise blue and teal palette, clean flat UI, no photorealism."
    )),
    ("frame-05-under-the-hood-v2a", (
        "Desktop web app dashboard UI mockup, PropertyStack property-technology "
        "intelligence tool, enterprise SaaS style. Navy blue top nav bar, bold "
        "white word PropertyStack left, four short white tab words: Leads, "
        "Table, Share, Hood, small dropdown and toggle right. Below: five "
        "connected gray boxes in a row with thin teal arrows between them, "
        "each box has one short two-word label and one bold number underneath. "
        "Below: a small white table with a few rows and columns. Below: two "
        "white cards side by side, left card has a huge bold fraction number "
        "and a small teal upward sparkline line, right card has a small teal "
        "and gray stacked bar chart and a bold dollar number. Below: a muted "
        "gray table labeled Review. Clean flat enterprise UI, generous white "
        "space, no photorealism."
    )),
    ("frame-05-under-the-hood-v2b", (
        "Desktop web app dashboard UI mockup, PropertyStack property-technology "
        "intelligence tool, real-estate analytics style. Dark navy vertical "
        "sidebar on left with bold white word PropertyStack at top and four "
        "stacked white menu words. Main area white background: a horizontal "
        "row of five small connected boxes with teal arrows and short labels "
        "with numbers, below that two side by side cards, one with a big "
        "fraction number and sparkline, one with a small stacked bar chart and "
        "dollar number, below that a small muted gray review table. Enterprise "
        "blue and teal palette, clean flat UI, no photorealism."
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
        "title": "propertystack-wireframes-v2",
    }
    submission = _request("POST", "/v2/videos/from-templates", api_key, body)
    job_id = submission["item"]["id"]
    print("job id:", job_id)
    (OUT_DIR / "submission-v2.json").write_text(json.dumps(submission, indent=2))

    deadline = time.time() + 300
    last = submission["item"]
    while last.get("status") not in TERMINAL_STATUSES and time.time() < deadline:
        time.sleep(5)
        polled = _request("GET", f"/v2/videos/creations/{job_id}", api_key)
        last = polled["item"]
        print("status:", last.get("status"))
    (OUT_DIR / "final-status-v2.json").write_text(json.dumps(last, indent=2))

    credits_after = _request("GET", "/v2/credits", api_key)
    print("credits after:", credits_after["creditsRemaining"])
    print("credits spent:", credits_before["creditsRemaining"] - credits_after["creditsRemaining"])

    if last.get("status") != "done":
        print("NOT DONE:", last.get("error"))
        raise SystemExit(1)

    image_urls = last.get("imageUrls") or []
    print("image urls returned:", len(image_urls))
    for (name, _prompt), url in zip(FRAMES, image_urls):
        ext = Path(url).suffix or ".jpg"
        dest = OUT_DIR / f"{name}{ext}"
        urllib.request.urlretrieve(url, dest)
        print("saved", dest)


if __name__ == "__main__":
    main()
