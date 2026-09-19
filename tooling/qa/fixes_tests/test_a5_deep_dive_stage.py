"""A5/G1: Deep dives use the real stage and ask for sourced contact details first."""
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


def test_callers_pass_the_buyer_when_available():
    index = (ROOT / "site/index.html").read_text(encoding="utf-8")
    detail = (ROOT / "site/property.html").read_text(encoding="utf-8")
    assert "buyer: l.buyer" in index
    assert "buyer: l.buyer" in detail
    assert "p.sale && p.sale.newOwner" in detail


@pytest.mark.skipif(not shutil.which("node"), reason="node not installed")
def test_prompt_uses_real_stage():
    base = {"name": "X", "city": "Mesa", "units": 100, "software": "unknown"}
    got = prompts([
        {**base, "stage": "under construction", "signalType": "Upcoming"},
        {**base, "stage": "leasing", "signalType": "Upcoming"},
        {**base, "stage": "under construction", "signalType": "Leasing"},
        {**base, "stage": "permitted", "signalType": "Upcoming"},
        {**base, "stage": "planned", "signalType": "Planned"},
        {**base, "stage": "sold", "signalType": "Sold", "buyer": "Example Owner LLC"},
        {**base, "upcoming": True, "stage": "zoning-filed"},
        {**base, "stage": "sold", "signalType": "Sold", "buyer": None},
    ])
    assert "under construction" in got[0] and "planned" not in got[0]
    assert "leasing now" in got[1] and "planned" not in got[1]
    assert "leasing now" in got[2]
    assert "permit filed" in got[3] and "planned" not in got[3]
    assert "planned" in got[4]
    assert "recently sold" in got[5]
    assert "planned" in got[6]
    contact_request = (
        "Who to call: management company, office phone, website, and the role to ask for "
        "(with a source link for each)"
    )
    for prompt in got:
        assert contact_request in prompt
        assert prompt.index(contact_request) < prompt.index("why call now")
    assert "who bought it (new owner)" not in got[5]
    assert "who bought it (new owner), with a source link" in got[7]
