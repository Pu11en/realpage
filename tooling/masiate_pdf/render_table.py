#!/usr/bin/env python3
"""Render a PDF-only contact table from the fixed, reviewed Masiate pilot."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from weasyprint import HTML


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "propertystack/data/masiate/pilot-20260920"
REVIEW_PATH = Path(__file__).with_name("table_review.json")
PHONE_PATH = DATA / "masiate-business-phone-update.json"
OUTPUT = DATA / "Masiate-Project-Contractor-Table-With-Phone-Numbers-2026-09-20.pdf"


def esc(value):
    return html.escape(str(value or ""), quote=True)


def safe_url(value):
    parsed = urlparse(str(value or ""))
    return str(value) if parsed.scheme in {"http", "https"} and parsed.netloc else None


def link(url, label):
    href = safe_url(url)
    return f'<a href="{esc(href)}">{esc(label)}</a>' if href else esc(label)


def short_date(value):
    try:
        return date.fromisoformat(value).strftime("%b %d, %Y")
    except (TypeError, ValueError):
        return str(value or "Not recorded")


def has_route(contact):
    return bool(contact.get("phone") or contact.get("email") or safe_url(contact.get("website")))


def build_rows(records, review, phone_update):
    # The editorial notes are specific to the original numbered snapshot, not a live feed.
    expected = list(range(1, 50))
    ranks = [int(record["rank"]) for record in records]
    selected = [rank for section in review["sections"] for rank in section["ranks"]]
    if sorted(ranks) != expected or sorted(selected) != expected:
        raise ValueError("The table must account for all 49 pilot profiles exactly once")
    if len({record["id"] for record in records}) != 49:
        raise ValueError("Duplicate pilot profile IDs")
    by_rank = {record["rank"]: record for record in records}
    expected_names = set(review["construction_contacts"].values())
    if set(phone_update["contacts"]) != expected_names:
        raise ValueError("Phone update must match the nine named construction companies exactly")
    rows = []
    for section_index, section in enumerate(review["sections"]):
        for rank in section["ranks"]:
            record = by_rank[rank]
            key = str(rank)
            contractor_name = review["construction_contacts"].get(key)
            contacts = [dict(c) for c in record.get("business_contacts", [])]
            construction_contact = next((c for c in contacts if c["name"] == contractor_name), None)
            if contractor_name and not construction_contact:
                raise ValueError(f"Missing saved construction contact for profile {rank}")
            if construction_contact:
                update = phone_update["contacts"][contractor_name]
                if not update.get("phone") or not safe_url(update.get("source_url")):
                    raise ValueError("Every phone update requires a public source")
                if update.get("phone_status") not in {"company_published", "association_published", "directory_only"}:
                    raise ValueError("Unknown phone evidence status")
                construction_contact.update(update)
                construction_contact["phone_checked_on"] = phone_update["checked_on"]
            direct = [c for c in contacts if has_route(c)]
            if section_index == 0 and not has_route(construction_contact or {}):
                raise ValueError("First section requires a construction-company contact route")
            if section_index == 1 and not contractor_name:
                raise ValueError("Named-contractor section requires a named construction company")
            if section_index == 2 and (not direct or contractor_name):
                raise ValueError("Engineering section must not imply an appointed builder")
            role = review["special_roles"].get(key)
            if not role:
                role = (f'{contractor_name}: {construction_contact["role"]}.'
                        if construction_contact else "Building contractor not established in saved evidence.")
            # Avoid turning designer names or private-owner details into sales contacts.
            shown_contacts = [construction_contact] if construction_contact else direct
            rows.append({
                "record": record, "section": section_index, "brief": review["briefs"][key][0],
                "fit": review["briefs"][key][1], "role": role,
                "contacts": [c for c in shown_contacts if c],
                "caveat": review["caveats"].get(key, "Confirm current phase, appointed builder and remaining trade work."),
                "has_construction_route": bool(construction_contact and has_route(construction_contact)),
                "has_any_route": bool(direct),
                "provisional_phone": bool(construction_contact and construction_contact.get("phone_status") == "directory_only"),
            })
    return rows


def contacts_html(row):
    blocks = []
    for contact in row["contacts"]:
        if not has_route(contact):
            continue
        bits = [f'<b>{esc(contact["name"])}</b>']
        if not contact.get("phone_kind"):
            bits.append(esc(contact["role"]))
        if contact.get("phone"):
            bits.append(f'<strong class="phone">Phone: {esc(contact["phone"])}</strong>')
            if contact.get("phone_kind"):
                bits.append(esc(contact["phone_kind"]))
        if contact.get("email"):
            bits.append(esc(contact["email"]))
        website = safe_url(contact.get("website"))
        if website:
            bits.append(link(website, urlparse(website).netloc.removeprefix("www.")))
        if safe_url(contact.get("source_url")):
            bits.append(link(contact["source_url"], "Contact evidence"))
        if safe_url(contact.get("email_source_url")):
            bits.append(link(contact["email_source_url"], "Email evidence (2024 form)"))
        blocks.append("<br>".join(bits))
    return "<p>" + "</p><p>".join(blocks) + "</p>" if blocks else (
        "<p>No public business phone, email or website saved for this route.</p>"
    )


def source_label(source, index):
    title = source.get("title", "").lower()
    if "tdlr" in title:
        return "TDLR"
    if "building permits" in title:
        return "City permit list"
    if "cad" in title:
        return "CAD search"
    if "sdrc" in title or "sp26-" in title:
        return "Site plan"
    if "ordinance" in title:
        return "Ordinance"
    if "website" in title or "contact page" in title:
        return "Company site"
    if "dashboard" in title:
        return "City dashboard"
    if "frost" in title:
        return "Bank location"
    return f"Source {index}"


def row_html(row):
    record = row["record"]
    links = [link(source.get("url"), source_label(source, i))
             for i, source in enumerate(record.get("sources", []), 1) if safe_url(source.get("url"))]
    stage = {"permitted": "Permit issued", "planned": "Registration / planning only",
             "construction_reported": "City reports construction underway"}.get(record["stage"], "Status unresolved")
    timing = [f'<b>{esc(stage)}</b>', "Record: " + esc(short_date(record.get("record_date")))]
    if record.get("estimated_start"):
        timing.append("Planned start: " + esc(short_date(record["estimated_start"])))
    if record.get("estimated_completion") and record["rank"] != 30:
        timing.append("Estimated finish: " + esc(short_date(record["estimated_completion"])))
    address = str(record.get("address") or "Address unresolved")
    if record["rank"] == 46:
        address = "Avenue P, Landolt #9 Block 2 west half; 2 acres; street number unknown"
    if record["city"].casefold() not in address.casefold():
        address += ", " + record["city"]
    contact_notes = " ".join(c["contact_note"] for c in row["contacts"] if c.get("contact_note"))
    contact_caveat = f'<p><b>Contact note:</b> {esc(contact_notes)}</p>' if contact_notes else ""
    return f'''<tr data-id="{esc(record['id'])}">
    <td><b>#{record['rank']:02d} {esc(record['project_name'])}</b><p>{esc(address)}<br>{esc(record['county'])} County</p>
    <p class="sources">{' / '.join(links)}</p></td>
    <td>{esc(row['brief'])}<p><b>Possible fit:</b> {esc(row['fit'])}</p></td>
    <td>{esc(row['role'])}</td><td>{contacts_html(row)}</td>
    <td>{'<br>'.join(timing)}<p>{esc(row['caveat'])}</p>{contact_caveat}</td></tr>'''


CSS = '''
@page { size: A4 landscape; margin: 13mm 11mm 15mm;
  @bottom-left { content: "MASIATE | Saved evidence: September 20, 2026 | Need for help unverified"; font: 8pt sans-serif; color: #515b5c; }
  @bottom-right { content: counter(page) " / " counter(pages); font: 8pt sans-serif; color: #515b5c; }
}
* { box-sizing: border-box; }
body { font-family: DejaVu Sans, sans-serif; font-size: 9pt; line-height: 1.32; color: #202b2b; }
h1 { font-size: 25pt; margin: 0 0 6mm; color: #174d46; }
h2 { font-size: 15pt; margin: 0 0 3mm; color: #174d46; }
h3 { font-size: 11pt; margin: 4mm 0 2mm; }
p { margin: 0 0 2mm; }
a { color: #145e83; text-decoration: underline; overflow-wrap: anywhere; }
.eyebrow { font-size: 9pt; margin-bottom: 4mm; color: #606b6b; }
.lead { font-size: 12pt; max-width: 230mm; margin-bottom: 5mm; }
.cover { break-after: page; }
.metrics { width: 100%; margin: 5mm 0; border-collapse: collapse; }
.metrics td { width: 25%; vertical-align: top; font-size: 10pt; padding: 3mm; border-top: 2pt solid #2b7666; }
.metrics b { font-size: 23pt; display: block; color: #174d46; }
.columns { display: flex; gap: 4%; }
.columns > div { width: 48%; flex: none; min-width: 0; }
ul { margin: 1mm 0 3mm; padding-left: 5mm; }
li { margin-bottom: 2mm; }
.notice { padding: 3mm 0; border-top: 1pt solid #a75c28; border-bottom: 1pt solid #a75c28; margin: 4mm 0; }
.section { break-before: page; }
.section-description { margin-bottom: 4mm; }
.grid { table-layout: fixed; border-collapse: collapse; width: 100%; font-size: 9pt; }
.grid th { background: #174d46; color: white; text-align: left; padding: 2.2mm; font-size: 9pt; }
.grid td { vertical-align: top; border: 0.5pt solid #c9d3d1; padding: 2mm; overflow-wrap: anywhere; }
.grid tr:nth-child(even) td { background: #f2f6f5; }
.grid tr { break-inside: avoid; }
thead { display: table-header-group; }
.grid p { margin: 2mm 0 0; }
.grid p:first-child { margin-top: 0; }
.sources { font-size: 8pt; }
.appendix { break-before: page; }
.small { font-size: 8pt; color: #515b5c; }
'''


def render_html(rows, review, summary):
    sections = []
    for index, section in enumerate(review["sections"]):
        section_rows = [row for row in rows if row["section"] == index]
        sections.append(f'''<section class="section"><h2>{esc(section['title'])} ({len(section_rows)})</h2>
        <p class="section-description">{esc(section['description'])}</p>
        <table class="grid"><colgroup><col style="width:20%"><col style="width:19%"><col style="width:17%">
        <col style="width:19%"><col style="width:25%"></colgroup><thead><tr>
        <th>Project / location / sources</th><th>Brief / possible Masiate fit</th><th>Contractor / actual role</th>
        <th>Phone / email / contact</th><th>Timing / what to verify</th></tr></thead>
        <tbody>{''.join(row_html(row) for row in section_rows)}</tbody></table></section>''')
    counties = Counter(row["record"]["county"] for row in rows)
    county_text = "; ".join(f"{county}: {count}" for county, count in sorted(counties.items()))
    construction_routes = sum(row["has_construction_route"] for row in rows)
    all_routes = sum(row["has_any_route"] for row in rows)
    provisional = sum(row["provisional_phone"] for row in rows)
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
    <title>Masiate | Project and Contractor Table</title><style>{CSS}</style></head><body>
    <section class="cover"><p class="eyebrow">CRANESIGNAL RESEARCH / MASIATE CONSTRUCTION / SEPTEMBER 20, 2026 SNAPSHOT</p>
    <h1>Project &amp; Contractor Table</h1>
    <p class="lead">Useful businesses and projects to qualify, not a list of confirmed available jobs.</p>
    <table class="metrics"><tr><td><b>{len(rows)}</b>project profiles</td><td><b>{construction_routes - provisional}</b>company / association-sourced business numbers</td>
    <td><b>{provisional}</b>directory-only number; identity check needed</td><td><b>0</b>confirmed open trade packages</td></tr></table>
    <p class="notice"><b>Phone update:</b> all nine named construction-company prospects now have a published number to check.
    Eight use company or builder-association sources; Valco is directory-only with an unconfirmed project match.
    Masiate can ask about helping with remaining trades. <b>What is not established:</b> whether any of them needs another crew,
    whether each job is active now, or whether Masiate meets project requirements.</p>
    <div class="columns"><div><h3>How the table is organized</h3><ul>
    <li>Three initial construction-company contacts come first, including Collier's unresolved exact project role.</li>
    <li>Six additional named contractors now have phone details; Valco needs identity verification and Atlas is sign/wall scope only.</li>
    <li>Three profiles provide engineer contacts, not confirmed buyers. J4 appears on two different projects.</li>
    <li>Thirty-seven profiles have no established outside building contractor. Unknown does not mean available.</li></ul>
    <h3>A useful first call</h3><p>"We're Masiate Construction. We saw your company listed on [project]. Are you handling that job,
    and do you have any remaining [relevant trade] work? Who handles subcontractor estimates?"</p>
    </div><div><h3>Read the evidence carefully</h3><ul>
    <li><b>Possible fit is our judgment</b> from the described work, not proof that a specific trade package exists.</li>
    <li>Permit issuance is not a verified start. TDLR registration / Review Complete is not a builder award or job completion.</li>
    <li>Scheduled dates are estimates from records. Only AutoZone has saved city evidence explicitly reporting construction underway.</li>
    <li>Construction-company phone sources checked September 20, 2026; no test calls made. Engineering contacts remain from the pilot.</li>
    <li>Row numbers refer to the original 49 profiles, not a sales score. Source links open the supporting public pages.</li></ul>
    <p><b>Coverage:</b> {esc(county_text)}. Research geography does not establish Masiate's travel range.</p></div></div>
    </section>{''.join(sections)}
    <section class="appendix"><h2>What this research can and cannot tell us</h2>
    <div class="columns"><div><h3>Saved projects plus a focused phone lookup</h3><ul>
    <li>{summary['source_records_collected']} source entries collected; these are not unique qualified leads.</li>
    <li>{summary['source_records_linked_to_detailed_profiles']} source entries support the 49 merged profiles, all represented once in this table.</li>
    <li>{summary['source_receipts']} source-coverage checks across seven counties; coverage is incomplete.</li>
    <li>{summary['unreviewed_brazos_records']} additional Brazos registrations were not deeply reviewed.</li>
    <li>Three out-of-area entries were excluded. Three coordinator watchlist demotions were kept out of the 49:
    Lorca (unresolved street address), Iola wastewater plant (expired tender), and Pecan Grove (future agenda).</li>
    <li>Project evidence is unchanged. Public contact pages and a builder-association directory were checked for missing business numbers.
    Valco uses a clearly flagged Houzz listing. No calls, emails, paid tools, new workers or site build were started.</li></ul>
    <h3>Limits that matter before calling</h3><ul>
    <li>Phone/contact routes cover {all_routes} profiles: nine construction-company names (one provisional) and three engineering-contact profiles.
    These are not verified purchasing decision-makers or guaranteed working phone lines.</li>
    <li>CAD links may open a search home page, not a permanent parcel record. A failed CAD match is not evidence of no owner.</li>
    <li>Project costs are intentionally omitted: total building budgets are not Masiate contract values.</li>
    <li>Personal home addresses and private-owner phone numbers are not reproduced. Missing business contact methods are explicit.</li>
    <li>One contractor can already be appointed while still needing subcontractors. Only a current project-specific confirmation can resolve that.</li></ul></div>
    <div><h3>Three smaller jobs checked more closely</h3>
    <p><b>#37 Galaxy Spa:</b> TDLR describes the work, but Bryan's detailed search was inaccessible. Contractor selection remains unknown.
    {link('https://www.tdlr.texas.gov/TABS/Search/Project/TABS2027000633', 'TDLR record')}.</p>
    <p><b>#14 Glo Tanning:</b> tenant-funded fit-out; its own page says coming soon, but does not establish whether construction bids are being accepted.
    No matching permit row was found in the nine posted 2026 College Station workbooks inspected.
    {link('https://www.glotanning.com/location/college-station-tx/', 'Company location page')}.</p>
    <p><b>#12 Barron Suite 204:</b> other units at 2800 Barron have named builders, but none establishes Suite 204's builder.
    Lintz is Unit 102; Keys &amp; Walsh are Units 401-403; Create Construction is Suite 305. Do not transfer those contractors to this row.
    {link('https://www.cstx.gov/media/xyvokjhs/08_august-building-permits-issued.xlsx', 'August permits')};
    {link('https://www.cstx.gov/media/t43fmsag/04_april-building-permits-issued.xlsx', 'April permits')}.</p>
    <p><b>Coverage gap:</b> the available September College Station workbook stopped at September 11, before the September 20 check.
    Detailed eTRAKiT access required a login. Missing permit matches do not prove no builder has been hired.
    {link('https://www.cstx.gov/media/ahjdpwpz/09_september-building-permits-issued.xlsx', 'September permits')};
    {link('https://www.cstx.gov/your-government/departments/planning-development-services-department/building-permits-issued/', 'Monthly report index')}.</p>
    <h3>Bottom line</h3><p>The pilot produced specific projects, nine named construction-company prospects (including one sign contractor),
    now supplemented with eight company/association-sourced numbers and one unconfirmed directory number. It did <b>not</b> establish an available job.
    Use the first rows to ask about real needs, and the unresolved rows to guide further verification.</p>
    </div></div><p class="small">Separate table revision of the September 20 pilot and its three-property follow-up.
    The original report and source records remain unchanged. This table is not a live status feed.</p></section>
    </body></html>'''


def render(output=OUTPUT):
    records_path = DATA / "masiate-reviewed-properties.json"
    records = json.loads(records_path.read_text())
    review = json.loads(REVIEW_PATH.read_text())
    source_hash = hashlib.sha256(records_path.read_bytes()).hexdigest()
    if source_hash != review["source_sha256"]:
        raise ValueError("Pilot snapshot changed; review the numbered editorial notes before rendering")
    summary = json.loads((DATA / "masiate-report-summary.json").read_text())
    rows = build_rows(records, review, json.loads(PHONE_PATH.read_text()))
    document = HTML(string=render_html(rows, review, summary)).render()
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    document.write_pdf(output)
    return {"pdf": str(output), "pages": len(document.pages), "profiles": len(rows),
            "construction_contact_profiles": sum(r["has_construction_route"] for r in rows),
            "all_contact_profiles": sum(r["has_any_route"] for r in rows),
            "source_sha256": source_hash}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    print(json.dumps(render(parser.parse_args().output), indent=2))
