"""A6: the menu's "Last updated" comes from the built data, and "View as" is labeled plainly."""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
APP = (ROOT / "site/js/app.js").read_text(encoding="utf-8")


def test_no_hard_coded_date():
    assert not re.search(r"Last updated: [A-Z][a-z]{2} \d", APP)


def test_built_data_has_a_date():
    updated = json.loads((ROOT / "site/data/areas/index.json").read_text())["updated"]
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", updated)
    area_dates = {
        json.loads(path.read_text())["updated"]
        for path in (ROOT / "site/data/areas").glob("[a-z][a-z].json")
    }
    assert updated == max(area_dates)
    build_script = (ROOT / "site/data/build_data.py").read_text()
    assert '"updated": latest_area_run_date(slug) or CURRENT_DATA_DATE' in build_script
    assert '"updated": date.today().isoformat()' not in build_script


def test_view_as_menu_is_gone():
    # Removed 2026-09-19: first-time users did not understand "View as: RealPage / Yardi".
    assert ">View as</label>" not in APP
    assert 'id="view-as-select"' not in APP



def test_format_updated():
    fn = "function formatUpdated" + APP.split("function formatUpdated", 1)[1].split("\n}\n", 1)[0] + "\n}\n"
    out = subprocess.run(["node", "-e", fn + "console.log(formatUpdated('2026-09-15'), '|', formatUpdated(''))"],
                         capture_output=True, text=True, check=True).stdout.strip()
    assert out == "Last updated: Sep 15, 2026 |"
