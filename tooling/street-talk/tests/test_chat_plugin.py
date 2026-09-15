"""Offline: the chat plugin loads street_talk.csv as table street_talk, and a query returns thread links."""
import importlib.util
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
PLUGIN = ROOT / "chatbot" / "hermes-profile" / "plugins" / "propertystack" / "__init__.py"
SAVED_CSV = ROOT / "propertystack" / "data" / "street-talk" / "street_talk.csv"
SAMPLE = """part,date,source,subreddit,title,quote,url,companies,sentiment,city,building_id,building,warm_lead,score
rivals,2026-08-01,reddit,Dallas,Yardi portal down again,Our Yardi portal is down,https://www.reddit.com/r/Dallas/comments/abc/yardi/,Yardi,angry,Dallas,,,,4
unhappy,2026-07-01,reddit,PropertyManagement,Leaving AppFolio,We manage 300 units in Austin,https://www.reddit.com/r/PropertyManagement/comments/def/leaving/,AppFolio;Entrata,angry,Austin,,,1,9
"""


def _load_plugin(tmp_path, monkeypatch, csv_text):
    data = tmp_path / "data"
    data.mkdir()
    (data / "street-talk.csv").write_text(csv_text)  # the name the Dockerfile copies it to
    monkeypatch.setenv("PS_DATA_DIR", str(data))
    monkeypatch.setenv("PS_RESEARCH_DIR", str(tmp_path / "research"))
    monkeypatch.setenv("PS_DB_PATH", str(tmp_path / "ps.db"))
    monkeypatch.setenv("HERMES_HOME", str(tmp_path / "home"))
    spec = importlib.util.spec_from_file_location("ps_plugin_under_test", PLUGIN)
    mod = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, mod)
    spec.loader.exec_module(mod)
    mod._build_db()
    return mod


def test_table_loads_with_source_name(tmp_path, monkeypatch):
    mod = _load_plugin(tmp_path, monkeypatch, SAMPLE)
    schema = json.loads(mod.ps_schema({}))
    row = next(t for t in schema["tables"] if t["table"] == "street_talk")
    assert row["source_name"] == "Reddit posts" and row["rows"] == 2
    assert {"url", "companies", "sentiment", "warm_lead"} <= set(row["columns"])
    assert any("street_talk" in n for n in schema["notes"])


def test_sample_query_returns_rows_with_links(tmp_path, monkeypatch):
    mod = _load_plugin(tmp_path, monkeypatch, SAMPLE)
    out = json.loads(mod.ps_sql({"query": "SELECT title, url FROM street_talk WHERE companies LIKE '%Yardi%'"}))
    assert out["rows"] == [["Yardi portal down again", "https://www.reddit.com/r/Dallas/comments/abc/yardi/"]]
    seen = (tmp_path / "home" / "seen-urls.txt").read_text()  # link guard will keep these links
    assert "https://www.reddit.com/r/Dallas/comments/abc/yardi/" in seen


def test_saved_csv_loads(tmp_path, monkeypatch):
    if not SAVED_CSV.exists():
        return
    mod = _load_plugin(tmp_path, monkeypatch, SAVED_CSV.read_text())
    out = json.loads(mod.ps_sql({"query": "SELECT url FROM street_talk"}))
    assert out["rows"] and all(r[0].startswith(("https://www.reddit.com/", "https://www.youtube.com/")) for r in out["rows"])


def test_dockerfile_bakes_it_in():
    text = (ROOT / "chatbot" / "Dockerfile").read_text()
    assert "street-talk/street_talk.csv /kb/data/street-talk.csv" in text
