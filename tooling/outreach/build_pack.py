#!/usr/bin/env python3
"""Build a one-page sample pack to attach to an outreach email.

The pitch in docs/2026-09-20-maintenance-software-icp.md is "we can give you a few accounts
your sales team should look at for free". This is that "few accounts": a short, checkable
list a vendor can verify in thirty seconds and find true, not a login and not the whole
database. The data is the pitch; everything else is packaging.

Selection is by rule, never by hand, so a second pack for a different vendor is one command
and so the choice is defensible when a reader asks why these buildings. Every row carries the
public record it came from, and a blank cell means the record is silent, not that the value
is zero.

    python3 tooling/outreach/build_pack.py --list
    python3 tooling/outreach/build_pack.py --profile opening-soon
    python3 tooling/outreach/build_pack.py --profile opening-soon --metro Houston --for AppWork
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "site" / "data" / "areas"
OUT = ROOT / "docs" / "outreach" / "packs"
APP = "https://app.cranesignal.com"

# Reuse the SEO builder's text helpers rather than keeping a second copy of the rules for
# shouted county text and date formatting.
_spec = importlib.util.spec_from_file_location(
    "seo_build_pages", ROOT / "tooling" / "seo" / "build_pages.py"
)
_pages = importlib.util.module_from_spec(_spec)
sys.modules["seo_build_pages"] = _pages
_spec.loader.exec_module(_pages)
pretty, fmt_date, fmt_month, esc, clean_city = (
    _pages.pretty, _pages.fmt_date, _pages.fmt_month, _pages.esc, _pages.clean_city
)


def months_ahead(iso: str | None, today: date) -> float | None:
    """How far in the future a date is, in months. None if there is no date."""
    if not iso:
        return None
    try:
        year, month, _ = str(iso)[:10].split("-")
        # A malformed date must not take the whole pack down: the records are public and
        # occasionally messy, and one bad row is not a reason to send nothing.
        return (int(year) - today.year) * 12 + (int(month) - today.month)
    except ValueError:
        return None


# Each profile says who it is for, which buildings it picks and why that is the reason they
# would care. The "why" is printed on the pack: a reader who disagrees with the rule can say
# so, which is more useful than a list they cannot argue with.
PROFILES = {
    "opening-soon": {
        "audience": "vendors who sell to apartment operators before the building opens",
        "headline": "Apartment buildings opening soon that have not chosen their vendors yet",
        "why": (
            "A building that has not opened has not picked its maintenance software, its "
            "service contracts or its suppliers. Once it opens and a system is in place, "
            "the same conversation is a rip-and-replace. These are the ones still deciding."
        ),
        "rule": "opening in the next 21 months, 100 or more units",
        "pick": lambda lead, today: (
            (m := months_ahead(lead.get("openingDate"), today)) is not None
            and 0 < m <= 21
            and int(lead.get("units") or 0) >= 100
        ),
        "sort": lambda lead: str(lead.get("openingDate") or ""),
        "date_label": "Opens",
        "date_of": lambda lead: fmt_month(lead.get("openingDate")),
    },
    "just-sold": {
        "audience": "vendors whose buyer changes when a building changes hands",
        "headline": "Apartment buildings that just changed owner",
        "why": (
            "A new owner reviews everything in the first months: management, software, "
            "suppliers, service contracts. The incumbent relationship is with the seller, "
            "not the buyer."
        ),
        "rule": "a recorded sale in the last 12 months, 100 or more units",
        "pick": lambda lead, today: (
            (m := months_ahead(lead.get("saleDate"), today)) is not None
            and -12 <= m <= 0
            and int(lead.get("units") or 0) >= 100
        ),
        "sort": lambda lead: str(lead.get("saleDate") or ""),
        "reverse": True,
        "date_label": "Sold",
        "date_of": lambda lead: fmt_month(lead.get("saleDate")),
    },
}


def load_leads() -> tuple[list[dict], str]:
    index = json.loads((DATA / "index.json").read_text(encoding="utf-8"))
    leads = []
    for area in index.get("areas", []):
        if area.get("hidden"):
            continue
        path = DATA / f"{area['slug']}.json"
        if not path.exists():
            continue
        for lead in json.loads(path.read_text(encoding="utf-8")).get("leads", []):
            lead["_city"] = clean_city(lead.get("city"))
            lead["_state"] = area["label"]
            leads.append(lead)
    return leads, index.get("updated", "")


def render(rows: list[dict], profile: dict, profile_key: str, updated: str,
           for_whom: str | None, metro: str | None, pool: int) -> str:
    today = date.today().isoformat()
    scope = f" in {metro}" if metro else ""
    intro_for = f" for {for_whom}" if for_whom else ""
    date_label = profile["date_label"]

    body_rows = []
    for lead in rows:
        name = pretty(lead.get("community") or lead.get("property")) or "(unnamed in the record)"
        address = pretty(lead.get("address"))
        if address and address == name:
            address = ""
        sources = [s for s in (lead.get("sources") or []) if s.get("url")]
        link = (
            f'<a href="{esc(sources[0]["url"])}">{esc(sources[0].get("label") or "record")}</a>'
            if sources else ""
        )
        body_rows.append(
            "      <tr>"
            f"<td>{esc(name)}<br><span class=\"addr\">{esc(address)}</span></td>"
            f"<td>{esc(lead.get('_city') or '')}</td>"
            f"<td class=\"num\">{int(lead['units']):,}</td>"
            f"<td>{esc(profile['date_of'](lead))}</td>"
            f"<td>{esc(lead.get('stage') or '')}</td>"
            f"<td>{esc(lead.get('officePhone') or '')}</td>"
            f"<td>{link}</td>"
            "</tr>"
        )

    with_phone = sum(1 for lead in rows if lead.get("officePhone"))
    units = sum(int(lead.get("units") or 0) for lead in rows)

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>{esc(profile['headline'])}{esc(scope)} &mdash; CraneSignal</title>
<style>
  body {{ font: 15px/1.55 -apple-system, "Segoe UI", system-ui, sans-serif; color: #0e1320;
         max-width: 60rem; margin: 0 auto; padding: 32px 22px 56px; }}
  .brand {{ font-weight: 700; color: #1a3d8f; letter-spacing: -0.01em; }}
  h1 {{ font-size: 22px; margin: 6px 0 4px; letter-spacing: -0.01em; }}
  .rule {{ color: #5d6577; font-size: 13px; margin: 0 0 18px; }}
  .why {{ background: #f3f4f6; border-left: 4px solid #f5b700; padding: 12px 16px;
          margin: 0 0 20px; max-width: 62ch; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th, td {{ text-align: left; padding: 7px 8px; border-bottom: 1px solid #d9dce3;
            vertical-align: top; }}
  th {{ font-size: 11px; text-transform: uppercase; letter-spacing: .03em; color: #5d6577; }}
  .num {{ text-align: right; white-space: nowrap; }}
  .addr {{ color: #5d6577; }}
  footer {{ margin-top: 28px; font-size: 13px; color: #343b4c; border-top: 2px solid #1a3d8f;
            padding-top: 14px; }}
  a {{ color: #1a3d8f; }}
  @media print {{ body {{ padding: 0; }} a {{ text-decoration: none; }} }}
</style>
</head>
<body>
<p class="brand">CraneSignal</p>
<h1>{esc(profile['headline'])}{esc(scope)}</h1>
<p class="rule">{len(rows)} of {pool} buildings that match: {esc(profile['rule'])}.
Prepared{esc(intro_for)} on {esc(fmt_date(today))}. Data as of {esc(fmt_date(updated))}.</p>

<div class="why"><strong>Why these.</strong> {esc(profile['why'])}</div>

<table>
  <thead><tr>
    <th>Building</th><th>City</th><th class="num">Units</th>
    <th>{esc(date_label)}</th><th>Stage</th><th>Office phone</th><th>Source</th>
  </tr></thead>
  <tbody>
{chr(10).join(body_rows)}
  </tbody>
</table>

<footer>
<p><strong>{len(rows)} buildings, {units:,} units, {with_phone} with a published office
phone.</strong> Every row links the public record it came from &mdash; state and city permit
records, county appraisal-district sales, and public announcements. A blank cell means the
record is silent on it, not that the value is zero. Nothing here is estimated.</p>
<p>This is a sample. The full list is {pool:,} buildings for this rule alone, and
1,861 in total across every stage, free and with no account at
<a href="{APP}/index.html">app.cranesignal.com</a> &mdash; including the same list as a
spreadsheet. If your team sells somewhere we do not cover yet, ask and we will add it.</p>
</footer>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="opening-soon", choices=sorted(PROFILES))
    parser.add_argument("--metro", help="limit to one metro, e.g. Houston")
    parser.add_argument("--for", dest="for_whom", help="vendor name, printed on the pack")
    parser.add_argument("--limit", type=int, default=15)
    parser.add_argument("--list", action="store_true", help="show the profiles and stop")
    args = parser.parse_args()

    if args.list:
        for key, profile in PROFILES.items():
            print(f"{key:14} {profile['rule']}\n{'':14} for {profile['audience']}\n")
        return 0

    profile = PROFILES[args.profile]
    leads, updated = load_leads()
    today = date.today()

    matched = [lead for lead in leads if profile["pick"](lead, today)]
    if args.metro:
        want = args.metro.lower()
        matched = [
            lead for lead in matched
            if want in (lead.get("metro") or "").lower()
            or want in (lead.get("_city") or "").lower()
        ]
    if not matched:
        print("no buildings match that rule -- try a wider metro or profile", file=sys.stderr)
        return 1

    rows = sorted(matched, key=profile["sort"], reverse=profile.get("reverse", False))
    shown = rows[: args.limit]

    name_bits = [args.profile]
    if args.metro:
        name_bits.append(args.metro.lower().replace(" ", "-"))
    if args.for_whom:
        name_bits.append(args.for_whom.lower().replace(" ", "-"))
    path = OUT / f"{'-'.join(name_bits)}.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        render(shown, profile, args.profile, updated, args.for_whom, args.metro, len(matched)),
        encoding="utf-8", newline="\n",
    )

    with_phone = sum(1 for lead in shown if lead.get("officePhone"))
    print(f"wrote {path.relative_to(ROOT).as_posix()}")
    print(f"  {len(shown)} of {len(matched)} matching buildings, {with_phone} with a phone")
    print("  open it in a browser and print to PDF to attach")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
