"""A5: the Deep dive prompt names the lead's real stage instead of calling every upcoming row "planned"."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
PANEL = (ROOT / "site/js/chat-panel.js").read_text(encoding="utf-8")


def prompts(leads):
    script = ("const window = {};\n"
              + "const STAGE_WORDS" + PANEL.split("const STAGE_WORDS", 1)[1].split("  window.PSChatPanel", 1)[0]
              + "\nconst leads = JSON.parse(require('fs').readFileSync(0, 'utf8'));\n"
              "console.log(JSON.stringify(leads.map(deepDivePrompt)));")
    out = subprocess.run(["node", "-e", script], input=json.dumps(leads),
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def test_callers_pass_the_stage():
    for page in ("site/index.html", "site/property.html"):
        assert "stage: l.stage, signalType: l.signalType" in (ROOT / page).read_text(encoding="utf-8")


@pytest.mark.skipif(not shutil.which("node"), reason="node not installed")
def test_prompt_uses_real_stage():
    base = {"name": "X", "city": "Mesa", "units": 100, "software": "unknown"}
    got = prompts([
        {**base, "stage": "under construction", "signalType": "Upcoming"},
        {**base, "stage": "leasing", "signalType": "Upcoming"},
        {**base, "stage": "under construction", "signalType": "Leasing"},
        {**base, "stage": "permitted", "signalType": "Upcoming"},
        {**base, "stage": "planned", "signalType": "Planned"},
        {**base, "stage": "sold", "signalType": "Sold"},
        {**base, "upcoming": True, "stage": "zoning-filed"},
    ])
    assert "under construction" in got[0] and "planned" not in got[0]
    assert "leasing now" in got[1] and "planned" not in got[1]
    assert "leasing now" in got[2]
    assert "permit filed" in got[3] and "planned" not in got[3]
    assert "planned" in got[4]
    assert "recently sold" in got[5] and "who runs it" in got[5]
    assert "planned" in got[6]
