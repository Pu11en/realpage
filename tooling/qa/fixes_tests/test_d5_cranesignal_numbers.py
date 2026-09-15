"""D5: CraneSignal's own Under the Hood numbers load into the chat as
`cranesignal_*` tables, with values matching site/data exactly."""
import importlib.util
import json
import pathlib
import sqlite3
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tooling" / "chat-data"))
import build_cranesignal_numbers  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "propertystack_plugin", ROOT / "chatbot" / "hermes-profile" / "plugins" / "propertystack" / "__init__.py"
)
plugin = importlib.util.module_from_spec(_spec)


EXPECTED_TABLES = {
    "cranesignal_pipeline_steps",
    "cranesignal_pipeline_runs",
    "cranesignal_review_reasons",
    "cranesignal_review_queue",
    "cranesignal_accuracy_docs",
    "cranesignal_chat_stats",
    "cranesignal_how_tested",
    "cranesignal_eval_summary",
    "cranesignal_eval_failure_types",
    "cranesignal_buildbot_summary",
    "cranesignal_buildbot_examples",
}


def _build_kb(tmp_path):
    kb_data = tmp_path / "kb-data"
    kb_data.mkdir()
    numbers_kb = tmp_path / "numbers-kb"
    build_cranesignal_numbers.build(out_dir=numbers_kb)
    for csv_path in numbers_kb.glob("*.csv"):
        (kb_data / csv_path.name).write_bytes(csv_path.read_bytes())
    return kb_data


def _load_plugin(kb_data, tmp_path):
    plugin.DATA_DIR = kb_data
    plugin.DB_PATH = tmp_path / "test.db"
    plugin._build_db()
    return plugin


def test_dockerfile_copies_cranesignal_numbers_kb():
    dockerfile = (ROOT / "chatbot" / "Dockerfile").read_text()
    assert "propertystack/data/cranesignal-build/kb" in dockerfile


def test_cranesignal_tables_load_with_sources():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = pathlib.Path(tmp)
        kb_data = _build_kb(tmp_path)
        _spec.loader.exec_module(plugin)
        p = _load_plugin(kb_data, tmp_path)

        tables = {t["table"] for t in p.SCHEMA}
        assert EXPECTED_TABLES <= tables
        source_names = {t["table"]: t["source_name"] for t in p.SCHEMA}
        assert source_names["cranesignal_chat_stats"] == "CraneSignal chat speed measurements"

        con = sqlite3.connect(f"file:{p.DB_PATH}?mode=ro", uri=True)
        row = con.execute("SELECT n_answers, measured_at FROM cranesignal_chat_stats").fetchone()
        con.close()
        assert row == ("105", "2026-09-15")


def test_cranesignal_tables_match_site_json():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = pathlib.Path(tmp)
        kb_data = _build_kb(tmp_path)

        pipeline = json.loads((ROOT / "site" / "data" / "pipeline.json").read_text())
        chat_stats = json.loads((ROOT / "site" / "data" / "chat-stats.json").read_text())
        evals = json.loads((ROOT / "site" / "data" / "evals.json").read_text())
        buildbot = json.loads((ROOT / "site" / "data" / "buildbot.json").read_text())

        _spec.loader.exec_module(plugin)
        p = _load_plugin(kb_data, tmp_path)

        con = sqlite3.connect(f"file:{p.DB_PATH}?mode=ro", uri=True)
        assert con.execute("SELECT COUNT(*) FROM cranesignal_pipeline_steps").fetchone()[0] == len(pipeline["steps"])
        assert con.execute("SELECT COUNT(*) FROM cranesignal_pipeline_runs").fetchone()[0] == len(pipeline["runs"])
        assert con.execute("SELECT COUNT(*) FROM cranesignal_review_queue").fetchone()[0] == len(pipeline["reviewQueue"]["rows"])
        assert con.execute("SELECT COUNT(*) FROM cranesignal_how_tested").fetchone()[0] >= 6

        row = con.execute(
            "SELECT p50_seconds, p95_seconds, measured_at FROM cranesignal_chat_stats"
        ).fetchone()
        assert row == (str(chat_stats["p50_seconds"]), str(chat_stats["p95_seconds"]), chat_stats["measured_at"])

        row = con.execute(
            "SELECT test_answers_total, test_answers_correct, human_reviewed, human_review_agreement_pct, "
            "measured_at FROM cranesignal_eval_summary"
        ).fetchone()
        assert row == (
            str(evals["failure_types"]["n"]),
            str(evals["failure_types"]["ok_count"]),
            str(evals["human_review"]["n_reviewed"]),
            str(evals["human_review"]["agreement_pct"]),
            evals["measured_at"],
        )

        row = con.execute(
            "SELECT plans, steps_done, first_try_pct, commits, measured_at FROM cranesignal_buildbot_summary"
        ).fetchone()
        con.close()
        assert row == (
            str(buildbot["plans"]),
            str(buildbot["steps_done"]),
            str(buildbot["first_try_pct"]),
            str(buildbot["commits"]),
            buildbot["measured_at"],
        )


def test_chat_numbers_drop_internal_scorecard():
    with tempfile.TemporaryDirectory() as tmp:
        out = pathlib.Path(tmp)
        build_cranesignal_numbers.build(out_dir=out)
        assert not (out / "cranesignal-eval-checks.csv").exists()
        text = "".join(p.read_text() for p in out.glob("*.csv"))
        for internal in ["false_alarm", "checks_passed", "PLACEHOLDER"]:
            assert internal not in text, internal
