"""D1: the Dallas building survey loads into the chat's kb as its own tables, without touching
Texas/DFW lead counts (which come from state_leads, built separately by the Dockerfile)."""
import csv
import importlib.util
import pathlib
import sqlite3
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tooling" / "chat-data"))
import build_dallas  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "propertystack_plugin", ROOT / "chatbot" / "hermes-profile" / "plugins" / "propertystack" / "__init__.py"
)
plugin = importlib.util.module_from_spec(_spec)


def _build_kb(tmp_path):
    """Reproduce the Dockerfile's kb stage: plano-richardson CSVs + dallas-parked/kb CSVs, flat."""
    kb_data = tmp_path / "kb-data"
    kb_data.mkdir()
    for src in (ROOT / "propertystack" / "data" / "plano-richardson").glob("*.csv"):
        (kb_data / src.name).write_bytes(src.read_bytes())
    dallas_kb = tmp_path / "dallas-kb"
    build_dallas.build(src_dir=ROOT / "propertystack" / "data" / "dallas-parked", out_dir=dallas_kb)
    for src in dallas_kb.glob("*.csv"):
        (kb_data / src.name).write_bytes(src.read_bytes())
    return kb_data


def _load_plugin(kb_data, tmp_path):
    plugin.DATA_DIR = kb_data
    plugin.DB_PATH = tmp_path / "test.db"
    plugin._build_db()
    return plugin


def test_dallas_tables_load_with_area_column():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = pathlib.Path(tmp)
        kb_data = _build_kb(tmp_path)
        _spec.loader.exec_module(plugin)
        p = _load_plugin(kb_data, tmp_path)

        tables = {t["table"] for t in p.SCHEMA}
        for expected in ("dallas_buildings", "dallas_websites", "dallas_software", "dallas_sales", "dallas_contacts"):
            assert expected in tables, tables

        con = sqlite3.connect(f"file:{p.DB_PATH}?mode=ro", uri=True)
        rows = con.execute("SELECT area, name FROM dallas_buildings LIMIT 1").fetchall()
        assert rows and rows[0][0] == "dallas"
        con.close()


def test_texas_lead_count_unchanged_by_dallas_tables():
    """state_leads (built by the Dockerfile from chat-leads.csv, not part of this repro) doesn't
    exist in this test's kb, but the point of D1 is that dallas_* tables carry their own rows and
    never get unioned into leads/state_leads -- assert the row counts stay independent."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = pathlib.Path(tmp)
        kb_data = _build_kb(tmp_path)
        leads_rows = 0
        leads_csv = ROOT / "propertystack" / "data" / "plano-richardson" / "leads.csv"
        with open(leads_csv, newline="") as f:
            leads_rows = sum(1 for _ in csv.reader(f)) - 1

        _spec.loader.exec_module(plugin)
        p = _load_plugin(kb_data, tmp_path)

        leads_table = next(t for t in p.SCHEMA if t["table"] == "leads")
        assert leads_table["rows"] == leads_rows

        dallas_buildings_table = next(t for t in p.SCHEMA if t["table"] == "dallas_buildings")
        assert dallas_buildings_table["rows"] > 0
