"""H2: recruiter evidence is reproducible, plainly historical, and auditable."""
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "site" / "data"
PAGE = (ROOT / "site" / "under-the-hood.html").read_text(encoding="utf-8")


def read_json(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def test_historical_scorecard_rebuilds_without_an_old_worktree():
    """The public values must survive after the disposable eval worktree is gone."""
    subprocess.run(["python3", str(DATA / "build_evals.py")], cwd=ROOT, check=True)

    scorecard = read_json("recruiter-scorecard.json")
    assert scorecard["evidence_status"] == "Historical recruiter scorecard — not a current release approval"
    assert read_json("evals.json") == scorecard["evals"]
    assert read_json("chat-stats.json") == scorecard["chat_stats"]


def test_every_headline_measure_has_a_sample_and_matches_saved_evidence():
    scorecard = read_json("recruiter-scorecard.json")
    evals = scorecard["evals"]
    chat = scorecard["chat_stats"]

    assert (evals["checks_passed"], evals["checks_total"]) == (1, 6)
    assert (evals["failure_types"]["ok_count"], evals["failure_types"]["n"]) == (92, 100)
    assert evals["human_review"]["n_reviewed"] == 17
    assert chat["n_answers"] == 105
    assert evals["measured_at"] == chat["measured_at"] == "2026-09-15"
    assert "n=${checksTotal}" in PAGE
    assert "n=${failureTypes.n}" in PAGE
    assert "n=${reviewN}" in PAGE
    assert "n=${chatN}" in PAGE


def test_page_shows_historical_status_method_and_open_limits_not_an_inferred_claim():
    for required in [
        'loadData("data/recruiter-scorecard.json")',
        "Historical status:",
        "Method:",
        "Open limitations",
        "approval to release the current product",
    ]:
        assert required in PAGE
    assert "passed check first try" not in PAGE
    assert "firstTryPct" not in PAGE


def test_public_evidence_has_no_machine_paths():
    for path in [DATA / "recruiter-scorecard.json", DATA / "evals.json", DATA / "chat-stats.json"]:
        assert "/home/" not in path.read_text(encoding="utf-8")
        assert "source_dir" not in path.read_text(encoding="utf-8")
    assert "/home/" not in (DATA / "build_evals.py").read_text(encoding="utf-8")
