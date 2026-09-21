#!/usr/bin/env python3
"""Render the fixed 49-property Masiate snapshot with researched contact routes."""

from __future__ import annotations

import argparse
import hashlib
import html
import importlib.util
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from weasyprint import HTML


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "propertystack/data/masiate/pilot-20260920"
RESEARCH_DIR = DATA / "contact-research"
REVIEW_PATH = Path(__file__).with_name("table_review.json")
OUTPUT = DATA / "Masiate-All-Property-Contacts-2026-09-20.pdf"
SUMMARY_OUTPUT = DATA / "masiate-all-property-contact-summary.json"


def _load_coverage_module():
    path = Path(__file__).with_name("contact_coverage.py")
    spec = importlib.util.spec_from_file_location("masiate_contact_coverage_for_pdf", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def safe_url(value: Any) -> str | None:
    parsed = urlparse(str(value or ""))
    return str(value) if parsed.scheme in {"http", "https"} and parsed.netloc else None


def link(url: Any, label: str) -> str:
    href = safe_url(url)
    return f'<a href="{esc(href)}">{esc(label)}</a>' if href else esc(label)


def short_date(value: Any) -> str:
    try:
        return date.fromisoformat(str(value)).strftime("%b %d, %Y")
    except (TypeError, ValueError):
        return str(value or "Not recorded")


def load_research() -> tuple[dict[str, Any], list[dict[str, Any]], Any]:
    coverage = _load_coverage_module()
    manifest = load_json(coverage.MANIFEST_PATH)
    documents = coverage.load_result_documents(RESEARCH_DIR)
    report = coverage.validate_coverage(manifest, documents, require_complete=True)
    if not report.complete:
        detail = "; ".join(report.errors) or "coverage is incomplete"
        raise ValueError(f"Contact research failed the final coverage gate: {detail}")
    return manifest, documents, report


def _role_groups(review: dict[str, Any]) -> dict[int, str]:
    groups: dict[int, str] = {}
    for group_id, group in review["contact_role_groups"].items():
        for rank in group["ranks"]:
            if rank in groups:
                raise ValueError(f"Rank {rank} appears in more than one contact role group")
            groups[rank] = group_id
    if sorted(groups) != list(range(1, 50)):
        raise ValueError("Contact role groups must cover ranks 1-49 exactly once")
    return groups


def build_rows(
    records: list[dict[str, Any]],
    review: dict[str, Any],
    manifest: dict[str, Any],
    documents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Merge immutable project records with the validated all-row contact ledger."""
    expected = list(range(1, 50))
    ranks = [int(record["rank"]) for record in records]
    selected_ranks = [rank for section in review["sections"] for rank in section["ranks"]]
    if sorted(ranks) != expected or sorted(selected_ranks) != expected:
        raise ValueError("The table must account for all 49 pilot profiles exactly once")
    if len({record["id"] for record in records}) != 49:
        raise ValueError("Duplicate pilot profile IDs")
    records_hash = hashlib.sha256((DATA / "masiate-reviewed-properties.json").read_bytes()).hexdigest()
    if manifest.get("source_records_sha256") != records_hash:
        raise ValueError("Contact manifest does not match the immutable pilot snapshot")

    by_rank = {int(record["rank"]): record for record in records}
    research_results = [result for document in documents for result in document["properties"]]
    by_id = {result["property_id"]: result for result in research_results}
    if len(research_results) != 49 or len(by_id) != 49:
        raise ValueError("Contact research must contain 49 unique property results")

    group_for_rank = _role_groups(review)
    section_for_rank = {
        rank: section_index
        for section_index, section in enumerate(review["sections"])
        for rank in section["ranks"]
    }
    rows = []
    for rank in expected:
        record = by_rank[rank]
        result = by_id.get(record["id"])
        if not result or result.get("rank") != rank or result.get("research_status") != "researched":
            raise ValueError(f"Missing researched result for profile {rank}")
        contacts_by_id = {contact["route_id"]: dict(contact) for contact in result["contacts"]}
        selected_id = result.get("selected_route_id")
        selected = contacts_by_id.get(selected_id) if selected_id else None
        alternatives = [contacts_by_id[route_id] for route_id in result.get("alternative_route_ids", [])]
        if not selected and not result.get("researched_gap"):
            raise ValueError(f"Profile {rank} needs a selected phone or researched gap")
        rows.append(
            {
                "record": record,
                "result": result,
                "section": section_for_rank[rank],
                "brief": review["briefs"][str(rank)][0],
                "fit": review["briefs"][str(rank)][1],
                "caveat": review["caveats"].get(
                    str(rank), "Confirm current phase, appointed builder and remaining trade work."
                ),
                "selected": selected,
                "alternatives": alternatives,
                "role_group": group_for_rank[rank],
                "provisional": bool(selected and selected.get("source_strength") == "provisional"),
            }
        )
    return rows


def source_label(source: dict[str, Any], index: int) -> str:
    title = str(source.get("title", "")).lower()
    if "tdlr" in title:
        return "TDLR project"
    if "building permits" in title:
        return "City permits"
    if "cad" in title:
        return "CAD search"
    if "sdrc" in title or "sp26-" in title:
        return "Site plan"
    if "ordinance" in title:
        return "Ordinance"
    if "dashboard" in title:
        return "City dashboard"
    return f"Project source {index}"


def contact_html(contact: dict[str, Any], *, selected: bool) -> str:
    status = "BEST-GUESS / VERIFY IDENTITY" if contact.get("source_strength") == "provisional" else (
        "SELECTED ROUTE" if selected else "ALTERNATIVE ROUTE"
    )
    status_class = " provisional" if contact.get("source_strength") == "provisional" else ""
    bits = [
        f'<span class="badge{status_class}">{esc(status)}</span>',
        f'<b>{esc(contact["contact_name"])}</b>',
        f'<span class="role">{esc(contact["role"])}</span>',
    ]
    if contact.get("phone"):
        bits.append(f'<strong class="phone">{esc(contact["phone"])}</strong>')
    if contact.get("email"):
        bits.append(f'Email: {esc(contact["email"])}')
    if safe_url(contact.get("website")):
        host = urlparse(contact["website"]).netloc.removeprefix("www.")
        bits.append(link(contact["website"], host))
    source_type = str(contact.get("source_type", "source")).replace("_", " ")
    bits.append(
        link(contact.get("source_url"), f"{source_type.title()} evidence")
        + f" · Checked {esc(short_date(contact.get('checked_on')))}"
    )
    return "<br>".join(bits)


def selected_route_html(row: dict[str, Any]) -> str:
    if row["selected"]:
        return contact_html(row["selected"], selected=True)
    gap = row["result"]["researched_gap"]
    return (
        '<span class="badge gap">NO SUITABLE PUBLIC NUMBER</span><br>'
        + esc(gap["explanation"])
        + f'<br><span class="checked">Checked {esc(short_date(gap["checked_on"]))}</span>'
    )


def alternatives_html(row: dict[str, Any]) -> str:
    if not row["alternatives"]:
        return '<span class="muted">No additional route selected.</span>'
    return '<div class="alternative">' + '</div><div class="alternative">'.join(
        contact_html(contact, selected=False) for contact in row["alternatives"]
    ) + "</div>"


def row_html(row: dict[str, Any]) -> str:
    record = row["record"]
    project_links = [
        link(source.get("url"), source_label(source, index))
        for index, source in enumerate(record.get("sources", []), 1)
        if safe_url(source.get("url"))
    ]
    stage = {
        "permitted": "Permit issued",
        "planned": "Registration / planning only",
        "construction_reported": "City reports construction underway",
    }.get(record["stage"], "Status unresolved")
    timing = [f"<b>{esc(stage)}</b>", "Project record: " + esc(short_date(record.get("record_date")))]
    if record.get("estimated_start"):
        timing.append("Planned start: " + esc(short_date(record["estimated_start"])))
    if record.get("estimated_completion") and record["rank"] != 30:
        timing.append("Estimated finish: " + esc(short_date(record["estimated_completion"])))
    address = str(record.get("address") or "Address unresolved")
    if record["rank"] == 46:
        address = "Avenue P, Landolt #9 Block 2 west half; 2 acres; street number unknown"
    if record["city"].casefold() not in address.casefold():
        address += ", " + record["city"]
    return f'''<tr data-id="{esc(record['id'])}">
    <td><b>#{record['rank']:02d} {esc(record['project_name'])}</b><p>{esc(address)}<br>{esc(record['county'])} County</p>
    <p class="sources">{' / '.join(project_links)}</p></td>
    <td>{esc(row['brief'])}<p><b>Possible fit:</b> {esc(row['fit'])}</p><p>{'<br>'.join(timing)}</p></td>
    <td>{selected_route_html(row)}</td><td>{alternatives_html(row)}</td>
    <td><b>Before calling:</b> {esc(row['caveat'])}</td></tr>'''


CSS = '''
@page { size: A4 landscape; margin: 11mm 9mm 14mm;
  @bottom-left { content: "MASIATE | Projects saved Sep. 20, 2026 | Contacts checked Sep. 20, 2026 | Need unverified"; font: 7.5pt sans-serif; color: #515b5c; }
  @bottom-right { content: counter(page) " / " counter(pages); font: 7.5pt sans-serif; color: #515b5c; }
}
* { box-sizing: border-box; }
body { font-family: DejaVu Sans, sans-serif; font-size: 8.1pt; line-height: 1.27; color: #202b2b; }
h1 { font-size: 24pt; margin: 0 0 5mm; color: #174d46; }
h2 { font-size: 14pt; margin: 0 0 3mm; color: #174d46; }
h3 { font-size: 10.5pt; margin: 3mm 0 1.5mm; }
p { margin: 0 0 1.6mm; }
a { color: #145e83; text-decoration: underline; overflow-wrap: anywhere; }
.eyebrow { font-size: 8.5pt; margin-bottom: 3mm; color: #606b6b; }
.lead { font-size: 11.5pt; max-width: 235mm; margin-bottom: 4mm; }
.cover { break-after: page; }
.metrics { width: 100%; margin: 4mm 0; border-collapse: collapse; }
.metrics td { width: 20%; vertical-align: top; font-size: 9pt; padding: 2.5mm; border-top: 2pt solid #2b7666; }
.metrics b { font-size: 21pt; display: block; color: #174d46; }
.columns { display: flex; gap: 4%; }
.columns > div { width: 48%; flex: none; min-width: 0; }
ul { margin: 1mm 0 2mm; padding-left: 5mm; }
li { margin-bottom: 1.4mm; }
.notice { padding: 2.5mm 0; border-top: 1pt solid #a75c28; border-bottom: 1pt solid #a75c28; margin: 3mm 0; }
.section { break-before: page; }
.section-description { margin-bottom: 3mm; }
.grid { table-layout: fixed; border-collapse: collapse; width: 100%; font-size: 7.7pt; }
.grid th { background: #174d46; color: white; text-align: left; padding: 2mm; font-size: 8pt; }
.grid td { vertical-align: top; border: 0.5pt solid #c9d3d1; padding: 1.7mm; overflow-wrap: anywhere; }
.grid tr:nth-child(even) td { background: #f2f6f5; }
.grid tr { break-inside: avoid; }
thead { display: table-header-group; }
.grid p { margin: 1.5mm 0 0; }
.sources { font-size: 7.1pt; }
.phone { display: block; font-size: 11.5pt; line-height: 1.2; color: #0d493f; letter-spacing: 0.15pt; margin: 0.6mm 0; }
.role { font-style: italic; }
.badge { display: inline-block; font-size: 6.5pt; font-weight: bold; letter-spacing: 0.2pt; color: #fff; background: #2b7666; padding: 0.6mm 1mm; margin-bottom: 0.8mm; }
.badge.provisional { background: #a75c28; }
.badge.gap { background: #7a3333; }
.alternative + .alternative { border-top: 0.5pt solid #c9d3d1; padding-top: 1.4mm; margin-top: 1.4mm; }
.muted, .checked { color: #606b6b; }
.appendix { break-before: page; }
.small { font-size: 7.5pt; color: #515b5c; }
'''


def coverage_summary(rows: list[dict[str, Any]], review: dict[str, Any]) -> dict[str, Any]:
    selected = [row["selected"] for row in rows if row["selected"]]
    role_counts = Counter(row["role_group"] for row in rows)
    checked_dates = sorted({contact["checked_on"] for contact in selected})
    return {
        "snapshot_date": "2026-09-20",
        "contact_checked_dates": checked_dates,
        "property_rows": len(rows),
        "researched_rows": sum(row["result"]["research_status"] == "researched" for row in rows),
        "confirmed_strong_routes": sum(contact["source_strength"] == "strong" for contact in selected),
        "provisional_best_guess_routes": sum(contact["source_strength"] == "provisional" for contact in selected),
        "researched_no_number_gaps": sum(row["selected"] is None for row in rows),
        "distinct_selected_contact_names": len({contact["contact_name"] for contact in selected}),
        "distinct_selected_phone_numbers": len({contact["phone"] for contact in selected}),
        "role_category_counts": {
            group_id: {
                "label": review["contact_role_groups"][group_id]["label"],
                "rows": role_counts[group_id],
            }
            for group_id in review["contact_role_groups"]
        },
    }


def render_html(rows: list[dict[str, Any]], review: dict[str, Any], summary: dict[str, Any]) -> str:
    sections = []
    for index, section in enumerate(review["sections"]):
        section_rows = [row for row in rows if row["section"] == index]
        sections.append(f'''<section class="section"><h2>{esc(section['title'])} ({len(section_rows)})</h2>
        <p class="section-description">{esc(section['description'])}</p>
        <table class="grid"><colgroup><col style="width:19%"><col style="width:20%"><col style="width:23%">
        <col style="width:22%"><col style="width:16%"></colgroup><thead><tr>
        <th>Project / location / evidence</th><th>Scope / timing</th><th>Best public business route</th>
        <th>Useful alternative route(s)</th><th>What to verify</th></tr></thead>
        <tbody>{''.join(row_html(row) for row in section_rows)}</tbody></table></section>''')
    counties = Counter(row["record"]["county"] for row in rows)
    county_text = "; ".join(f"{county}: {count}" for county, count in sorted(counties.items()))
    role_lines = "".join(
        f'<li><b>{group["rows"]}</b> {esc(group["label"])}</li>'
        for group in summary["role_category_counts"].values()
    )
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
    <title>Masiate | All Property Contacts</title><style>{CSS}</style></head><body>
    <section class="cover"><p class="eyebrow">CRANESIGNAL RESEARCH / MASIATE CONSTRUCTION / ORIGINAL SEPTEMBER 20, 2026 PROJECT SNAPSHOT</p>
    <h1>All 49 Property Contacts</h1>
    <p class="lead">Every saved property now has a sourced public business phone route, labeled by who it belongs to. These are routes for qualification—not proof of open work, an awarded role, or a purchasing decision-maker.</p>
    <table class="metrics"><tr><td><b>{summary['property_rows']}</b>property rows researched</td>
    <td><b>{summary['confirmed_strong_routes']}</b>confirmed / strong routes</td>
    <td><b>{summary['provisional_best_guess_routes']}</b>best-guess routes to verify</td>
    <td><b>{summary['researched_no_number_gaps']}</b>rows without a suitable number</td>
    <td><b>0</b>confirmed open trade packages</td></tr></table>
    <p class="notice"><b>Two dates, two meanings:</b> project facts are the saved September 20, 2026 snapshot. Contact routes were checked September 20, 2026. No test calls were made, so publication does not prove a number still connects.</p>
    <div class="columns"><div><h3>Who the selected numbers reach</h3><ul>{role_lines}</ul>
    <p>Counts describe rows, not unique people or phone numbers. The 49 rows contain {summary['distinct_selected_contact_names']} distinct selected contact names and {summary['distinct_selected_phone_numbers']} distinct selected numbers.</p>
    <h3>How to use each row</h3><ul><li>Start with the large number in “Best public business route.”</li>
    <li>Read the role before calling; designers, engineers, owners, tenants, institutions and routing offices are clearly labeled.</li>
    <li>Use alternatives when the best route cannot answer who manages construction or remaining trade work.</li></ul></div>
    <div><h3>Evidence rules used</h3><ul><li>Strong routes use official company, institution, association or government sources with a confirmed entity match.</li>
    <li>Best-guess routes are kept separate and visibly flagged; they must not be counted as confirmed.</li>
    <li>Project links support the saved project. Contact-evidence links support the displayed route; they are not interchangeable.</li>
    <li>Consumer order lines, unrelated stores, fax numbers and private-owner numbers were excluded.</li></ul>
    <h3>Important limits</h3><ul><li>Permit or planning status does not prove work is active or available.</li>
    <li>A public business number is not necessarily a direct project manager.</li>
    <li>Possible fit is a research judgment, not a verified trade package.</li></ul>
    <p><b>Coverage:</b> {esc(county_text)}.</p></div></div></section>
    {''.join(sections)}
    <section class="appendix"><h2>Coverage and unresolved verification</h2>
    <div class="columns"><div><h3>Complete row coverage</h3><ul>
    <li>All 49 immutable property IDs appear exactly once.</li>
    <li>{summary['confirmed_strong_routes']} rows have a confirmed/strong selected phone route.</li>
    <li>{summary['provisional_best_guess_routes']} rows use a provisional selected phone route.</li>
    <li>{summary['researched_no_number_gaps']} rows end without a suitable public number.</li>
    <li>All original linked sources were given a recorded research disposition in the repository ledger.</li></ul>
    <h3>Best-guess routes</h3><p><b>#05 Brennan Taylor Developments:</b> the phone is a provisional exact-name/location business match; confirm that this Louisiana entity is the permit actor before relying on it.</p>
    <p><b>#33 Valco Builders:</b> the number is directory-sourced and the exact project/company identity is not confirmed. The City permit-routing office is included as an alternative.</p></div>
    <div><h3>Role cautions that matter</h3><ul><li><b>#04 Atlas:</b> the saved contractor is for sign/wall scope, not the parking work; the selected route is the church owner/applicant.</li>
    <li><b>#12 Barron Suite 204:</b> builders from other suites were not transferred; the accessibility specialist is a fallback route.</li>
    <li><b>#14 Glo:</b> tenant-funded does not mean landlord-bought; the selected route is the listed designer.</li>
    <li><b>#36, #38 and #39:</b> developer/engineer routes are not appointed builders. Tabor plans remain interim and not for bidding or construction.</li>
    <li><b>#42:</b> Lay is a project representative/design firm, not a confirmed building contractor.</li>
    <li><b>#46:</b> the City of Somerville is an approving-jurisdiction routing office because no safely matched Altura Capital number was established.</li></ul>
    <h3>Bottom line</h3><p>This revision completes contact research for the original 49-property snapshot without changing the original property JSON or any earlier PDF. The table is for careful qualification only; no outreach was performed.</p></div></div>
    <p class="small">Generated from the four validated contact-research batches. Older Masiate PDFs remain separate and unchanged.</p></section>
    </body></html>'''


def merged_summary_document(rows: list[dict[str, Any]], summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": "Masiate all-property contact coverage summary",
        **summary,
        "properties": [
            {
                "property_id": row["record"]["id"],
                "rank": row["record"]["rank"],
                "project_name": row["record"]["project_name"],
                "role_category": row["role_group"],
                "selected_route": row["selected"],
                "alternative_routes": row["alternatives"],
                "researched_gap": row["result"].get("researched_gap"),
            }
            for row in rows
        ],
    }


def render(output: Path = OUTPUT, summary_output: Path = SUMMARY_OUTPUT) -> dict[str, Any]:
    records_path = DATA / "masiate-reviewed-properties.json"
    records = load_json(records_path)
    review = load_json(REVIEW_PATH)
    source_hash = hashlib.sha256(records_path.read_bytes()).hexdigest()
    if source_hash != review["source_sha256"]:
        raise ValueError("Pilot snapshot changed; review the numbered editorial notes before rendering")
    manifest, documents, report = load_research()
    rows = build_rows(records, review, manifest, documents)
    summary = coverage_summary(rows, review)
    if (
        summary["researched_rows"] != report.researched_count
        or summary["confirmed_strong_routes"] != report.confirmed_phone_count
        or summary["provisional_best_guess_routes"] != report.provisional_phone_count
        or summary["researched_no_number_gaps"] != report.researched_gap_count
    ):
        raise ValueError("Renderer coverage counts disagree with the validated ledger")
    document = HTML(string=render_html(rows, review, summary)).render()
    output = Path(output)
    summary_output = Path(summary_output)
    output.parent.mkdir(parents=True, exist_ok=True)
    summary_output.parent.mkdir(parents=True, exist_ok=True)
    document.write_pdf(output)
    summary_output.write_text(
        json.dumps(merged_summary_document(rows, summary), indent=2) + "\n", encoding="utf-8"
    )
    return {
        "pdf": str(output),
        "summary": str(summary_output),
        "pages": len(document.pages),
        "profiles": len(rows),
        "confirmed_strong_routes": summary["confirmed_strong_routes"],
        "provisional_best_guess_routes": summary["provisional_best_guess_routes"],
        "researched_no_number_gaps": summary["researched_no_number_gaps"],
        "source_sha256": source_hash,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--summary-output", type=Path, default=SUMMARY_OUTPUT)
    args = parser.parse_args()
    print(json.dumps(render(args.output, args.summary_output), indent=2))
