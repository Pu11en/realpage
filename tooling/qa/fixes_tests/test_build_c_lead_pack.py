"""Build C T2: a signed-in visitor can download a sourced PDF for every lead in one region."""

import json
import subprocess
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[3]
SITE = ROOT / "site"


def test_pdf_libraries_are_pinned_local_and_licensed():
    jspdf = SITE / "vendor" / "jspdf-4.2.1.umd.min.js"
    autotable = SITE / "vendor" / "jspdf-autotable-5.0.8.min.js"
    assert jspdf.is_file() and b"Version 4.2.1" in jspdf.read_bytes()[:500]
    assert autotable.is_file() and b"v5.0.8" in autotable.read_bytes()[:500]
    for license_name in ("LICENSE-jspdf-4.2.1.txt", "LICENSE-jspdf-autotable-5.0.8.txt"):
        text = (SITE / "vendor" / license_name).read_text(encoding="utf-8")
        assert "MIT" in text or "Permission is hereby granted" in text


def test_lead_pack_ui_uses_the_existing_account_check():
    page = (SITE / "index.html").read_text(encoding="utf-8")
    panel = (SITE / "js" / "chat-panel.js").read_text(encoding="utf-8")
    assert "Download call list (PDF)" in page
    assert 'window.PSChatPanel.requireAuth(' in page
    assert "Make a free account to download your call list" in page
    assert "function requireAuth(purpose, onSuccess)" in panel
    assert "return checkAuth(panel).then" in panel
    assert "sendPendingAuthAction(panel)" in panel


def test_dallas_lead_pack_has_one_complete_linked_row_per_lead(tmp_path):
    tx = json.loads((SITE / "data" / "areas" / "tx.json").read_text(encoding="utf-8"))
    leads = [lead for lead in tx["leads"] if lead.get("metro") == "Dallas–Fort Worth"]
    assert leads

    pdf_path = tmp_path / "dallas-lead-pack.pdf"
    script = r"""
const fs = require("fs");
const path = require("path");
const root = process.argv[1];
const output = process.argv[2];
const jspdf = require(path.join(root, "site/vendor/jspdf-4.2.1.umd.min.js"));
global.jspdf = jspdf;
const plugin = require(path.join(root, "site/vendor/jspdf-autotable-5.0.8.min.js"));
if (typeof jspdf.jsPDF.API.autoTable !== "function" && plugin.applyPlugin) plugin.applyPlugin(jspdf.jsPDF);
const leadPack = require(path.join(root, "site/js/lead-pack.js"));
const leads = JSON.parse(fs.readFileSync(0, "utf8"));
const result = leadPack.buildLeadPack({leads, region: "Dallas–Fort Worth", date: "2026-09-19"});
fs.writeFileSync(output, Buffer.from(result.doc.output("arraybuffer")));
process.stdout.write(JSON.stringify({
  filename: result.filename,
  rowCount: result.rowCount,
  rows: result.rows.map((row) => ({
    id: row.id,
    label: row.priority.label,
    reason: row.priority.reason,
    whyNow: row.whyNow,
    source: row.source.url,
  })),
}));
"""
    proc = subprocess.run(
        ["node", "-e", script, str(ROOT), str(pdf_path)],
        input=json.dumps(leads),
        text=True,
        capture_output=True,
        check=True,
    )
    built = json.loads(proc.stdout)

    assert built["filename"] == "cranesignal-lead-pack-dallas-fort-worth-2026-09-19.pdf"
    assert built["rowCount"] == len(leads)
    assert [row["id"] for row in built["rows"]] == [lead["id"] for lead in leads]
    assert {row["label"] for row in built["rows"]} == {"Hot", "Warm", "Early"}
    assert all(row["reason"].endswith(".") for row in built["rows"])
    assert all(row["whyNow"].endswith((".", "!", "?")) for row in built["rows"])
    assert all(row["source"].startswith(("http://", "https://")) for row in built["rows"])

    reader = PdfReader(pdf_path)
    assert reader.metadata.title == "CraneSignal call list: Dallas–Fort Worth, September 19, 2026"
    first_page = reader.pages[0]
    assert round(float(first_page.mediabox.width)) == 792
    assert round(float(first_page.mediabox.height)) == 612

    source_links = []
    for page in reader.pages:
        for annotation_ref in page.get("/Annots", []):
            annotation = annotation_ref.get_object()
            uri = annotation.get("/A", {}).get("/URI", "")
            if uri and uri != "https://app.cranesignal.com":
                source_links.append(uri)
    assert len(source_links) == len(leads)

    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    assert "CraneSignal call list: Dallas" in text
    assert all(label in text for label in ("Hot", "Warm", "Early"))
    assert "Find who to call for any building at app.cranesignal.com" in text
