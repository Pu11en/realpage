"""D2: the site's lead map (site/data/client-map.json) loads into the chat as `map_summary`,
with state totals matching the site exactly."""
import importlib.util
import json
import pathlib
import sqlite3
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tooling" / "chat-data"))
import build_map_summary  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "propertystack_plugin", ROOT / "chatbot" / "hermes-profile" / "plugins" / "propertystack" / "__init__.py"
)
plugin = importlib.util.module_from_spec(_spec)


def _build_kb(tmp_path):
    kb_data = tmp_path / "kb-data"
    kb_data.mkdir()
    map_kb = tmp_path / "map-kb"
    build_map_summary.build(out=map_kb / "map-summary.csv")
    (kb_data / "map-summary.csv").write_bytes((map_kb / "map-summary.csv").read_bytes())
    return kb_data


def _load_plugin(kb_data, tmp_path):
    plugin.DATA_DIR = kb_data
    plugin.DB_PATH = tmp_path / "test.db"
    plugin._build_db()
    return plugin


def test_map_summary_table_loads():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = pathlib.Path(tmp)
        kb_data = _build_kb(tmp_path)
        _spec.loader.exec_module(plugin)
        p = _load_plugin(kb_data, tmp_path)

        tables = {t["table"] for t in p.SCHEMA}
        assert "map_summary" in tables, tables

        con = sqlite3.connect(f"file:{p.DB_PATH}?mode=ro", uri=True)
        row = con.execute(
            "SELECT state_total FROM map_summary WHERE state='Texas' LIMIT 1"
        ).fetchone()
        con.close()
        assert row is not None


def test_map_summary_totals_match_site():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = pathlib.Path(tmp)
        kb_data = _build_kb(tmp_path)

        site_map = json.loads((ROOT / "site" / "data" / "client-map.json").read_text())

        _spec.loader.exec_module(plugin)
        p = _load_plugin(kb_data, tmp_path)

        con = sqlite3.connect(f"file:{p.DB_PATH}?mode=ro", uri=True)
        for state, info in site_map["states"].items():
            row = con.execute(
                "SELECT DISTINCT state_total FROM map_summary WHERE state=?", (state,)
            ).fetchall()
            assert row, f"missing state {state}"
            assert len(row) == 1, f"state_total should be constant per state: {state} -> {row}"
            assert int(row[0][0]) == info["total"], (state, row, info["total"])
        con.close()
