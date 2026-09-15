"""A4: every Early Leads row opens a detail page, including rows with no propertyId (TX/AZ/NY)."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
INDEX = (ROOT / "site/index.html").read_text(encoding="utf-8")
PROPERTY = (ROOT / "site/property.html").read_text(encoding="utf-8")


def test_every_row_is_clickable():
    assert 'class="clickable" data-id="${l.propertyId || l.id}"' in INDEX
    assert "l.propertyId ? \"clickable\"" not in INDEX


def test_property_page_falls_back_to_lead():
    assert "findLead(id" in PROPERTY
    for bit in ("Stage", "Software", "Sources", "Deep dive in chat", "l.why", "l.units"):
        assert bit in PROPERTY


@pytest.mark.skipif(not shutil.which("node"), reason="node not installed")
def test_every_built_lead_id_is_found():
    props = json.loads((ROOT / "site/data/properties.json").read_text(encoding="utf-8"))
    known = {p["id"] for p in props["properties"]} | {p["id"] for p in props.get("upcoming", [])}
    index = json.loads((ROOT / "site/data/areas/index.json").read_text(encoding="utf-8"))
    files = []
    for a in index["areas"]:
        data = json.loads((ROOT / "site" / a["dataPath"]).read_text(encoding="utf-8"))
        files.append({"slug": a["slug"], "label": a["label"], "leads": data["leads"]})
    wanted = [l.get("propertyId") or l["id"] for f in files for l in f["leads"]]
    assert len(wanted) > 900
    app = (ROOT / "site/js/app.js").read_text(encoding="utf-8")
    fn = "function pickLead" + app.split("function pickLead", 1)[1].split("async function findLead", 1)[0]
    script = fn + "\nconst {files, ids} = JSON.parse(require('fs').readFileSync(0, 'utf8'));\n" \
                  "console.log(JSON.stringify(ids.filter((id) => !pickLead(files, id))));"
    missing = json.loads(subprocess.run(["node", "-e", script], input=json.dumps({"files": files, "ids": wanted}),
                                        capture_output=True, text=True, check=True).stdout)
    not_found = [i for i in missing if i not in known]
    assert not_found == [], f"these leads would show 'not found': {not_found[:10]}"
