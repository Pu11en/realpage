from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from pypdf import PdfReader


MODULE_PATH = Path(__file__).resolve().parents[4] / "tooling" / "masiate_pdf" / "render_report.py"
spec = importlib.util.spec_from_file_location("masiate_render_report", MODULE_PATH)
renderer = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(renderer)


def extract_text(path: Path) -> str:
    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def test_renderer_outputs_include_profiles_without_local_paths(tmp_path: Path) -> None:
    records = [
        {
            "id": "synthetic-include-1",
            "county": "Brazos",
            "project_name": "Synthetic apartment renovation",
            "address": "123 Test Street",
            "city": "Bryan",
            "record_type": "permit",
            "record_date": "2026-09-01",
            "stage": "permitted",
            "status_basis": "Permit issued; no source-backed bid status.",
            "scope": "Interior renovation with paint and flooring.",
            "masiate_fit": "Paint and flooring fit; inference labeled.",
            "estimated_value": "$100,000 whole-project estimate",
            "review_decision": "include",
            "priority_reason": "Recent permit with concrete Masiate trade fit.",
            "member_ids": ["synthetic-include-1"],
            "evidence_checked": ["/tmp/local-evidence-should-not-print.pdf"],
            "sources": [
                {
                    "url": "https://example.test/permits/123?with=a-very-long-query-string-for-wrapping",
                    "title": "Synthetic permit",
                    "date": "2026-09-01",
                    "page": "row 1",
                    "evidence": "Permit names address and renovation scope.",
                    "local_path": "/tmp/local-evidence-should-not-print.pdf",
                }
            ],
            "unknowns": ["Whether packages remain available"],
        },
        {
            "id": "synthetic-watch-1",
            "county": "Leon",
            "project_name": "Synthetic shelter",
            "review_decision": "watchlist",
            "priority_reason": "Needs award follow-up.",
            "status_basis": "Bid deadline has passed.",
        },
    ]
    coverage = [
        {
            "name": "Synthetic permit source",
            "county": "Brazos",
            "status": "partial",
            "covered_from": "2026-09-01",
            "covered_to": "2026-09-20",
            "records_found": 1,
            "reason": "Synthetic fixture only.",
            "next_cursor": "None.",
        }
    ]
    output = tmp_path / "report.pdf"

    renderer.render_pdf(records, coverage, output, "Synthetic Masiate Report")

    assert output.exists()
    text = extract_text(output)
    assert "Synthetic apartment renovation" in text
    assert "Synthetic shelter" in text
    assert "Work availability: unknown" in text
    assert "local-evidence-should-not-print" not in text


def test_cli_renders_empty_results_state(tmp_path: Path) -> None:
    records_path = tmp_path / "records.json"
    coverage_path = tmp_path / "coverage.json"
    output = tmp_path / "empty.pdf"
    records_path.write_text(json.dumps([]), encoding="utf-8")
    coverage_path.write_text(json.dumps([]), encoding="utf-8")

    renderer.render_pdf(
        renderer.load_json_array(records_path),
        renderer.load_json_array(coverage_path),
        output,
        "Empty Synthetic Report",
    )

    text = extract_text(output)
    assert "No detailed include records supplied yet" in text
    assert "No coverage file was supplied" in text
