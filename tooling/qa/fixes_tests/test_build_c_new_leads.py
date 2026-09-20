"""Build C T3: later downloads include only leads first seen after the saved date."""

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SITE = ROOT / "site"


def run_lead_pack_script(script):
    proc = subprocess.run(
        ["node", "-e", script, str(ROOT)],
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


def test_download_history_is_scoped_to_each_state_and_region():
    script = r"""
const path = require("path");
const root = process.argv[1];
const leadPack = require(path.join(root, "site/js/lead-pack.js"));
const values = new Map();
const storage = {
  getItem(key) { return values.has(key) ? values.get(key) : null; },
  setItem(key, value) { values.set(key, value); },
};
leadPack.rememberDownloadDate(storage, "tx", "Dallas–Fort Worth", "2026-09-19");
leadPack.rememberDownloadDate(storage, "tx", "__all__", "2026-09-18");
process.stdout.write(JSON.stringify({
  dallas: leadPack.lastDownloadDate(storage, "tx", "Dallas–Fort Worth"),
  allTexas: leadPack.lastDownloadDate(storage, "tx", "__all__"),
  houston: leadPack.lastDownloadDate(storage, "tx", "Houston"),
  keys: [...values.keys()],
}));
"""
    result = run_lead_pack_script(script)

    assert result["dallas"] == "2026-09-19"
    assert result["allTexas"] == "2026-09-18"
    assert result["houston"] == ""
    assert len(set(result["keys"])) == 2


def test_new_leads_are_strictly_after_the_last_download_date():
    script = r"""
const path = require("path");
const root = process.argv[1];
const leadPack = require(path.join(root, "site/js/lead-pack.js"));
const leads = [
  {id: "old", firstSeen: "2026-09-15"},
  {id: "same-day", firstSeen: "2026-09-19"},
  {id: "new-one", firstSeen: "2026-09-20"},
  {id: "new-two", firstSeen: "2026-10-01"},
  {id: "missing"},
];
process.stdout.write(JSON.stringify({
  ids: leadPack.leadsFirstSeenAfter(leads, "2026-09-19").map((lead) => lead.id),
  noHistory: leadPack.leadsFirstSeenAfter(leads, "").map((lead) => lead.id),
}));
"""
    result = run_lead_pack_script(script)

    assert result["ids"] == ["new-one", "new-two"]
    assert result["noHistory"] == []


def test_get_new_leads_ui_is_hidden_until_a_download_and_has_empty_state():
    page = (SITE / "index.html").read_text(encoding="utf-8")

    assert 'id="download-new-leads" hidden' in page
    assert "newLeadsButton.hidden = !lastDownloadFor(selectedLeadPack())" in page
    assert "leadsFirstSeenAfter(selection.leads, lastDownload)" in page
    assert "No new leads since ${window.CraneSignalLeadPack.displayDate(lastDownload)}. Ask for your area below." in page
    assert "rememberDownloadDate(" in page
    assert "selection.areaSlug" in page
    assert "selection.storageRegion" in page
