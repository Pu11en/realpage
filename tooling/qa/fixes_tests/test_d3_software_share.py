"""D3: the site's vendor market-share chart (site/data/software-share.json) loads into the chat
as `software_share`, with numbers matching the site exactly."""
import importlib.util
import json
import pathlib
import sqlite3
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tooling" / "chat-data"))
import build_software_share  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "propertystack_plugin", ROOT / "chatbot" / "hermes-profile" / "plugins" / "propertystack" / "__init__.py"
)
plugin = importlib.util.module_from_spec(_spec)


def _build_kb(tmp_path):
    kb_data = tmp_path / "kb-data"
    kb_data.mkdir()
    share_kb = tmp_path / "share-kb"
    build_software_share.build(out=share_kb / "software-share.csv")
    (kb_data / "software-share.csv").write_bytes((share_kb / "software-share.csv").read_bytes())
    return kb_data


def _load_plugin(kb_data, tmp_path):
    plugin.DATA_DIR = kb_data
    plugin.DB_PATH = tmp_path / "test.db"
    plugin._build_db()
    return plugin


def test_software_share_table_loads():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = pathlib.Path(tmp)
        kb_data = _build_kb(tmp_path)
        _spec.loader.exec_module(plugin)
        p = _load_plugin(kb_data, tmp_path)

        tables = {t["table"] for t in p.SCHEMA}
        assert "software_share" in tables, tables

        con = sqlite3.connect(f"file:{p.DB_PATH}?mode=ro", uri=True)
        row = con.execute(
            "SELECT pct_of_identified_properties FROM software_share WHERE vendor='RealPage' LIMIT 1"
        ).fetchone()
        con.close()
        assert row is not None


def test_software_share_matches_site():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = pathlib.Path(tmp)
        kb_data = _build_kb(tmp_path)

        site_share = json.loads((ROOT / "site" / "data" / "software-share.json").read_text())["share"]

        _spec.loader.exec_module(plugin)
        p = _load_plugin(kb_data, tmp_path)

        con = sqlite3.connect(f"file:{p.DB_PATH}?mode=ro", uri=True)
        for entry in site_share:
            row = con.execute(
                "SELECT properties, units, pct_of_identified_properties FROM software_share WHERE vendor=?",
                (entry["vendor"],),
            ).fetchone()
            assert row, f"missing vendor {entry['vendor']}"
            assert int(row[0]) == entry["properties"], (entry["vendor"], row)
            assert int(row[1]) == entry["units"], (entry["vendor"], row)
            assert float(row[2]) == entry["pctOfIdentifiedProperties"], (entry["vendor"], row)
        con.close()
