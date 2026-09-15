"""B2: the chat counts leads like the site -- Texas = site total, Dallas-Fort Worth = 320."""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "propertystack/data"
PLUGIN = ROOT / "chatbot/hermes-profile/plugins/propertystack/__init__.py"


def _plugin(tmp_path, monkeypatch):
    """Load the chat plugin on a knowledge base put together like chatbot/Dockerfile does."""
    kb = tmp_path / "data"
    kb.mkdir()
    for f in (DATA / "plano-richardson").glob("*.csv"):
        (kb / f.name).write_text(f.read_text())
    lines = []
    for f in sorted(DATA.glob("*/chat-leads.csv")):
        if f.parent.name.startswith("_"):
            continue
        rows = f.read_text().splitlines()
        lines += rows if not lines else rows[1:]
    (kb / "state-leads.csv").write_text("\n".join(lines) + "\n")
    monkeypatch.setenv("PS_DATA_DIR", str(kb))
    monkeypatch.setenv("PS_DB_PATH", str(tmp_path / "ps.db"))
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    spec = importlib.util.spec_from_file_location("ps_plugin_b2", PLUGIN)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["ps_plugin_b2"] = mod
    spec.loader.exec_module(mod)
    mod._build_db()
    return mod


def _count(mod, sql):
    out = json.loads(mod.ps_sql({"query": sql}))
    assert "error" not in out, out
    return int(out["rows"][0][0])


def test_dfw_is_320(tmp_path, monkeypatch):
    mod = _plugin(tmp_path, monkeypatch)
    assert _count(mod, "SELECT COUNT(*) FROM state_leads WHERE region='Dallas–Fort Worth'") == 320


def test_texas_matches_site(tmp_path, monkeypatch):
    mod = _plugin(tmp_path, monkeypatch)
    site = json.loads((ROOT / "site/data/areas/tx.json").read_text())
    assert _count(mod, "SELECT COUNT(*) FROM state_leads WHERE area='tx'") == site["stats"]["leads"]
    assert _count(mod, "SELECT COUNT(*) FROM state_leads WHERE area='tx' AND stage=''") == 0
