"""D6: the AI Visibility page's read-only JSON loads into chat as `ai_visibility_*`
tables, with key values matching site/data exactly."""
import importlib.util
import json
import pathlib
import sqlite3
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tooling" / "chat-data"))
import build_ai_visibility  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "propertystack_plugin", ROOT / "chatbot" / "hermes-profile" / "plugins" / "propertystack" / "__init__.py"
)
plugin = importlib.util.module_from_spec(_spec)


EXPECTED_TABLES = {
    "ai_visibility_summary",
    "ai_visibility_models",
    "ai_visibility_competitors",
    "ai_visibility_questions",
    "ai_visibility_top_picks",
    "ai_visibility_actions",
    "ai_visibility_site_facts",
    "ai_visibility_caveats",
}


def _build_kb(tmp_path):
    kb_data = tmp_path / "kb-data"
    kb_data.mkdir()
    ai_kb = tmp_path / "ai-kb"
    build_ai_visibility.build(out_dir=ai_kb)
    for csv_path in ai_kb.glob("*.csv"):
        (kb_data / csv_path.name).write_bytes(csv_path.read_bytes())
    return kb_data


def _load_plugin(kb_data, tmp_path):
    plugin.DATA_DIR = kb_data
    plugin.DB_PATH = tmp_path / "test.db"
    plugin._build_db()
    return plugin


def test_dockerfile_copies_ai_visibility_kb():
    dockerfile = (ROOT / "chatbot" / "Dockerfile").read_text()
    assert "propertystack/data/ai-visibility/kb" in dockerfile


def test_ai_visibility_tables_load_with_sources():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = pathlib.Path(tmp)
        kb_data = _build_kb(tmp_path)
        _spec.loader.exec_module(plugin)
        p = _load_plugin(kb_data, tmp_path)

        tables = {t["table"] for t in p.SCHEMA}
        assert EXPECTED_TABLES <= tables
        source_names = {t["table"]: t["source_name"] for t in p.SCHEMA}
        assert source_names["ai_visibility_summary"] == "AI Visibility score summary"
        assert source_names["ai_visibility_actions"] == "AI Visibility recommended actions"


def test_ai_visibility_tables_match_site_json():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = pathlib.Path(tmp)
        kb_data = _build_kb(tmp_path)

        scores = json.loads((ROOT / "site" / "data" / "ai-visibility.json").read_text())
        actions = json.loads((ROOT / "site" / "data" / "ai-visibility-actions.json").read_text())

        _spec.loader.exec_module(plugin)
        p = _load_plugin(kb_data, tmp_path)

        con = sqlite3.connect(f"file:{p.DB_PATH}?mode=ro", uri=True)
        row = con.execute(
            "SELECT target, domain, generated_at, answers, mention_pct, first_pct, share_of_voice_pct "
            "FROM ai_visibility_summary"
        ).fetchone()
        assert row == (
            scores["target"],
            scores["domain"],
            scores["generatedAt"],
            str(scores["overall"]["answers"]),
            str(scores["overall"]["mentionPct"]),
            str(scores["overall"]["firstPct"]),
            str(scores["overall"]["shareOfVoicePct"]),
        )

        assert con.execute("SELECT COUNT(*) FROM ai_visibility_models").fetchone()[0] == len(scores["models"])
        assert con.execute("SELECT COUNT(*) FROM ai_visibility_competitors").fetchone()[0] == len(scores["competitors"])
        assert con.execute("SELECT COUNT(*) FROM ai_visibility_questions").fetchone()[0] == len(scores["questions"])
        assert con.execute("SELECT COUNT(*) FROM ai_visibility_actions").fetchone()[0] == sum(
            len(group["actions"]) for group in actions["groups"]
        )

        row = con.execute(
            "SELECT mention_pct, wins, avg_rank FROM ai_visibility_competitors WHERE name='Yardi'"
        ).fetchone()
        yardi = next(row for row in scores["competitors"] if row["name"] == "Yardi")
        assert row == (str(yardi["mentionPct"]), str(yardi["wins"]), str(yardi["avgRank"]))

        row = con.execute(
            "SELECT priority, title, based_on FROM ai_visibility_actions ORDER BY priority, action_order LIMIT 1"
        ).fetchone()
        con.close()
        assert row[1]
        assert actions["basedOn"] in row[2]
