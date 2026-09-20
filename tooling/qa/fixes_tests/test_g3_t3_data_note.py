"""G3-T3: Leads names the snapshot date and links area requests."""
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
INDEX = (ROOT / "site/index.html").read_text(encoding="utf-8")
APP = (ROOT / "site/js/app.js").read_text(encoding="utf-8")


def test_data_note_sits_directly_under_stats_without_a_coverage_claim():
    note = INDEX.index('Data from ${formatDataDate(data.updated)}')
    stats = INDEX.index('<div class="stats-row" id="lead-stats"></div>')
    search = INDEX.index('<form class="lead-agent-search"')

    assert note < stats < search
    assert "Data from ${formatDataDate(data.updated)}" in INDEX
    assert "Texas &amp; Arizona" not in INDEX



@pytest.mark.skipif(not shutil.which("node"), reason="node not installed")
def test_data_note_uses_the_area_snapshot_date():
    fn = "function formatDataDate" + APP.split("function formatDataDate", 1)[1].split("\n}\n", 1)[0] + "\n}\n"
    out = subprocess.run(
        ["node", "-e", fn + "console.log(formatDataDate('2026-09-15'), '|', formatDataDate(''))"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    assert out == "Sep 15, 2026 |"
