#!/usr/bin/env python3
"""Generate the static, crawlable pages under site/leads/.

Why these exist: every page the site serves today is a JavaScript shell, so a search
engine or an AI crawler that does not run scripts sees a title and nothing else. These
pages are plain HTML with the buildings written into them, so the data is readable
without JavaScript.

Why there are ~25 of them and not 1,861: Google's March 2026 core update demotes sites
for mass-produced thin pages, and the demotion is sitewide rather than per page. The
buildings are unique data, but one page per building would still be thin. See
docs/plans/PLAN-seo-geo-strategy.md for the search-demand evidence behind the page set.

Reads the built JSON in site/data/, writes HTML. It deliberately does not live inside
site/data/build_data.py: that script owns the data, this one owns presentation, and it
copies none of its logic.

    python3 tooling/seo/build_pages.py            # write the pages
    python3 tooling/seo/build_pages.py --check    # exit 1 if any page is out of date
"""

from __future__ import annotations

import argparse
import csv
import html
import io
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "site"
DATA = SITE / "data"
OUT = SITE / "leads"
HOST = "https://app.cranesignal.com"
LANDING = "https://cranesignal.com"
# The brand's single identity, declared on the landing page (live 2026-09-25).
# Every page references it rather than declaring its own, so the two hosts are
# one entity to a model rather than two that happen to share a name.
ORG_ID = f"{LANDING}/#org"

# A city needs this many buildings before it gets its own page. Below it the page would
# be thin, which is the thing that carries sitewide risk.
CITY_MIN = 25

STAGE_ORDER = ["under construction", "permitted", "planned", "leasing", "sold"]

# The widest pages would otherwise run to half a megabyte of HTML, which is slow on a
# phone and no more useful than the narrower pages it links to. Rows are sorted largest
# first, so a cap keeps the most notable buildings and the page says plainly what it cut.
ROW_CAP = 400

# City values in the source records are messy: casing varies, some carry a county in
# brackets, and a few are counties rather than cities. Counties are kept in the data
# (they are real buildings) but never get their own page, because "apartments in
# Tarrant County" is not a thing anyone searches and the label would read as an error.
NOT_A_CITY = re.compile(r"\b(county|co\.?)\s*$", re.I)


def slugify(value: str) -> str:
    value = value.lower().replace("–", "-").replace("—", "-")
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def clean_city(raw: str | None) -> str | None:
    """'GARLAND (DALLAS CO)' -> 'Garland'. Returns None for a non-city."""
    if not raw:
        return None
    name = re.sub(r"\s*\(.*?\)\s*", " ", raw).strip()
    if not name or NOT_A_CITY.search(name):
        return None
    # Title-case only the shouted ones; leave mixed case (e.g. "Fort Worth") alone.
    if name.isupper():
        name = name.title()
    return re.sub(r"\s+", " ", name)


def esc(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


# County and permit records arrive SHOUTED. Title-casing them reads better and matches how
# people write these names, but a naive .title() turns "LLC" into "Llc", so the tokens that
# are genuinely acronyms are put back. Mixed-case values are left exactly as they are: if a
# record already has real casing, it is better than anything we would infer.
KEEP_UPPER = {
    "LLC", "L.L.C.", "LP", "L.P.", "LLP", "LTD", "INC", "PLLC", "PC", "PA",
    "USA", "US", "TX", "AZ", "NM", "NY", "HOA", "GP", "REIT", "DBA", "TIC",
    "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
    "NE", "NW", "SE", "SW", "JR", "SR", "MLK", "FM", "IH", "SH", "US-",
}


def pretty(value: str | None) -> str:
    """'PECOS HOUSING FINANCE CORP' -> 'Pecos Housing Finance Corp'."""
    if not value:
        return ""
    text = str(value).strip()
    if not text or not text.isupper():
        return text
    words = []
    for word in text.split():
        bare = word.strip(".,()")
        if bare in KEEP_UPPER:
            words.append(word)
        elif re.fullmatch(r"[0-9]+(ST|ND|RD|TH)", bare):  # 1ST, 22ND
            words.append(word.lower())
        else:
            words.append(word.title())
    return " ".join(words)


def fmt_date(iso: str | None) -> str:
    if not iso:
        return ""
    try:
        y, m, d = str(iso)[:10].split("-")
        return date(int(y), int(m), int(d)).strftime("%b %-d, %Y")
    except (ValueError, TypeError):
        try:
            y, m, d = str(iso)[:10].split("-")
            return f"{date(int(y), int(m), int(d)):%b %d, %Y}".replace(" 0", " ")
        except Exception:
            return str(iso)[:10]


def fmt_month(iso: str | None) -> str:
    if not iso:
        return ""
    try:
        y, m, _ = str(iso)[:10].split("-")
        return date(int(y), int(m), 1).strftime("%b %Y")
    except Exception:
        return str(iso)[:7]


def load_areas() -> tuple[dict, list[dict]]:
    index = json.loads((DATA / "areas" / "index.json").read_text(encoding="utf-8"))
    areas = []
    for area in index.get("areas", []):
        if area.get("hidden"):
            continue
        path = DATA / "areas" / f"{area['slug']}.json"
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        for lead in payload.get("leads", []):
            lead["_city"] = clean_city(lead.get("city"))
            lead["_state"] = area["label"]
        areas.append({**area, "payload": payload})
    return index, areas


# ---------------------------------------------------------------- numbers per page


def summarise(leads: list[dict]) -> dict:
    """Everything a page states about itself, computed from its own rows.

    This is what makes each page substantially different from its siblings rather than
    the same template with a name swapped: the counts, the delivery years and the
    largest projects are genuinely different per place.
    """
    stages = Counter((lead.get("stage") or "unknown") for lead in leads)
    units = sum(int(lead.get("units") or 0) for lead in leads)
    sold = [lead for lead in leads if lead.get("saleDate")]
    pipeline = [lead for lead in leads if (lead.get("stage") or "") != "sold"]

    sales_by_year = Counter(str(lead["saleDate"])[:4] for lead in sold)
    opening_by_year = Counter(
        str(lead["openingDate"])[:4] for lead in leads if lead.get("openingDate")
    )
    cities = Counter(lead["_city"] for lead in leads if lead.get("_city"))

    biggest = sorted(
        (lead for lead in leads if lead.get("units")),
        key=lambda lead: int(lead["units"]),
        reverse=True,
    )[:5]

    developers = Counter(
        (lead.get("developer") or "").strip()
        for lead in leads
        if (lead.get("developer") or "").strip()
    )

    return {
        "count": len(leads),
        "units": units,
        "stages": stages,
        "sold": len(sold),
        "pipeline": len(pipeline),
        "sales_by_year": sales_by_year,
        "opening_by_year": opening_by_year,
        "cities": cities,
        "biggest": biggest,
        "developers": developers,
        "with_units": sum(1 for lead in leads if lead.get("units")),
    }


def answer_block(place: str, s: dict, updated: str) -> str:
    """The 40-60 word extractable answer that answer engines lift verbatim.

    Kept to plain declarative sentences with the numbers in them, because a hedged
    paragraph is not quotable and an unsourced one should not be quoted.
    """
    parts = [f"CraneSignal tracks {s['count']:,} apartment buildings in {place}"]
    if s["units"]:
        parts.append(f"covering {s['units']:,} units")
    parts = [", ".join(parts) + "."]

    building = s["stages"].get("under construction", 0)
    permitted = s["stages"].get("permitted", 0)
    planned = s["stages"].get("planned", 0)
    pipeline_bits = []
    if building:
        pipeline_bits.append(f"{building:,} under construction")
    if permitted:
        pipeline_bits.append(f"{permitted:,} permitted")
    if planned:
        pipeline_bits.append(f"{planned:,} planned")
    if pipeline_bits:
        parts.append(f"{'; '.join(pipeline_bits)}.")
    if s["sold"]:
        recent = max(s["sales_by_year"]) if s["sales_by_year"] else None
        if recent:
            parts.append(
                f"{s['sold']:,} have changed owner, {s['sales_by_year'][recent]:,} of them in {recent}."
            )
        else:
            parts.append(f"{s['sold']:,} have changed owner.")
    parts.append(f"Every building links its public source record. Updated {fmt_date(updated)}.")
    return " ".join(parts)


# ---------------------------------------------------------------- html rendering


def fit_title(title: str, limit: int = 60) -> str:
    """Keep titles inside the length a search result actually shows.

    Google cuts the title at roughly 60 characters, so anything past that is spent, and
    the place name is what matters most here. Rather than hand-trim one page, drop the
    least informative words in a fixed order until it fits.
    """
    if len(title) <= limit:
        return title
    for long, short in (
        ("Multifamily Construction Pipeline", "Multifamily Pipeline"),
        ("Apartment Construction and Sales", "Apartment Construction"),
        ("Apartment Construction Pipeline", "Apartment Pipeline"),
    ):
        if long in title:
            title = title.replace(long, short)
            if len(title) <= limit:
                return title
    return title


def page_shell(title: str, description: str, canonical: str, jsonld: str, body: str,
               depth: int) -> str:
    """One static page. No JavaScript is required to read it.

    The chat panel and app scripts are deliberately left off: these pages exist to be
    read by crawlers and by people arriving from a search result, and every script is
    another thing that can fail before the content renders.
    """
    # Links are root-relative. The site is always served from /, and counting "../" per
    # page depth was both wrong (off by one on every page) and easy to get wrong again.
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <link rel="icon" type="image/svg+xml" href="/static/favicon.svg">
  <link rel="apple-touch-icon" href="/static/apple-touch-icon.png">
  <title>{fit_title(title)}</title>
  <meta name="description" content="{description}">
  <link rel="canonical" href="{canonical}">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="CraneSignal">
  <meta property="og:title" content="{fit_title(title)}">
  <meta property="og:description" content="{description}">
  <meta property="og:url" content="{canonical}">
  <meta property="og:image" content="{HOST}/img/og-default.png">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:image" content="{HOST}/img/og-default.png">
  <link rel="stylesheet" href="/css/styles.css" />
  <script type="application/ld+json">
{jsonld}
  </script>
  <style>
    .static-page {{ max-width: 1100px; margin: 0 auto; padding: 24px 20px 64px; }}
    .static-page h1 {{ font-size: 26px; letter-spacing: -0.01em; margin: 0 0 6px; }}
    .static-page .answer {{ font-size: 15px; line-height: 1.6; max-width: 70ch; margin: 12px 0 20px; }}
    .static-page h2 {{ font-size: 15px; margin: 28px 0 10px; }}
    .static-page table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    .static-page th, .static-page td {{ text-align: left; padding: 6px 8px; border-bottom: 1px solid var(--rule); vertical-align: top; }}
    .static-page th {{ font-size: 11px; text-transform: uppercase; letter-spacing: 0.03em; color: var(--text-muted); }}
    .static-page .num {{ text-align: right; white-space: nowrap; }}
    .static-page .facts {{ display: flex; flex-wrap: wrap; gap: 18px; margin: 0 0 8px; padding: 0; list-style: none; font-size: 13px; }}
    .static-page .facts b {{ display: block; font-size: 20px; }}
    .static-page nav.crumbs {{ font-size: 12px; margin-bottom: 14px; }}
    .static-page .sibs {{ font-size: 13px; line-height: 1.9; }}
    .static-page .next-step {{ margin: 28px 0 8px; padding: 16px 18px; border: 1px solid var(--rule); border-left: 4px solid var(--accent); max-width: 80ch; }}
    .static-page .next-step h2 {{ margin-top: 0; }}
    .static-page .next-step p {{ font-size: 14px; line-height: 1.55; margin: 8px 0 0; }}
    .static-page .mgmt {{ color: var(--text-muted); font-size: 12px; }}
    .static-page .download {{ font-size: 13px; line-height: 1.55; max-width: 80ch;
      margin: 0 0 14px; padding: 10px 14px; background: var(--paper-2);
      border-left: 4px solid var(--accent); }}
    .static-page .faq {{ max-width: 80ch; font-size: 14px; }}
    .static-page .faq dt {{ font-weight: 600; margin-top: 14px; }}
    .static-page .faq dd {{ margin: 4px 0 0; line-height: 1.55; }}
    .static-page footer {{ margin-top: 40px; font-size: 12px; color: var(--text-muted); }}
  </style>
</head>
<body>
  <div class="static-page">
{body}
  </div>
</body>
</html>
"""


def table(leads: list[dict], sold_view: bool) -> str:
    date_head = "Sold" if sold_view else "Opens"
    rows = [
        "    <table>",
        "      <thead><tr>"
        "<th>Building</th><th>Address</th><th>City</th><th class=\"num\">Units</th>"
        f"<th>Stage</th><th>{date_head}</th><th>{'Buyer' if sold_view else 'Developer'}</th>"
        "<th>Who to call</th><th>Source</th></tr></thead>",
        "      <tbody>",
    ]
    for lead in leads:
        name = pretty(lead.get("community") or lead.get("property")) or "(unnamed)"
        when = fmt_month(lead.get("saleDate") if sold_view else lead.get("openingDate"))
        who = pretty(lead.get("buyer") if sold_view else lead.get("developer"))
        sources = lead.get("sources") or []
        if sources:
            src = " · ".join(
                f'<a href="{esc(s.get("url"))}" rel="nofollow noopener">{esc(s.get("label") or "record")}</a>'
                for s in sources[:2]
                if s.get("url")
            )
        else:
            src = ""
        # Who to call. The phone is what a salesperson dials; the management company is who
        # actually buys software, so it goes underneath rather than being dropped. Both are
        # blank where nothing was found, because a guessed number is worse than none.
        call_bits = []
        if lead.get("officePhone"):
            call_bits.append(esc(lead["officePhone"]))
        if lead.get("managementCompany"):
            call_bits.append(f'<span class="mgmt">{esc(pretty(lead["managementCompany"]))}</span>')
        call = "<br>".join(call_bits)

        units = f"{int(lead['units']):,}" if lead.get("units") else ""
        # Many sale records carry no building name, so the name field holds the address.
        # Printing it twice on one row looks like a bug; the name column keeps it.
        address = pretty(lead.get("address"))
        if address and address == name:
            address = ""
        rows.append(
            "        <tr>"
            f"<td>{esc(name)}</td>"
            f"<td>{esc(address)}</td>"
            f"<td>{esc(lead.get('_city') or lead.get('city') or '')}</td>"
            f'<td class="num">{units}</td>'
            f"<td>{esc(lead.get('stage') or '')}</td>"
            f"<td>{esc(when)}</td>"
            f"<td>{esc(who)}</td>"
            f"<td>{call}</td>"
            f"<td>{src}</td>"
            "</tr>"
        )
    rows += ["      </tbody>", "    </table>"]
    return "\n".join(rows)


def facts_strip(s: dict) -> str:
    items = [("Buildings", f"{s['count']:,}")]
    if s["units"]:
        items.append(("Units", f"{s['units']:,}"))
    if s["stages"].get("under construction"):
        items.append(("Under construction", f"{s['stages']['under construction']:,}"))
    if s["sold"]:
        items.append(("Changed owner", f"{s['sold']:,}"))
    return (
        '    <ul class="facts">\n'
        + "\n".join(f"      <li><b>{v}</b>{k}</li>" for k, v in items)
        + "\n    </ul>"
    )


def breakdowns(s: dict, place: str) -> str:
    """The per-place analysis. Every number here is computed from this page's own rows."""
    out = []

    if s["stages"]:
        rows = [
            f"        <tr><td>{esc(stage)}</td><td class=\"num\">{count:,}</td></tr>"
            for stage in STAGE_ORDER
            if (count := s["stages"].get(stage))
        ]
        if rows:
            out += [
                "    <h2>Where these buildings are in their life</h2>",
                "    <table><thead><tr><th>Stage</th><th class=\"num\">Buildings</th></tr></thead><tbody>",
                *rows,
                "    </tbody></table>",
            ]

    if s["opening_by_year"]:
        years = sorted(s["opening_by_year"])
        rows = [
            f"        <tr><td>{y}</td><td class=\"num\">{s['opening_by_year'][y]:,}</td></tr>"
            for y in years
        ]
        out += [
            f"    <h2>When they are expected to open</h2>",
            "    <p>Expected opening dates come from the construction record, and move when the record moves.</p>",
            "    <table><thead><tr><th>Year</th><th class=\"num\">Buildings</th></tr></thead><tbody>",
            *rows,
            "    </tbody></table>",
        ]

    if s["sales_by_year"]:
        years = sorted(s["sales_by_year"])
        rows = [
            f"        <tr><td>{y}</td><td class=\"num\">{s['sales_by_year'][y]:,}</td></tr>"
            for y in years
        ]
        out += [
            "    <h2>Recorded sales by year</h2>",
            "    <table><thead><tr><th>Year</th><th class=\"num\">Buildings sold</th></tr></thead><tbody>",
            *rows,
            "    </tbody></table>",
        ]

    if len(s["cities"]) > 1:
        top = s["cities"].most_common(12)
        rows = [f"        <tr><td>{esc(c)}</td><td class=\"num\">{n:,}</td></tr>" for c, n in top]
        out += [
            f"    <h2>Busiest cities in {esc(place)}</h2>",
            "    <table><thead><tr><th>City</th><th class=\"num\">Buildings</th></tr></thead><tbody>",
            *rows,
            "    </tbody></table>",
        ]

    if s["biggest"]:
        items = []
        for lead in s["biggest"]:
            name = pretty(lead.get("community") or lead.get("property")) or "(unnamed)"
            where = lead.get("_city") or lead.get("city") or ""
            items.append(
                f"      <li>{esc(name)} &mdash; {int(lead['units']):,} units, "
                f"{esc(where)}, {esc(lead.get('stage') or '')}</li>"
            )
        out += [
            "    <h2>Largest projects by unit count</h2>",
            "    <ol>",
            *items,
            "    </ol>",
        ]

    return "\n".join(out)


def next_step(place: str, state_slug: str | None) -> str:
    """What a reader does after reading. These pages had no answer to that.

    Kept to what is actually true and free: the same list filtered and sortable, a PDF and a
    spreadsheet that need no account, and a way to ask for a metro we do not cover. No
    invented offer, no signup wall, and no claim the data cannot back.
    """
    where = f"/index.html?area={state_slug}" if state_slug else "/index.html"
    return "\n".join([
        '    <div class="next-step">',
        f"      <h2>Take this list with you</h2>",
        f'      <p><a href="{where}"><strong>Open {esc(place)} in CraneSignal</strong></a> to sort and '
        "filter these buildings, see the lead score behind each one, and download the call "
        "list as a PDF or the whole thing as a spreadsheet. Free, and no account needed for "
        "any of that.</p>",
        '      <p>A free account adds the manager name and direct phone where the record has '
        'them, and a note on why to call now.</p>',
        f'      <p>Not your area? <a href="{LANDING}/#next">Ask for your metro</a> &mdash; it is '
        "free and we add areas on request.</p>",
        "    </div>",
    ])


def faq_for(place: str, s: dict, updated: str) -> list[tuple[str, str]]:
    """Real questions with answers computed from this page's own rows.

    Answer engines do not summarise a page, they lift the sentence that is the answer, so
    each one is a standalone statement carrying its own subject, number and as-of date. The
    text here is rendered visibly *and* emitted as FAQPage JSON-LD, character for character
    -- LD that says something the page does not show is treated as spam.
    """
    when = fmt_date(updated)
    qa: list[tuple[str, str]] = []

    building = s["stages"].get("under construction", 0)
    if building:
        qa.append((
            f"How many apartment buildings in {place} are under construction?",
            f"{building:,} of the {s['count']:,} apartment buildings CraneSignal tracks in "
            f"{place} are under construction, as of {when}.",
        ))

    permitted = s["stages"].get("permitted", 0) + s["stages"].get("planned", 0)
    if permitted:
        qa.append((
            f"How many new apartment projects are planned or permitted in {place}?",
            f"{permitted:,} are permitted or planned but not yet under construction in "
            f"{place}, as of {when}.",
        ))

    if s["sold"]:
        newest = max(s["sales_by_year"]) if s["sales_by_year"] else None
        extra = (
            f", {s['sales_by_year'][newest]:,} of them in {newest}" if newest else ""
        )
        qa.append((
            f"How many apartment complexes in {place} have recently changed owner?",
            f"{s['sold']:,} apartment buildings in {place} have a recorded sale{extra}, "
            f"as of {when}.",
        ))

    if s["biggest"]:
        top = s["biggest"][0]
        name = pretty(top.get("community") or top.get("property")) or "an unnamed project"
        where = top.get("_city") or top.get("city") or place
        qa.append((
            f"What is the largest apartment project in {place}?",
            f"{name} in {where} is the largest on this page at "
            f"{int(top['units']):,} units, currently {top.get('stage') or 'unrecorded'}.",
        ))

    if s["opening_by_year"]:
        year = min(y for y in s["opening_by_year"] if y >= str(date.today().year)) \
            if any(y >= str(date.today().year) for y in s["opening_by_year"]) \
            else max(s["opening_by_year"])
        qa.append((
            f"When do the next apartment buildings in {place} open?",
            f"{s['opening_by_year'][year]:,} buildings in {place} have an expected opening "
            f"date in {year}. Opening dates come from the construction record and move when "
            f"that record moves.",
        ))

    qa.append((
        f"Where does this {place} apartment data come from?",
        "Public records only: state and city construction permits, county appraisal-district "
        "sale records, and public announcements. Every building on this page links the record "
        "it came from, and a fact with no source is left blank rather than guessed.",
    ))
    return qa[:5]


def faq_html(qa: list[tuple[str, str]]) -> str:
    out = ["    <h2>Questions about this list</h2>", '    <dl class="faq">']
    for question, answer in qa:
        out.append(f"      <dt>{esc(question)}</dt>")
        out.append(f"      <dd>{esc(answer)}</dd>")
    out.append("    </dl>")
    return "\n".join(out)


def breadcrumb_items(crumbs_html: str, here: str, canonical: str) -> list[dict]:
    """BreadcrumbList built from the same links the page shows, so the two cannot diverge."""
    items = []
    for href, label in re.findall(r'<a href="([^"]+)">([^<]+)</a>', crumbs_html):
        url = href if href.startswith("http") else f"{HOST}{href}"
        items.append({
            "@type": "ListItem",
            "position": len(items) + 1,
            "name": html.unescape(label),
            "item": url,
        })
    items.append({
        "@type": "ListItem",
        "position": len(items) + 1,
        "name": html.unescape(re.sub(r"<[^>]+>", "", here)),
        "item": canonical,
    })
    return items


# ---------------------------------------------------------------- the machine-readable copy

# What the spreadsheet beside each page contains, and what each column means. This list is
# the single source for three things that must agree: the CSV header, the visible note on
# the page, and the Dataset's variableMeasured. Google reads the last one to decide what
# questions the data can answer, so a column missing from here is a column no engine knows
# exists.
CSV_COLUMNS: list[tuple[str, str, str]] = [
    ("Building", "Building name, or the street address when the record carries no name", "name"),
    ("Address", "Street address from the public record", "address"),
    ("City", "City, cleaned of the casing and county suffixes the records vary on", "city"),
    ("State", "US state", "state"),
    ("Units", "Number of apartment units", "units"),
    ("Stage", "planned, permitted, under construction, leasing or sold", "stage"),
    ("Opens", "Expected opening date, from the construction record", "opens"),
    ("Sold", "Date of the recorded sale", "sold"),
    ("Buyer", "Buyer named on the sale record, often a holding company", "buyer"),
    ("Developer", "Developer or contractor named on the construction record", "developer"),
    ("Office phone", "Published leasing or management office phone, where one exists", "phone"),
    ("Management company", "The company that runs the building, where it is published -- "
     "the buyer for anything sold to a portfolio rather than to one address", "management"),
    ("Contact source", "Where the phone and management company were found, and on what date",
     "contact_source"),
    ("Source", "What kind of public record the row came from", "source"),
    ("Source URL", "Direct link to that record, so any row can be checked", "source_url"),
]


def csv_cell(lead: dict, key: str) -> str:
    """One CSV value. Blank means the record is silent, never that the value is zero."""
    sources = [s for s in (lead.get("sources") or []) if s.get("url")]
    name = pretty(lead.get("community") or lead.get("property")) or ""
    address = pretty(lead.get("address"))
    return {
        "name": name or address,
        # The HTML table blanks a duplicated address because printing it twice looks like
        # a bug. A spreadsheet is filtered and sorted, so both columns stay filled.
        "address": address,
        "city": lead.get("_city") or lead.get("city") or "",
        "state": lead.get("_state") or "",
        "units": str(int(lead["units"])) if lead.get("units") else "",
        "stage": lead.get("stage") or "",
        "opens": str(lead.get("openingDate") or "")[:10],
        "sold": str(lead.get("saleDate") or "")[:10],
        "buyer": pretty(lead.get("buyer")),
        "developer": pretty(lead.get("developer")),
        "phone": lead.get("officePhone") or "",
        "management": lead.get("managementCompany") or "",
        # The contact is the one thing on a row that came from a web page rather than a public
        # record, so it carries where it came from and when, in the row itself.
        "contact_source": (
            f"{lead['contactSource']} ({lead.get('contactFoundOn') or ''})".strip()
            if lead.get("contactSource") else ""
        ),
        "source": sources[0].get("label") or "record" if sources else "",
        "source_url": sources[0]["url"] if sources else "",
    }[key]


def csv_for(leads: list[dict]) -> str:
    """The whole list as a spreadsheet, not the capped set the HTML table shows.

    Why this file exists at all: the site already offered a free spreadsheet, but it was
    built inside the visitor's browser and never existed as a URL, so no crawler, no
    Google Dataset Search and no answer engine could ever fetch it. The measured opening
    for CraneSignal is the free-data question -- engines name paid tools 70% of the time
    even when asked for a free source, because as far as they can tell none exists. A real
    file at a real address, declared in the Dataset's distribution, is how that changes.

    ISO dates rather than the page's "Sep 2026", because this one is read by machines and
    sorted in spreadsheets.
    """
    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow([column for column, _, _ in CSV_COLUMNS])
    for lead in leads:
        writer.writerow([csv_cell(lead, key) for _, _, key in CSV_COLUMNS])
    return out.getvalue()


def states_phrase(leads: list[dict]) -> str:
    """The states these rows are actually in, as a phrase a sentence can use.

    The two cross-cutting pages used to hardcode "Texas and Arizona". On 2026-09-26 the
    opening-2027-2028 page held 89 buildings, every one of them in Texas and none in
    Arizona, and said "in Texas and Arizona" four times in its visible FAQ -- text that is
    also FAQPage schema, so Google can show it as a rich result. Naming a state we have no
    buildings in is the one thing this data must never do. Derived from the rows, it cannot
    say it again.
    """
    states = sorted({lead["_state"] for lead in leads if lead.get("_state")})
    if not states:
        return "the areas CraneSignal covers"
    if len(states) == 1:
        return states[0]
    return ", ".join(states[:-1]) + f" and {states[-1]}"


def coverage_for(leads: list[dict], place: str) -> dict:
    """spatialCoverage, temporalCoverage and keywords, computed from the rows themselves.

    The home page's Dataset has carried these since the start; the 18 pages built to
    actually be found carried none of them, which is backwards -- these are the properties
    that tell an engine the data is about Houston, covers 2024 to 2028, and can answer a
    question about either.
    """
    states = sorted({lead["_state"] for lead in leads if lead.get("_state")})
    cities = Counter(lead["_city"] for lead in leads if lead.get("_city"))

    dates = sorted(
        str(value)[:10]
        for lead in leads
        for value in (lead.get("permitDate"), lead.get("openingDate"), lead.get("saleDate"))
        if value and re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(value)[:10])
    )

    keywords = [
        "apartment construction pipeline",
        "multifamily development",
        "apartment sales records",
    ]
    # "Texas and Arizona apartments" -- the two cross-cutting pages' place -- is not a
    # phrase anyone types. Every other place name is.
    if " and " not in place:
        keywords.append(f"{place} apartments")
    keywords += [f"{city} apartments" for city, _ in cities.most_common(3)]

    out: dict = {"keywords": sorted(set(keywords))}
    if place in states:
        # A state page. Saying Arizona is contained in Arizona is worse than saying nothing.
        out["spatialCoverage"] = {"@type": "AdministrativeArea", "name": place}
    elif " and " in place and len(states) > 1:
        out["spatialCoverage"] = [
            {"@type": "AdministrativeArea", "name": state} for state in states
        ]
    else:
        out["spatialCoverage"] = {"@type": "Place", "name": place}
        if states:
            out["spatialCoverage"]["containedInPlace"] = [
                {"@type": "AdministrativeArea", "name": state} for state in states
            ]
    if dates:
        # An open-ended interval would be wrong: these are recorded dates with a real
        # first and last, and one of them is in the future because the buildings are not
        # finished. That is the whole point of the dataset.
        out["temporalCoverage"] = dates[0] if dates[0] == dates[-1] else f"{dates[0]}/{dates[-1]}"
    return out


def jsonld_for(name: str, description: str, canonical: str, leads: list[dict],
               updated: str, place: str, csv_url: str, csv_bytes: int,
               faq: list[tuple[str, str]] | None = None,
               crumbs: list[dict] | None = None) -> str:
    """Dataset for the collection, ItemList for the rows.

    ItemList is capped: the point is to describe the list to a machine, not to restate
    every row in JSON when the row is already in the HTML above it.
    """
    items = []
    for i, lead in enumerate(leads[:50], start=1):
        label = pretty(lead.get("community") or lead.get("property")) or "(unnamed)"
        where = ", ".join(
            bit for bit in (pretty(lead.get("address")), lead.get("_city") or lead.get("city")) if bit
        )
        items.append(
            {
                "@type": "ListItem",
                "position": i,
                "name": label,
                "description": where or None,
            }
        )
    for item in items:
        if item["description"] is None:
            del item["description"]

    # One Organization for the whole site, under a single @id, so the two hosts are one
    # entity to a model rather than two that happen to share a name. It is declared here
    # rather than only referenced: the @id lives on cranesignal.com, so a crawler reading
    # this page alone previously found creator and publisher pointing at a node that was
    # nowhere on the page. Same id, so nothing splits; enough fields that it resolves.
    graph = [
        {
            "@type": "Organization",
            "@id": ORG_ID,
            "name": "CraneSignal",
            "url": LANDING,
        },
        {
            "@type": "Dataset",
            "name": name,
            "description": description,
            "url": canonical,
            "isAccessibleForFree": True,
            "dateModified": updated,
            "creator": {"@id": ORG_ID},
            "publisher": {"@id": ORG_ID},
            "creditText": "CraneSignal",
            # No usageInfo. It pointed at under-the-hood.html until 2026-09-26, which turned
            # out to render 8 visible words without JavaScript -- so the property told a
            # cautious engine "the method is written up over here" and sent it to a blank
            # page. Better to claim nothing than to claim that. Put it back when there is a
            # readable page to point at.
            "distribution": [
                {
                    "@type": "DataDownload",
                    "name": f"{name} (CSV)",
                    "encodingFormat": "text/csv",
                    "contentUrl": csv_url,
                    # With a unit. A bare number here is ambiguous, and the one thing a
                    # size is for is telling a fetcher what it is about to download.
                    "contentSize": f"{csv_bytes} B",
                }
            ],
            "variableMeasured": [
                {"@type": "PropertyValue", "name": column, "description": about}
                for column, about, _ in CSV_COLUMNS
            ],
            **coverage_for(leads, place),
        },
        {
            "@type": "ItemList",
            "name": name,
            "numberOfItems": len(leads),
            "itemListElement": items,
        },
    ]
    if crumbs:
        graph.append({"@type": "BreadcrumbList", "itemListElement": crumbs})
    if faq:
        graph.append({
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": question,
                    "acceptedAnswer": {"@type": "Answer", "text": answer},
                }
                for question, answer in faq
            ],
        })

    payload = {"@context": "https://schema.org", "@graph": graph}
    text = json.dumps(payload, indent=2)
    return "\n".join("  " + line for line in text.splitlines())


# ---------------------------------------------------------------- page builders


def download_line(leads: list[dict], shown: int, csv_url: str) -> str:
    """The visible half of the CSV. A file nothing links to is a file nobody finds: an
    unlinked URL in the schema is weaker than a linked one, and a human reading the page
    has no other way to get the rows the table had to cut."""
    with_phone = sum(1 for lead in leads if lead.get("officePhone"))
    extra = (
        f" That is all {len(leads):,} buildings, not the {shown:,} this page lists."
        if len(leads) > shown else ""
    )
    # Only mentioned when there are some. "0 published office phone numbers" reads as a
    # boast about nothing, and contact data is already this dataset's weakest column.
    phones = f"{with_phone:,} published office phone numbers, " if with_phone else ""
    return (
        '    <p class="download">'
        f'<strong><a href="{esc(csv_url)}" download>Download this list as a spreadsheet '
        f'(CSV, {len(leads):,} rows)</a></strong>.{esc(extra)} '
        "Free, no account, no sign-up. "
        f"{len(CSV_COLUMNS)} columns including units, stage, dates, buyer, developer, "
        f"{phones}and a link to the public record behind every row."
        "</p>"
    )


def render_page(*, title, h1, description, canonical, depth, place, leads, updated,
                crumbs, siblings, sold_view=False, intro_extra="", state_slug=None
                ) -> tuple[str, str]:
    """Returns the page and the spreadsheet that sits beside it.

    Both come out of one call so the row count the page claims, the byte size the schema
    declares and the file on disk cannot drift apart.
    """
    csv_text = csv_for(leads)
    csv_url = canonical[: -len(".html")] + ".csv"
    s = summarise(leads)
    body = [
        f'    <nav class="crumbs">{crumbs}</nav>',
        f"    <h1>{h1}</h1>",
        facts_strip(s),
        f'    <p class="answer">{esc(answer_block(place, s, updated))}</p>',
    ]
    if intro_extra:
        body.append(f"    <p>{intro_extra}</p>")
    body.append(breakdowns(s, place))
    shown = leads[:ROW_CAP]
    if len(leads) > ROW_CAP:
        heading = f"The {len(shown):,} largest of {len(leads):,} buildings"
        note = (
            f"Sorted by unit count. This page lists the {len(shown):,} largest; the rest are on "
            "the metro and city pages linked below, and all of them are in the searchable list. "
            "Every row names the public record it came from. Some links open that building's own record; most open the county or city source it was published in, where the address finds it. Blank cells mean the record does not say, never that we guessed."
        )
    else:
        heading = f"Every building ({len(leads):,})"
        note = (
            "Sorted by unit count. Every row names the public record it came from. Some links open that building's own record; most open the county or city source it was published in, where the address finds it. Blank cells mean the record does not say, never that we guessed."
        )
    body += [f"    <h2>{heading}</h2>", f"    <p>{note}</p>",
             download_line(leads, len(shown), csv_url), table(shown, sold_view)]
    body.append(next_step(place, state_slug))
    faq = faq_for(place, s, updated)
    body.append(faq_html(faq))
    if siblings:
        body += ["    <h2>Nearby and related</h2>", f'    <p class="sibs">{siblings}</p>']
    body += [
        "    <footer>",
        f"      Data updated {esc(fmt_date(updated))}. Built from public construction and "
        "sale records only &mdash; no proprietary feeds, no purchased lists. ",
        '      <a href="/index.html">Search every building</a> &middot; '
        f'      <a href="{LANDING}">CraneSignal home</a>',
        "    </footer>",
    ]
    jsonld = jsonld_for(
        h1, description, canonical, leads, updated,
        place=place,
        csv_url=csv_url,
        csv_bytes=len(csv_text.encode("utf-8")),
        faq=faq,
        crumbs=breadcrumb_items(crumbs, h1, canonical),
    )
    page = page_shell(title, description, canonical, jsonld, "\n".join(body), depth)
    return page, csv_text


def emit(pages: dict[Path, str], path: Path, **kwargs) -> None:
    """Record one page and the spreadsheet beside it. Same stem, same directory, so the
    link on the page and the contentUrl in the schema are both just the path with a
    different extension."""
    page, csv_text = render_page(**kwargs)
    pages[path] = page
    pages[path.with_suffix(".csv")] = csv_text


def sort_leads(leads: list[dict]) -> list[dict]:
    return sorted(leads, key=lambda lead: (-int(lead.get("units") or 0),
                                           (lead.get("community") or "")))


def build_all() -> dict[Path, str]:
    index, areas = load_areas()
    updated = index.get("updated", "")
    pages: dict[Path, str] = {}

    state_links = {
        area["slug"]: f'<a href="{HOST}/leads/{area["slug"]}.html">{esc(area["label"])}</a>'
        for area in areas
    }

    for area in areas:
        slug = area["slug"]
        label = area["label"]
        leads = area["payload"].get("leads", [])
        home = '<a href="/index.html">All buildings</a>'

        # --- metro pages, where the data groups cities into metros
        by_metro: dict[str, list[dict]] = defaultdict(list)
        for lead in leads:
            if lead.get("metro"):
                by_metro[lead["metro"]].append(lead)
        metro_pages = {}
        for metro, rows in by_metro.items():
            if metro.lower().startswith("rest of") or len(rows) < CITY_MIN:
                continue
            metro_pages[metro] = rows

        # --- city pages, for cities big enough to carry one
        #
        # A metro is usually named after its anchor city, so "Houston" the metro and
        # "Houston" the city would write to the same file and, worse, compete with each
        # other in search for the same phrase. The metro page wins: it contains the
        # city's buildings plus the suburbs, so it is the strictly better answer. The
        # namesake city therefore gets no page of its own.
        metro_slugs = {slugify(m) for m in metro_pages}
        by_city: dict[str, list[dict]] = defaultdict(list)
        for lead in leads:
            if lead.get("_city"):
                by_city[lead["_city"]].append(lead)
        city_pages = {
            c: rows
            for c, rows in by_city.items()
            if len(rows) >= CITY_MIN and slugify(c) not in metro_slugs
        }

        metro_link_list = " &middot; ".join(
            f'<a href="/leads/{slug}/{slugify(m)}.html">{esc(m)}</a>'
            for m in sorted(metro_pages, key=lambda m: -len(metro_pages[m]))
        )
        city_link_list = " &middot; ".join(
            f'<a href="/leads/{slug}/{slugify(c)}.html">{esc(c)}</a>'
            for c in sorted(city_pages, key=lambda c: -len(city_pages[c]))
        )

        # ---------- state page
        sibs = []
        if metro_link_list:
            sibs.append(f"Metros: {metro_link_list}")
        if city_link_list:
            sibs.append(f"Cities: {city_link_list}")
        others = [state_links[a["slug"]] for a in areas if a["slug"] != slug]
        if others:
            sibs.append("Other states: " + " &middot; ".join(others))

        s = summarise(leads)
        emit(pages, OUT / f"{slug}.html",
            title=f"{label} Apartment Construction Pipeline | CraneSignal",
            h1=f"{esc(label)} apartment construction pipeline and recent sales",
            description=(
                f"{s['count']:,} apartment buildings in {label} that are planned, permitted, "
                f"under construction or recently sold &mdash; {s['units']:,} units, each with "
                "its public source record. Free, updated weekly."
            ),
            canonical=f"{HOST}/leads/{slug}.html",
            depth=1,
            place=label,
            leads=sort_leads(leads),
            updated=updated,
            state_slug=slug,
            crumbs=home,
            siblings="<br>".join(sibs),
        )

        # ---------- metro pages
        for metro, rows in metro_pages.items():
            ms = summarise(rows)
            sib_bits = [f"State: {state_links[slug]}"]
            peers = [
                f'<a href="/leads/{slug}/{slugify(m)}.html">{esc(m)}</a>'
                for m in sorted(metro_pages, key=lambda m: -len(metro_pages[m]))
                if m != metro
            ]
            if peers:
                sib_bits.append("Other metros: " + " &middot; ".join(peers))
            in_metro = [
                f'<a href="/leads/{slug}/{slugify(c)}.html">{esc(c)}</a>'
                for c in sorted(city_pages, key=lambda c: -len(city_pages[c]))
                if any(r.get("metro") == metro for r in city_pages[c])
            ]
            if in_metro:
                sib_bits.append("Cities here: " + " &middot; ".join(in_metro))

            emit(pages, OUT / slug / f"{slugify(metro)}.html",
                title=f"{metro} Multifamily Construction Pipeline | CraneSignal",
                h1=f"{esc(metro)} multifamily construction pipeline and apartment sales",
                description=(
                    f"{ms['count']:,} apartment buildings across {metro}: "
                    f"{ms['stages'].get('under construction', 0):,} under construction, "
                    f"{ms['sold']:,} recently sold, {ms['units']:,} units in all. "
                    "Building-level detail with a public source for every row."
                ),
                canonical=f"{HOST}/leads/{slug}/{slugify(metro)}.html",
                depth=2,
                place=metro,
                leads=sort_leads(rows),
                updated=updated,
                state_slug=slug,
                crumbs=f'<a href="/index.html">All buildings</a> &rsaquo; '
                       f'<a href="/leads/{slug}.html">{esc(label)}</a>',
                siblings="<br>".join(sib_bits),
                intro_extra=(
                    "Market reports for this metro usually stop at totals. This is the list "
                    "behind the totals: which buildings, where, how big, how far along, and "
                    "which public record says so."
                ),
            )

        # ---------- city pages
        for city, rows in city_pages.items():
            cs = summarise(rows)
            metro = next((r.get("metro") for r in rows if r.get("metro")), None)
            crumbs = f'<a href="/index.html">All buildings</a> &rsaquo; ' \
                     f'<a href="/leads/{slug}.html">{esc(label)}</a>'
            if metro and metro in metro_pages:
                crumbs += f' &rsaquo; <a href="/leads/{slug}/{slugify(metro)}.html">{esc(metro)}</a>'
            peers = [
                f'<a href="/leads/{slug}/{slugify(c)}.html">{esc(c)}</a>'
                for c in sorted(city_pages, key=lambda c: -len(city_pages[c]))
                if c != city
            ][:12]
            sib_bits = [f"State: {state_links[slug]}"]
            if metro and metro in metro_pages:
                sib_bits.append(f'Metro: <a href="/leads/{slug}/{slugify(metro)}.html">{esc(metro)}</a>')
            if peers:
                sib_bits.append("Other cities: " + " &middot; ".join(peers))

            emit(pages, OUT / slug / f"{slugify(city)}.html",
                title=f"{city} Apartment Construction and Sales | CraneSignal",
                h1=f"Apartment buildings under construction and recently sold in {esc(city)}",
                description=(
                    f"{cs['count']:,} apartment buildings in {city}, {label}: "
                    f"{cs['stages'].get('under construction', 0):,} under construction, "
                    f"{cs['sold']:,} recently sold, {cs['units']:,} units. "
                    "Each with its public source record."
                ),
                canonical=f"{HOST}/leads/{slug}/{slugify(city)}.html",
                depth=2,
                place=f"{city}, {label}",
                leads=sort_leads(rows),
                updated=updated,
                state_slug=slug,
                crumbs=crumbs,
                siblings="<br>".join(sib_bits),
            )

    # ---------- two cross-cutting lists, the format answer engines cite most
    all_leads = [lead for area in areas for lead in area["payload"].get("leads", [])]

    opening_next = [
        lead for lead in all_leads
        if lead.get("openingDate") and str(lead["openingDate"])[:4] in {"2027", "2028"}
    ]
    if len(opening_next) >= CITY_MIN:
        emit(pages, OUT / "opening-2027-2028.html",
            title="Apartment Buildings Opening in 2027-2028 | CraneSignal",
            h1="Apartment buildings expected to open in 2027 and 2028",
            description=(
                f"{len(opening_next):,} apartment buildings with expected opening dates in "
                "2027 or 2028, by city and size, each with its public construction record."
            ),
            canonical=f"{HOST}/leads/opening-2027-2028.html",
            depth=1,
            place=states_phrase(opening_next),
            leads=sort_leads(opening_next),
            updated=updated,
            crumbs='<a href="/index.html">All buildings</a>',
            siblings="States: " + " &middot; ".join(state_links.values()),
            intro_extra=(
                "Opening dates come from the construction record. A building that has not "
                "opened yet has not chosen its operating software, its vendors or its "
                "service contracts."
            ),
        )

    latest_sale_year = max(
        (str(lead["saleDate"])[:4] for lead in all_leads if lead.get("saleDate")),
        default=None,
    )
    if latest_sale_year:
        # The current year is usually part-finished; the completed year is the better list.
        years = sorted({str(l["saleDate"])[:4] for l in all_leads if l.get("saleDate")})
        target = years[-2] if len(years) > 1 else years[-1]
        sold_rows = [l for l in all_leads if l.get("saleDate") and str(l["saleDate"])[:4] == target]
        if len(sold_rows) >= CITY_MIN:
            emit(pages, OUT / f"sold-{target}.html",
                title=f"Apartment Complexes Sold in {target} | CraneSignal",
                h1=f"Apartment complexes that changed owner in {target}",
                description=(
                    f"{len(sold_rows):,} apartment buildings with a recorded {target} sale, "
                    "by city and size, each with the public record of the sale."
                ),
                canonical=f"{HOST}/leads/sold-{target}.html",
                depth=1,
                place=states_phrase(sold_rows),
                leads=sort_leads(sold_rows),
                updated=updated,
                crumbs='<a href="/index.html">All buildings</a>',
                siblings="States: " + " &middot; ".join(state_links.values()),
                sold_view=True,
                intro_extra=(
                    "A building that just changed hands is the most likely to change "
                    "everything else: management, software, suppliers. Buyer names come from "
                    "the county record and are often the holding company, not the operator."
                ),
            )

    return pages


STATIC_START = "    <!-- SEO-STATIC:start (written by tooling/seo/build_pages.py) -->"
STATIC_END = "    <!-- SEO-STATIC:end -->"


def home_static_block(index: dict, areas: list[dict], pages: dict[Path, str]) -> str:
    """Real content and real links inside the home page's app shell.

    `renderShell()` replaces the shell's contents as soon as app.js runs, so a visitor
    never sees this. A crawler that does not run JavaScript sees the only thing it can
    otherwise never find: that the site has data, and where the /leads/ pages are.
    Without it those pages are reachable only from the sitemap, which is a weaker signal
    than a link.
    """
    updated = index.get("updated", "")
    total = sum(int(a.get("leads") or 0) for a in areas)
    units = sum(int(a["payload"].get("stats", {}).get("unitsInPlay") or 0) for a in areas)

    # Ordered the way a reader would want it, not the way the filesystem sorts:
    # states, then the metros inside them, then cities, then the cross-cutting lists.
    def rank(path: Path) -> tuple:
        rel = path.relative_to(SITE).as_posix()
        depth = rel.count("/")
        is_list = depth == 1 and not any(
            rel == f"leads/{a['slug']}.html" for a in areas
        )
        if is_list:
            return (3, rel)
        if depth == 1:
            return (0, rel)
        body = pages[path]
        is_metro = "multifamily construction pipeline" in body
        return (1 if is_metro else 2, rel)

    links = []
    # Pages only. The dict also carries the CSV beside each one, and a spreadsheet is a
    # download rather than somewhere to send a crawler next.
    for path in sorted((p for p in pages if p.suffix == ".html"), key=rank):
        rel = path.relative_to(SITE).as_posix()
        text = re.search(r"<h1>(.*?)</h1>", pages[path], re.S)
        label = text.group(1).strip() if text else rel
        links.append(f'        <li><a href="{rel}">{label}</a></li>')

    # Everything below is computed, never written by hand, so it cannot drift from the data
    # the way a hand-written paragraph would. This block used to be a heading, one sentence
    # and a list of links -- 201 crawler-visible words on the page the sitemap rates 1.0,
    # which is thin for the page everything else points at.
    all_leads = [lead for area in areas for lead in area["payload"].get("leads", [])]
    totals = summarise(all_leads)
    stage_bits = [
        f"{count:,} {stage}" for stage in STAGE_ORDER
        if (count := totals["stages"].get(stage))
    ]
    opening_soon = sum(
        n for year, n in totals["opening_by_year"].items() if year >= str(date.today().year)
    )
    with_phone = sum(1 for lead in all_leads if lead.get("officePhone"))

    per_state = []
    for area in areas:
        stats = area["payload"].get("stats", {})
        sold = sum(1 for lead in area["payload"].get("leads", []) if lead.get("saleDate"))
        per_state.append(
            f"        <li><strong>{esc(area['label'])}</strong>: "
            f"{int(area.get('leads') or 0):,} buildings, "
            f"{int(stats.get('unitsInPlay') or 0):,} units, "
            f"{sold:,} with a recorded sale, across {stats.get('cities', 0)} cities.</li>"
        )

    return "\n".join(
        [
            STATIC_START,
            '    <div class="pre-js-summary">',
            "      <h1>Apartment buildings that are about to need something</h1>",
            f"      <p>CraneSignal tracks {total:,} apartment buildings across "
            # Named, not counted. With one state "across 1 US states" is both ungrammatical
            # and less useful than saying Texas, which is the thing a reader is checking for.
            f"{esc(states_phrase(all_leads))} &mdash; {units:,} units &mdash; that are planned, "
            "permitted, under construction, leasing, or have just changed owner. It is for "
            "people who sell <em>to</em> apartment owners rather than to renters: the "
            "question it answers is which buildings are about to need something, and why "
            f"now. Updated {fmt_date(updated)}.</p>",
            f"      <p>By stage today: {esc(', '.join(stage_bits))}. "
            f"{opening_soon:,} have an expected opening date this year or later and "
            f"{totals['sold']:,} have a recorded sale &mdash; the two moments when a "
            "building reviews its software, its suppliers and its service contracts.</p>",
            "      <h2>What each building carries</h2>",
            "      <p>Where the public record says so: name, street address, city, unit "
            "count, stage, permit date, expected opening date, sale date, buyer, developer "
            f"and office phone &mdash; {with_phone:,} of the {total:,} have a published "
            "office number. Every row names the public record it came from. A blank cell "
            "means that record is silent, never that we guessed, and nothing here is "
            "estimated or modelled.</p>",
            "      <h2>Where it comes from</h2>",
            "      <p>State and city construction records, county appraisal-district sale "
            "records, and public announcements. No proprietary feeds, no purchased lists, "
            "no logins. Some source links open a building&rsquo;s own record; most open the "
            "county or city source it was published in, where the address finds it.</p>",
            "      <h2>Coverage</h2>",
            "      <ul>",
            *per_state,
            "      </ul>",
            "      <h2>Taking the data with you</h2>",
            "      <p>Free, with no account and no key. Every page below has the same list "
            "as a spreadsheet at the same address with <code>.csv</code> instead of "
            "<code>.html</code> &mdash; the complete list for that place, not the capped "
            "set the page itself shows.</p>",
            "      <h2>Browse by place</h2>",
            "      <ul>",
            *links,
            "      </ul>",
            "    </div>",
            STATIC_END,
        ]
    )


def splice_home(index: dict, areas: list[dict], pages: dict[Path, str]) -> tuple[Path, str] | None:
    home = SITE / "index.html"
    text = home.read_text(encoding="utf-8")
    start = text.find(STATIC_START)
    end = text.find(STATIC_END)
    if start == -1 or end == -1:
        raise SystemExit("site/index.html is missing the SEO-STATIC markers")
    block = home_static_block(index, areas, pages)
    updated = text[:start] + block + text[end + len(STATIC_END) :]
    return (home, updated) if updated != text else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    pages = build_all()
    if not pages:
        print("no pages generated -- is site/data/areas populated?", file=sys.stderr)
        return 2

    stale = []
    for path, body in pages.items():
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current != body:
            stale.append(path.relative_to(SITE).as_posix())
            if not args.check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(body, encoding="utf-8", newline="\n")

    # A page whose place no longer clears the threshold must go, or the sitemap will
    # keep pointing at a list that is no longer worth reading. The same applies to its
    # spreadsheet, and doubly so: a CSV left behind after its page went would be a live
    # URL in an old schema serving numbers nothing on the site stands behind any more.
    wanted = set(pages)
    orphans = (
        [p for p in OUT.rglob("*") if p.is_file() and p.suffix in {".html", ".csv"}
         and p not in wanted]
        if OUT.exists() else []
    )
    for path in orphans:
        stale.append("remove " + path.relative_to(SITE).as_posix())
        if not args.check:
            path.unlink()

    index, areas = load_areas()
    spliced = splice_home(index, areas, pages)
    if spliced is not None:
        stale.append("index.html")
        if not args.check:
            spliced[0].write_text(spliced[1], encoding="utf-8", newline="\n")

    if args.check:
        if stale:
            print(f"{len(stale)} page(s) out of date: " + ", ".join(sorted(stale)[:8]), file=sys.stderr)
            return 1
        print(f"{len(pages)} pages up to date")
        return 0

    print(f"wrote {len(pages)} pages ({len(stale)} changed)")
    for path in sorted(pages):
        print("  " + path.relative_to(SITE).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
