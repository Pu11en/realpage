"""SEO: the answer-share sampler and its question bank.

Offline by construction. Nothing here calls Claude, Gemini or the network -- the two
`ask_*` functions are the only code that would, and these tests never reach them. The
reading and reporting logic is exercised against hand-written records instead, the same
way `archive/realpage/ai-visibility/tooling/fake_ai.py` did for the earlier run.
"""
import csv
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SEO = ROOT / "tooling" / "seo"
QUESTIONS = SEO / "questions.csv"


def load_module():
    spec = importlib.util.spec_from_file_location("seo_sample", SEO / "sample.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["seo_sample"] = module
    spec.loader.exec_module(module)
    return module


sample = load_module()


# ---------------------------------------------------------------- the question bank


def test_question_bank_is_all_lead_finding_and_has_no_duplicates():
    rows = list(csv.DictReader(QUESTIONS.open(encoding="utf-8")))
    assert len(rows) >= 25
    questions = [row["question"].strip().lower() for row in rows]
    assert len(questions) == len(set(questions)), "duplicate question in questions.csv"
    for row in rows:
        assert row["question"].strip().endswith("?"), row["question"]
        assert row["intent"].strip(), f"no intent for: {row['question']}"


def test_no_question_asks_which_software_to_buy():
    """CraneSignal sells lead data on buildings. "Best PMS for 200 units" measures
    RealPage's market, not ours -- it came from the archived project and was removed
    2026-09-23 on David's correction. If it creeps back, the report stops being about us.
    """
    rows = list(csv.DictReader(QUESTIONS.open(encoding="utf-8")))
    for row in rows:
        q = row["question"].lower()
        buying = ("best" in q or "better" in q or "compare" in q or " vs " in q)
        about_software = "software" in q or "system" in q or "platform" in q
        if buying and about_software:
            raise AssertionError(f"software-purchase question in the bank: {row['question']}")


def test_the_bank_covers_the_intents_the_product_claims():
    intents = {row["intent"] for row in csv.DictReader(QUESTIONS.open(encoding="utf-8"))}
    for needed in ("pipeline", "sales", "prospecting", "free-data"):
        assert needed in intents, f"no {needed} questions"


# ---------------------------------------------------------------- reading an answer


def test_brands_in_finds_names_and_ranks_them_by_first_appearance():
    text = "Try CoStar first. Yardi Matrix is another option, and Reonomy also has data."
    found = sample.brands_in(text)
    names = [item["brand"] for item in found]
    assert names[:3] == ["CoStar", "Yardi Matrix", "Reonomy"], names
    assert [item["rank"] for item in found][:3] == [1, 2, 3]


def test_brands_in_is_case_insensitive_and_counts_repeats():
    found = sample.brands_in("costar is big. CoStar again. Reonomy once.")
    by_name = {item["brand"]: item for item in found}
    assert by_name["CoStar"]["mentions"] == 2
    assert by_name["Reonomy"]["mentions"] == 1


def test_brands_in_returns_nothing_for_an_answer_that_names_nobody():
    assert sample.brands_in("It depends on the building and the local market.") == []


def test_go_read_the_records_yourself_is_counted_as_an_answer():
    """An engine that says "check the appraisal district" is one step from citing a
    site that has already read it. That is the opening, so it gets counted."""
    found = sample.brands_in("Check your county appraisal district or the permit office.")
    assert [item["brand"] for item in found] == ["Public records (DIY)"]


def test_cranesignal_is_tracked_under_both_spellings():
    assert sample.brands_in("CraneSignal lists them")[0]["brand"] == "CraneSignal"
    assert sample.brands_in("crane signal lists them")[0]["brand"] == "CraneSignal"


def test_host_of_prefers_the_real_domain_over_a_redirect():
    """Gemini's grounding links are Vertex redirects that say nothing; the title holds
    the domain the engine actually read."""
    link = {
        "title": "costar.com",
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/abc123",
    }
    assert sample.host_of(link) == "costar.com"


def test_host_of_falls_back_to_the_url_when_there_is_no_domain_title():
    link = {"title": "Some article headline", "url": "https://www.multifamilydive.com/news/x"}
    assert sample.host_of(link) == "multifamilydive.com"


def test_urls_in_dedupes_by_host_and_strips_trailing_punctuation():
    text = "See https://costar.com/a, https://costar.com/b and https://yardi.com/c."
    urls = sample.urls_in(text)
    assert urls == ["https://costar.com/a", "https://yardi.com/c"], urls


# ---------------------------------------------------------------- the report


@pytest.fixture
def run_dir(tmp_path):
    """A small saved run with a known shape: CraneSignal absent, competitors present."""
    records = [
        {
            "engine": "gemini", "set": "A", "ok": True,
            "question": "How do I find apartment buildings under construction in Dallas?",
            "answer": "Use CoStar or Yardi Matrix.",
            "brands": sample.brands_in("Use CoStar or Yardi Matrix."),
            "links": [{"title": "costar.com", "url": "https://vertexaisearch.cloud.google.com/x"}],
        },
        {
            "engine": "claude-web", "set": "A", "ok": True,
            "question": "How do I find apartment buildings under construction in Dallas?",
            "answer": "Yardi Matrix is the usual answer; CoStar too.",
            "brands": sample.brands_in("Yardi Matrix is the usual answer; CoStar too."),
            "links": [{"title": "yardimatrix.com", "url": "https://yardimatrix.com/a"}],
        },
        {
            "engine": "gemini", "set": "A", "ok": True,
            "question": "How can I find out who bought an apartment complex?",
            "answer": "Reonomy and the county appraisal district both show the buyer.",
            "brands": sample.brands_in("Reonomy and the county appraisal district both show the buyer."),
            "links": [{"title": "reonomy.com", "url": "https://reonomy.com/x"}],
        },
        {
            "engine": "claude-web", "set": "A", "ok": False,
            "question": "How can I find out who bought an apartment complex?",
            "error": "timed out after 300s",
        },
    ]
    for i, record in enumerate(records):
        (tmp_path / f"{record['engine']}-{i}.json").write_text(
            json.dumps(record), encoding="utf-8"
        )
    return tmp_path


def test_report_states_the_cranesignal_count_plainly(run_dir):
    rows = list(csv.DictReader(QUESTIONS.open(encoding="utf-8")))
    report = sample.build_report(run_dir, rows)
    assert "**CraneSignal is named in 0 of 3 answers.**" in report


def test_report_labels_the_engines_as_not_the_consumer_apps(run_dir):
    rows = list(csv.DictReader(QUESTIONS.open(encoding="utf-8")))
    report = sample.build_report(run_dir, rows)
    assert "not the consumer apps" in report.lower()


def test_report_lists_which_sites_were_cited(run_dir):
    rows = list(csv.DictReader(QUESTIONS.open(encoding="utf-8")))
    report = sample.build_report(run_dir, rows)
    assert "Which sites the engines actually read" in report
    assert "costar.com" in report and "reonomy.com" in report
    assert "vertexaisearch" not in report, "redirect hosts leaked into the report"


def test_report_surfaces_failed_questions_rather_than_hiding_them(run_dir):
    rows = list(csv.DictReader(QUESTIONS.open(encoding="utf-8")))
    report = sample.build_report(run_dir, rows)
    assert "did not get an answer" in report
    assert "timed out" in report


def test_report_counts_only_answers_that_succeeded(run_dir):
    rows = list(csv.DictReader(QUESTIONS.open(encoding="utf-8")))
    report = sample.build_report(run_dir, rows)
    # Three of the four records are ok; the failed one must not inflate the denominator.
    assert "Questions answered: 3" in report


# ---------------------------------------------------------------- the saved run


def test_the_committed_baseline_run_is_complete_and_honest():
    """The 2026-09-23 run is the before-picture the whole plan is measured against."""
    run = ROOT / "docs" / "seo" / "answer-share" / "2026-09-23"
    if not run.exists():
        pytest.skip("baseline run not present")
    records = [json.loads(p.read_text(encoding="utf-8")) for p in run.glob("*.json")]
    assert len(records) >= 40, f"only {len(records)} answers saved"
    assert all(r.get("ok") for r in records), "the committed baseline contains failures"
    assert all(r["is_consumer_app"] is False for r in records)
    named = [r for r in records if any(b["brand"] == "CraneSignal" for b in r.get("brands", []))]
    # Not an aspiration: if this ever fails, the SEO work has started to land.
    assert len(named) == 0, f"CraneSignal now appears in {len(named)} answers -- update the baseline note"
