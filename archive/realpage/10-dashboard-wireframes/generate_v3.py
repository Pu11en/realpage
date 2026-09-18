#!/usr/bin/env python3
"""Generate PropertyStack wireframe images v3 -- techie/dev-tool dark style,
grounded in shadcn/ui's dashboard-01 block (sidebar layout, border-based
cards not shadows) and Vercel's Geist design system (monochrome-first, no
gradients/glass, restrained single accent color). Self-contained, stdlib.
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
    ("frame-01-early-leads-v3", (
        "Desktop web app dashboard UI mockup in a techie developer-tool style "
        "like shadcn/ui, Linear, and Vercel dashboards. Near-black dark zinc "
        "background. A slim dark left sidebar with a small white wordmark "
        "PropertyStack at top and four short menu words stacked: Leads, "
        "Table, Share, Hood, one highlighted with a thin green left-border "
        "accent. Main area: four small stat cards with thin 1px gray borders, "
        "no shadows, no gradients, bold white numbers, small gray labels "
        "below, monospace-style numbers. Below: a thin search input and small "
        "dropdown filters, all with 1px borders. Below: a dense data table on "
        "the dark background, thin row dividers, a small colored circle score "
        "badge per row (green, yellow, or red) with a two-digit number, bold "
        "white apartment name, gray city and unit text, a small pill-shaped "
        "signal tag, a small pill-shaped software tag, a short gray note. High "
        "information density, flat, minimal chrome, Inter font, no "
        "photorealism."
    )),
    ("frame-02-master-table-v3", (
        "Desktop web app dashboard UI mockup in a techie developer-tool style "
        "like shadcn/ui, Linear, and Vercel dashboards. Near-black dark zinc "
        "background, slim dark left sidebar with small white wordmark "
        "PropertyStack and four stacked menu words, one highlighted with a "
        "thin green accent bar. Main area: four small stat cards with thin "
        "1px borders, bold white numbers, gray labels, no shadows. Below: a "
        "thin search input, small dropdown filters, and a small outlined "
        "Export button, all 1px bordered. Below: a dense dark data table with "
        "thin row dividers, bold white community names in the left column, "
        "gray city, units, year, owner columns, a small colored pill software "
        "tag per row. Below the table: five small thin-bordered boxes "
        "connected by thin gray lines forming a funnel, each with a bold "
        "white number. High density, flat, minimal chrome, Inter font, no "
        "photorealism."
    )),
    ("frame-03-software-share-v3", (
        "Desktop web app dashboard UI mockup in a techie developer-tool style "
        "like shadcn/ui and Linear. Near-black dark zinc background, slim "
        "dark left sidebar with small white wordmark PropertyStack and four "
        "stacked menu words, one highlighted with a thin green accent bar. "
        "Main area: two thin 1px-bordered chart cards side by side on the "
        "dark background, left a simple donut chart with a few muted accent "
        "colors, right a simple bar chart with matching muted colors, small "
        "white titles above each, no shadows. Below: a thin-bordered dark "
        "table with a bold white vendor name column, a small colored dot per "
        "row matching chart colors, gray columns for property count, unit "
        "count, percent, and a small green or red arrow. High density, flat, "
        "minimal chrome, no gradients, Inter font, no photorealism."
    )),
    ("frame-04-property-detail-v3", (
        "Desktop web app detail page UI mockup for one residential apartment "
        "community (not an office building, not a CRM), techie developer-tool "
        "style like shadcn/ui and Linear, near-black dark zinc background. "
        "Slim dark left sidebar with small white wordmark PropertyStack and "
        "four stacked menu words. Main area: a large bold white apartment "
        "community name at top, a smaller gray line with city, unit count, "
        "year built. Below: three thin 1px-bordered dark cards side by side: "
        "one with a small colored pill naming a property management software "
        "brand and a small green Confidence High tag; one with a small "
        "horizontal five-dot timeline with short gray words under each dot "
        "(Zoning, Permit, Construction, Leasing, Open); one with a large bold "
        "white score number and three thin colored progress bars. Below: a "
        "short bulleted list in gray text. At bottom: a small outlined button "
        "and a small dark square map with a green pin. High density, flat, "
        "minimal chrome, no shadows, Inter font, no photorealism."
    )),
    ("frame-05-under-the-hood-v3", (
        "Desktop web app dashboard UI mockup in a techie developer-tool style "
        "like shadcn/ui and Linear, near-black dark zinc background. Slim "
        "dark left sidebar with small white wordmark PropertyStack and four "
        "stacked menu words, one highlighted with a thin green accent bar. "
        "Main area: five small thin-bordered dark boxes in a row connected by "
        "thin gray lines, each with a short gray label and a bold white "
        "number. Below: a thin-bordered dark table with a few rows. Below: "
        "two thin-bordered dark cards side by side, one with a large bold "
        "white fraction number and a small green sparkline line, one with a "
        "small muted bar chart and a bold white dollar amount. Below: a "
        "dim gray-text table labeled Review, slightly faded to read as "
        "reference only. High density, flat, minimal chrome, no shadows, "
        "Inter font, no photorealism."
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
        "title": "propertystack-wireframes-v3-techie",
    }
    submission = _request("POST", "/v2/videos/from-templates", api_key, body)
    job_id = submission["item"]["id"]
    print("job id:", job_id)
    (OUT_DIR / "submission-v3.json").write_text(json.dumps(submission, indent=2))

    deadline = time.time() + 300
    last = submission["item"]
    while last.get("status") not in TERMINAL_STATUSES and time.time() < deadline:
        time.sleep(5)
        polled = _request("GET", f"/v2/videos/creations/{job_id}", api_key)
        last = polled["item"]
        print("status:", last.get("status"))
    (OUT_DIR / "final-status-v3.json").write_text(json.dumps(last, indent=2))

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
