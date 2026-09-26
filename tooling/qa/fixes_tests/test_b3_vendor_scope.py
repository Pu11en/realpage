"""B3: vendor answers say the software data only covers Plano and Richardson."""
import csv
import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PROFILE = ROOT / "chatbot/hermes-profile"
SCOPE = re.compile(r"Plano and Richardson", re.I)



def published_slugs() -> list[str]:
    """The states the site actually publishes, from the area index rather than a hard-coded
    tuple. Every one of these tests named ("tx", "az", "ny") and broke on 2026-09-26 when
    CraneSignal became Texas only; read from the index they survive the next change too.
    """
    import json as _json
    index = _json.loads(
        (ROOT / "site" / "data" / "areas" / "index.json").read_text(encoding="utf-8")
    )
    return [a["slug"] for a in index["areas"] if not a.get("hidden")]

def test_soul_has_scope_rule():
    rule = [l for l in (PROFILE / "SOUL.md").read_text().split("\n- ") if "vendor" in l.lower()]
    assert any(SCOPE.search(r) and "Texas-wide" in r for r in rule)


def test_skill_and_schema_say_scope():
    skill = (PROFILE / "skills/query-propertystack/SKILL.md").read_text()
    assert re.search(r"Software scope:.*Plano and Richardson", skill, re.S)
    plugin = (PROFILE / "plugins/propertystack/__init__.py").read_text()
    assert re.search(r"Software data covers Plano and Richardson only", plugin)


def test_scope_is_true_in_data():
    # The rule must match the data: software only filled in for Plano/Richardson rows.
    for area in published_slugs():
        for r in csv.DictReader(open(ROOT / f"propertystack/data/{area}/chat-leads.csv")):
            if r["software"]:
                assert r["city"] in ("Plano", "Richardson"), (area, r["name"])


def test_check_answers_checks_scope():
    spec = importlib.util.spec_from_file_location("ca", ROOT / "tooling/qa/check_answers.py")
    ca = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ca)
    q = "Which vendor runs the most buildings?"
    assert q in ca.QUESTIONS
    assert any("Plano" in p for p in ca.problems("**Yardi** runs **13**.", q))
    assert not any("covers" in p for p in ca.problems("In Plano and Richardson, **Yardi** runs **13**.", q))
