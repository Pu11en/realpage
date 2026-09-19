"""A2: Leads number boxes follow the rows shown (region, city, search), and an empty result says "Nothing found"."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
INDEX = (ROOT / "site/index.html").read_text(encoding="utf-8")


def test_stats_come_from_shown_rows():
    assert "data.stats" not in INDEX, "number boxes still read the whole state's totals"
    assert "leadStats(rows)" in INDEX


def test_empty_result_message_and_clear_button():
    assert "No buildings match this in" in INDEX  # reworded 2026-09-19: say where and what to try
    assert 'id="clear-search"' in INDEX


@pytest.mark.skipif(not shutil.which("node"), reason="node not installed")
def test_lead_stats_counts_only_given_rows():
    tx = json.loads((ROOT / "site/data/areas/tx.json").read_text(encoding="utf-8"))
    dfw = [l for l in tx["leads"] if l.get("metro") == "Dallas–Fort Worth"]
    assert 0 < len(dfw) < len(tx["leads"])
    app = (ROOT / "site/js/app.js").read_text(encoding="utf-8")
    fn = "function leadStats" + app.split("function leadStats", 1)[1].split("function placeholderBanner", 1)[0]
    script = fn + "\nconst rows = JSON.parse(require('fs').readFileSync(0, 'utf8'));\n" \
                  "console.log(JSON.stringify(leadStats(rows, new Date('2026-09-15'))));"
    out = subprocess.run(["node", "-e", script], input=json.dumps(dfw),
                         capture_output=True, text=True, check=True).stdout
    s = json.loads(out)
    assert s["leads"] == len(dfw)
    assert s["unitsInPlay"] == sum(l.get("units") or 0 for l in dfw)
    assert s["unitsInPlay"] < tx["stats"]["unitsInPlay"]
