#!/usr/bin/env python3
"""Render the Masiate first-pass reviewed records to a static PDF."""

from __future__ import annotations

import argparse
import html
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from weasyprint import HTML


UNKNOWN = "Unknown"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json_array(path: str | Path) -> list[dict[str, Any]]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    if isinstance(raw, dict):
        for key in ("records", "coverage", "items"):
            value = raw.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    raise ValueError(f"{path} must contain a JSON array or an object with records/coverage/items")


def clean_text(value: Any) -> str:
    if value is None:
        return UNKNOWN
    if isinstance(value, (list, tuple)):
        parts = [clean_text(item) for item in value if clean_text(item) != UNKNOWN]
        return "; ".join(parts) if parts else UNKNOWN
    text = str(value).strip()
    return text if text else UNKNOWN


def clean_text_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        values = [values] if values is not None else []
    cleaned = []
    for item in values:
        text = clean_text(item)
        if text != UNKNOWN:
            cleaned.append(text)
    return cleaned


def esc(value: Any) -> str:
    return html.escape(clean_text(value), quote=True)


def safe_href(value: Any) -> str | None:
    text = clean_text(value)
    parsed = urlparse(text)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return text
    return None


def display_url(value: Any, limit: int = 96) -> str:
    text = clean_text(value)
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "..."


def source_items(record: dict[str, Any]) -> list[str]:
    items = []
    for source in record.get("sources") or []:
        if not isinstance(source, dict):
            continue
        href = safe_href(source.get("url"))
        title = source.get("title") or source.get("url") or "Source"
        date = source.get("date")
        page = source.get("page")
        evidence = source.get("evidence")
        bits = [f"<strong>{esc(title)}</strong>"]
        if date:
            bits.append(esc(date))
        if page:
            bits.append(f"page/section: {esc(page)}")
        if href:
            label = esc(display_url(href))
            bits.append(f'<a href="{html.escape(href, quote=True)}">{label}</a>')
        else:
            bits.append("source URL unavailable")
        if evidence:
            bits.append(esc(evidence))
        items.append("<li>" + " | ".join(bits) + "</li>")
    return items or ["<li>No public source link supplied.</li>"]


def public_evidence_checked(record: dict[str, Any]) -> str:
    public = []
    private_count = 0
    for item in clean_text_list(record.get("evidence_checked")):
        href = safe_href(item)
        if href:
            public.append(href)
        else:
            private_count += 1
    if private_count:
        public.append(f"{private_count} local evidence file path(s) checked and omitted from public PDF")
    return "; ".join(public) if public else UNKNOWN


def participants(record: dict[str, Any]) -> str:
    rows = []
    for person in record.get("participants") or []:
        if not isinstance(person, dict):
            continue
        rows.append(f"{esc(person.get('name'))} ({esc(person.get('role'))})")
    return "; ".join(rows) if rows else UNKNOWN


def business_contacts(record: dict[str, Any]) -> str:
    rows = []
    for contact in record.get("business_contacts") or []:
        if not isinstance(contact, dict):
            continue
        name = esc(contact.get("name"))
        role = esc(contact.get("role"))
        website = safe_href(contact.get("website"))
        if website:
            rows.append(f'{name} ({role}) - <a href="{html.escape(website, quote=True)}">{esc(display_url(website))}</a>')
        else:
            rows.append(f"{name} ({role})")
    return "; ".join(rows) if rows else UNKNOWN


def include_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [record for record in records if clean_text(record.get("review_decision")).lower() == "include"]


def watchlist_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [record for record in records if clean_text(record.get("review_decision")).lower() == "watchlist"]


def record_card(record: dict[str, Any], index: int) -> str:
    bid = record.get("bid_deadline")
    stage = clean_text(record.get("stage"))
    if bid:
        availability = f"Bid/status evidence: deadline {esc(bid)}."
    elif stage == "open_bid":
        availability = "Bid/status evidence: source marks this as open bid, but no deadline was supplied."
    else:
        availability = "Work availability: unknown unless the cited source explicitly states an open bid/status."
    corrections = clean_text_list(record.get("corrections"))
    member_ids = clean_text_list(record.get("member_ids")) or clean_text_list(record.get("id") or record.get("source_record_id"))
    unknowns = clean_text_list(record.get("unknowns"))
    return f"""
    <article class="profile">
      <h3>{index}. {esc(record.get("project_name"))}</h3>
      <p class="meta">{esc(record.get("county"))} County | {esc(record.get("record_type"))} | record date {esc(record.get("record_date"))} | stage {esc(stage)}</p>
      <dl>
        <dt>Location</dt><dd>{esc(record.get("address"))}, {esc(record.get("city"))}</dd>
        <dt>Scope</dt><dd>{esc(record.get("scope"))}</dd>
        <dt>Masiate fit</dt><dd>{esc(record.get("masiate_fit"))}</dd>
        <dt>Priority reason</dt><dd>{esc(record.get("priority_reason"))}</dd>
        <dt>Status basis</dt><dd>{esc(record.get("status_basis"))}</dd>
        <dt>Availability</dt><dd>{availability}</dd>
        <dt>Value</dt><dd>{esc(record.get("estimated_value"))} <span class="quiet">Whole-project value is not Masiate contract value.</span></dd>
        <dt>Dates</dt><dd>Start: {esc(record.get("estimated_start"))}; Completion: {esc(record.get("estimated_completion"))}; Bid deadline: {esc(record.get("bid_deadline"))}</dd>
        <dt>Participants</dt><dd>{participants(record)}</dd>
        <dt>Verified business contacts</dt><dd>{business_contacts(record)}</dd>
        <dt>Unknowns</dt><dd>{esc(unknowns)}</dd>
        <dt>Corrections</dt><dd>{esc(corrections)}</dd>
        <dt>Member IDs</dt><dd>{esc(member_ids)}</dd>
        <dt>Evidence checked</dt><dd>{esc(public_evidence_checked(record))}</dd>
      </dl>
      <h4>Public Sources</h4>
      <ul class="sources">{''.join(source_items(record))}</ul>
    </article>
    """


def watchlist_section(records: list[dict[str, Any]]) -> str:
    if not records:
        return "<p>No watchlist records were supplied.</p>"
    items = []
    for record in records:
        items.append(
            "<li>"
            f"<strong>{esc(record.get('project_name'))}</strong> | {esc(record.get('county'))} County | "
            f"{esc(record.get('priority_reason'))} | {esc(record.get('status_basis'))}"
            "</li>"
        )
    return "<ul>" + "".join(items) + "</ul>"


def coverage_section(coverage: list[dict[str, Any]]) -> str:
    if not coverage:
        return "<p>No coverage file was supplied. Coverage gaps remain unknown.</p>"
    by_county: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in coverage:
        by_county[clean_text(item.get("county"))].append(item)
    chunks = []
    for county in sorted(by_county):
        rows = []
        for item in by_county[county]:
            rows.append(
                "<li>"
                f"<strong>{esc(item.get('name'))}</strong>: {esc(item.get('status'))}; "
                f"covered {esc(item.get('covered_from'))} to {esc(item.get('covered_to'))}; "
                f"records found {esc(item.get('records_found'))}. "
                f"{esc(item.get('reason'))} "
                f"<span class=\"quiet\">Next: {esc(item.get('next_cursor'))}</span>"
                "</li>"
            )
        chunks.append(f"<h3>{esc(county)} County</h3><ul>{''.join(rows)}</ul>")
    return "".join(chunks)


def render_html(records: list[dict[str, Any]], coverage: list[dict[str, Any]], title: str) -> str:
    included = include_records(records)
    watchlist = watchlist_records(records)
    decision_counts = Counter(clean_text(record.get("review_decision")).lower() for record in records)
    county_counts = Counter(clean_text(record.get("county")) for record in included)
    generated_at = utc_now()
    profile_html = (
        "".join(record_card(record, idx + 1) for idx, record in enumerate(included))
        if included
        else "<div class=\"empty\"><strong>No detailed include records supplied yet.</strong><br />This QA draft is ready for reviewed records once the reviewer JSON files arrive.</div>"
    )
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>{esc(title)}</title>
  <style>
    @page {{
      size: Letter;
      margin: 0.65in;
      @bottom-right {{ content: "Page " counter(page) " of " counter(pages); color: #667085; font-size: 9px; }}
    }}
    * {{ box-sizing: border-box; }}
    body {{ font-family: "DejaVu Sans", Arial, sans-serif; color: #182230; font-size: 10.5px; line-height: 1.42; }}
    h1 {{ font-size: 22px; margin: 0 0 8px; color: #0b2f36; }}
    h2 {{ font-size: 15px; margin: 24px 0 8px; padding-top: 8px; border-top: 1px solid #d0d5dd; color: #12434a; }}
    h3 {{ font-size: 12px; margin: 14px 0 5px; color: #101828; }}
    h4 {{ font-size: 10.5px; margin: 9px 0 4px; color: #344054; }}
    a {{ color: #175cd3; text-decoration: none; overflow-wrap: anywhere; }}
    .subtitle {{ color: #475467; margin-bottom: 14px; }}
    .summary {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin: 14px 0; }}
    .metric {{ border: 1px solid #d0d5dd; border-radius: 4px; padding: 8px; background: #f8fafc; }}
    .metric strong {{ display: block; font-size: 15px; color: #0b2f36; }}
    .notice {{ border-left: 4px solid #b54708; background: #fffaeb; padding: 8px 10px; margin: 12px 0; }}
    .empty {{ border: 1px dashed #98a2b3; background: #f9fafb; padding: 12px; margin: 10px 0; }}
    .profile {{ break-inside: avoid; border-top: 1px solid #eaecf0; padding-top: 10px; margin-top: 10px; }}
    .meta, .quiet {{ color: #667085; }}
    dl {{ display: grid; grid-template-columns: 1.45in 1fr; gap: 4px 10px; margin: 8px 0; }}
    dt {{ font-weight: 700; color: #344054; }}
    dd {{ margin: 0; overflow-wrap: anywhere; }}
    ul {{ margin: 5px 0 10px 18px; padding: 0; }}
    li {{ margin-bottom: 4px; overflow-wrap: anywhere; }}
    .sources li {{ font-size: 9.5px; }}
  </style>
</head>
<body>
  <h1>{esc(title)}</h1>
  <p class="subtitle">QA draft generated {esc(generated_at)} from reviewed JSON inputs. This is first-pass property research, not a final sales list.</p>
  <div class="notice">
    Source evidence can support property identity, location, scope, planning stage, permit status or bid status only as stated.
    Private homeowner contact details and local evidence file paths are intentionally omitted.
  </div>
  <section>
    <h2>First-Pass Scope And Counts</h2>
    <div class="summary">
      <div class="metric"><strong>{len(records)}</strong>Total reviewed records supplied</div>
      <div class="metric"><strong>{len(included)}</strong>Detailed include profiles</div>
      <div class="metric"><strong>{len(watchlist)}</strong>Watchlist records</div>
      <div class="metric"><strong>{len(coverage)}</strong>Coverage entries supplied</div>
    </div>
    <p>Review decisions: {esc(dict(sorted(decision_counts.items())))}.</p>
    <p>Included records by county: {esc(dict(sorted(county_counts.items())))}.</p>
  </section>
  <section>
    <h2>Detailed Property Profiles</h2>
    {profile_html}
  </section>
  <section>
    <h2>Watchlist</h2>
    {watchlist_section(watchlist)}
  </section>
  <section>
    <h2>County Coverage And Gaps</h2>
    {coverage_section(coverage)}
  </section>
  <section>
    <h2>Limitations</h2>
    <ul>
      <li>Unknown fields mean the reviewed input did not supply a source-backed value.</li>
      <li>Planning, registration and permit records are not proof that trade packages remain open.</li>
      <li>Whole-project budget or accessibility-registration cost is not Masiate contract value.</li>
      <li>Only records marked review_decision=include are rendered as detailed primary profiles.</li>
    </ul>
  </section>
</body>
</html>
"""


def render_pdf(records: list[dict[str, Any]], coverage: list[dict[str, Any]], output: str | Path, title: str) -> None:
    html_text = render_html(records, coverage, title)
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    HTML(string=html_text).write_pdf(str(output))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render Masiate reviewed records to PDF.")
    parser.add_argument("--records", action="append", required=True, help="Reviewed records JSON array. May be repeated.")
    parser.add_argument("--coverage", action="append", required=True, help="Coverage JSON array. May be repeated.")
    parser.add_argument("--output", required=True, help="Output PDF path.")
    parser.add_argument("--title", required=True, help="PDF title.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    records: list[dict[str, Any]] = []
    coverage: list[dict[str, Any]] = []
    for path in args.records:
        records.extend(load_json_array(path))
    for path in args.coverage:
        coverage.extend(load_json_array(path))
    render_pdf(records, coverage, args.output, args.title)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
