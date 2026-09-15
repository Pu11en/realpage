"""A7: Under the Hood hides raw internals and shows the same lead count as the site."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
PAGE = (ROOT / "site/under-the-hood.html").read_text(encoding="utf-8")


def test_raw_bits_hidden():
    for raw in ["area: plano-richardson", "runs/*.json", "placeholderBanner", "costPerArea", "errors)"]:
        assert raw not in PAGE, raw


def test_only_ok_runs_listed():
    assert '.runs.filter((r) => r.status === "ok")' in PAGE
    assert "${data.runs.map(" not in PAGE and "${pipeline.runs.map(" not in PAGE


def _fn(name):
    return "function " + name + PAGE.split("function " + name, 1)[1].split("\n    }\n", 1)[0] + "\n}\n"


@pytest.mark.skipif(not shutil.which("node"), reason="node not installed")
def test_lead_count_matches_site():
    index = json.loads((ROOT / "site/data/areas/index.json").read_text())
    steps = json.loads((ROOT / "site/data/pipeline.json").read_text())["steps"]
    js = _fn("siteLeadTotal") + _fn("userSteps") + (
        f"const t = siteLeadTotal({json.dumps(index['areas'])});"
        f"console.log(JSON.stringify(userSteps({json.dumps(steps)}, t).at(-1)));"
    )
    out = json.loads(subprocess.run(["node", "-e", js], capture_output=True, text=True, check=True).stdout)
    assert out["count"] == sum(a["leads"] for a in index["areas"])
    assert out["label"] == "leads on the site"
