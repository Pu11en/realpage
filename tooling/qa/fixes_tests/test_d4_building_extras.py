"""D4: site/data/properties.json's owner/sale/lead detail loads into the chat as
`building_extras`, one row per building keyed by `apt_id`, joinable to `master`."""
import importlib.util
import json
import pathlib
import sqlite3
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tooling" / "chat-data"))
import build_building_extras  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "propertystack_plugin", ROOT / "chatbot" / "hermes-profile" / "plugins" / "propertystack" / "__init__.py"
)
plugin = importlib.util.module_from_spec(_spec)


def _build_kb(tmp_path):
    kb_data = tmp_path / "kb-data"
    kb_data.mkdir()
    for csv_path in (ROOT / "propertystack" / "data" / "plano-richardson").glob("*.csv"):
        (kb_data / csv_path.name).write_bytes(csv_path.read_bytes())
    extras_kb = tmp_path / "extras-kb"
    build_building_extras.build(out=extras_kb / "building-extras.csv")
    (kb_data / "building-extras.csv").write_bytes((extras_kb / "building-extras.csv").read_bytes())
    return kb_data


def _load_plugin(kb_data, tmp_path):
    plugin.DATA_DIR = kb_data
    plugin.DB_PATH = tmp_path / "test.db"
    plugin._build_db()
    return plugin


def test_building_extras_table_loads():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = pathlib.Path(tmp)
        kb_data = _build_kb(tmp_path)
        _spec.loader.exec_module(plugin)
        p = _load_plugin(kb_data, tmp_path)

        tables = {t["table"] for t in p.SCHEMA}
        assert "building_extras" in tables, tables

        con = sqlite3.connect(f"file:{p.DB_PATH}?mode=ro", uri=True)
        n = con.execute("SELECT COUNT(*) FROM building_extras").fetchone()[0]
        con.close()
        properties = json.loads((ROOT / "site" / "data" / "properties.json").read_text())["properties"]
        assert n == len(properties)


def test_building_extras_joins_master_for_owner():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = pathlib.Path(tmp)
        kb_data = _build_kb(tmp_path)
        _spec.loader.exec_module(plugin)
        p = _load_plugin(kb_data, tmp_path)

        con = sqlite3.connect(f"file:{p.DB_PATH}?mode=ro", uri=True)
        row = con.execute(
            "SELECT m.owner, e.owner FROM master m JOIN building_extras e ON m.apt_id = e.apt_id "
            "WHERE m.apt_id = '2615335'"
        ).fetchone()
        con.close()
        assert row is not None, "join by apt_id returned no row"
        assert row[0] == row[1] == "5765 BOZEMAN (TX) OWNER LP"


def test_building_extras_sale_and_lead_notes_present():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = pathlib.Path(tmp)
        kb_data = _build_kb(tmp_path)
        _spec.loader.exec_module(plugin)
        p = _load_plugin(kb_data, tmp_path)

        properties = json.loads((ROOT / "site" / "data" / "properties.json").read_text())["properties"]
        want = next(pr for pr in properties if pr.get("sale") and pr.get("lead"))

        con = sqlite3.connect(f"file:{p.DB_PATH}?mode=ro", uri=True)
        row = con.execute(
            "SELECT sale_date, sale_new_owner, lead_rank, lead_why FROM building_extras WHERE apt_id = ?",
            (want["id"],),
        ).fetchone()
        con.close()
        assert row == (
            want["sale"]["date"],
            want["sale"]["newOwner"],
            str(want["lead"]["rank"]),
            want["lead"]["why"],
        )
