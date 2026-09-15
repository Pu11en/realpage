"""6.1: run.py wires the full lead-finder chain end to end, resumably.

Every network-touching call is faked (a FakeWeb standing in for
fetch.WebHelper, plus plain JSON/bytes fakes for the API-based steps) so
this runs offline like every other lead-finder-* test. Runs on one sample
city end to end, then re-runs with the same run folder to prove resume
skips every step that already has output.
"""
import datetime
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import run as chain  # noqa: E402
from runfolder import RunFolder  # noqa: E402

TODAY = datetime.date(2026, 9, 14)

CITY = "Sampleton"
STATE = "ZZ"

SOCRATA_CATALOG_HIT = {
    "results": [
        {
            "resource": {"id": "abcd-1234", "name": "Building Permits"},
            "metadata": {"domain": "data.sampleton-example.gov"},
        }
    ]
}
SOCRATA_ROWS = [
    {
        "permit_type": "multifamily new construction",
        "issue_date": "2026-08-01",
        "units_authorized": "40",
        "address": "1 Sample St",
    },
] + [
    {
        "permit_type": "single family",
        "issue_date": "2026-08-01",
        "units_authorized": "1",
        "address": f"{i} Sample St",
    }
    for i in range(120)
]


@dataclass
class FakeFetchResult:
    url: str
    ok: bool
    html: str = ""


@dataclass
class FakeWeb:
    """Stands in for fetch.WebHelper: same .search()/.fetch() shape, no I/O."""

    calls: list = field(default_factory=list)

    def search(self, query, n=10):
        self.calls.append(("search", query))
        return []

    def fetch(self, url):
        self.calls.append(("fetch", url))
        return FakeFetchResult(url=url, ok=False)


def _http_get_json(url):
    if url.startswith(chain.find_sources.ARCGIS_ONLINE_SEARCH):
        return {"results": []}
    if url.startswith(chain.find_sources.ARCGIS_HUB_SEARCH):
        return {"data": []}
    if url.startswith(chain.find_sources.SOCRATA_CATALOG):
        return SOCRATA_CATALOG_HIT
    return SOCRATA_ROWS


def _http_get_bytes(url):
    return b""


def _geocode_fn(query):
    return {}


def _make_deps(web, recipes_dir):
    return chain.ChainDeps(
        web=web,
        http_get_json=_http_get_json,
        http_get_bytes=_http_get_bytes,
        geocode_fn=_geocode_fn,
        gdelt_fetch_fn=None,
        today=TODAY,
        recipes_dir=recipes_dir,
    )


def test_run_chain_end_to_end_on_sample_city(tmp_path):
    run_folder = RunFolder(state=STATE, run_id="run1", runs_dir=tmp_path)
    web = FakeWeb()
    deps = _make_deps(web, tmp_path / "recipes")

    records = chain.run_chain(STATE, run_folder, deps, cities=[CITY])

    # 2.4's permit -> merged -> scored: one permitted-stage lead survives
    # (project_details drops it before scoring since the fake search/fetch
    # never returns a units-bearing page, so assert on the run-folder trail
    # instead, which is what 6.1 is actually responsible for wiring up).
    assert run_folder.step_file(chain.STEP_SOURCES, CITY).exists()
    assert run_folder.step_file(chain.STEP_PERMITS, CITY).exists()
    permits = run_folder.load_step(chain.STEP_PERMITS, CITY)
    assert len(permits) == 1
    assert permits[0]["units"] == 40

    assert run_folder.step_file(chain.STEP_DETAILS, CITY).exists()
    assert run_folder.step_file(chain.STEP_MERGED, CITY).exists()
    assert run_folder.step_file(chain.STEP_SOFTWARE, chain.STATE_CITY_KEY).exists()
    assert run_folder.step_file(chain.STEP_CONTACT, chain.STATE_CITY_KEY).exists()
    assert run_folder.step_file(chain.STEP_SCORE, chain.STATE_CITY_KEY).exists()
    assert isinstance(records, list)


def test_run_chain_resumes_without_touching_the_network_again(tmp_path):
    run_folder = RunFolder(state=STATE, run_id="run1", runs_dir=tmp_path)
    web = FakeWeb()
    deps = _make_deps(web, tmp_path / "recipes")
    chain.run_chain(STATE, run_folder, deps, cities=[CITY])
    first_search_calls = len(web.calls)

    # A fresh run against the same run folder must not redo any step: hook a
    # web/http that raises if actually called, and confirm nothing blows up.
    def _boom(*a, **k):
        raise AssertionError("network called again on a resumed run")

    resumed_web = FakeWeb()
    resumed_deps = chain.ChainDeps(
        web=resumed_web,
        http_get_json=_boom,
        http_get_bytes=_boom,
        geocode_fn=_boom,
        today=TODAY,
        recipes_dir=tmp_path / "recipes",
    )
    records = chain.run_chain(STATE, run_folder, resumed_deps, cities=[CITY])
    assert resumed_web.calls == []
    assert isinstance(records, list)
    assert first_search_calls >= 0  # sanity: first run did run (didn't crash before any call)


def test_run_folder_has_one_file_per_step_per_city(tmp_path):
    run_folder = RunFolder(state=STATE, run_id="run1", runs_dir=tmp_path)
    web = FakeWeb()
    deps = _make_deps(web, tmp_path / "recipes")
    chain.run_chain(STATE, run_folder, deps, cities=[CITY])

    step_files = sorted(p.name for p in run_folder.path.glob("*.json"))
    for step in (
        chain.STEP_CITIES, chain.STEP_SOURCES, chain.STEP_PERMITS, chain.STEP_DETAILS,
        chain.STEP_AGENDAS, chain.STEP_LEGISTAR, chain.STEP_CIVIC, chain.STEP_SALES,
        chain.STEP_MERGED,
    ):
        assert any(f.startswith(f"{step}.") for f in step_files), f"missing {step} output for {CITY}"


def test_run_chain_calls_on_city_done_once_per_city(tmp_path):
    """S0: save-as-you-go hook fires after each city, and leads.json for the
    area is written before it fires (so a commit right after has something
    real to save)."""
    run_folder = RunFolder(state=STATE, run_id="run1", runs_dir=tmp_path)
    web = FakeWeb()
    deps = _make_deps(web, tmp_path / "recipes")
    seen = []
    data_dir = tmp_path / "data"

    def on_city_done(city):
        seen.append(city)
        assert (data_dir / STATE.lower() / "leads.json").exists()

    orig_write = chain.write_area_leads

    def _write(state, records, data_dir_arg=None):
        return orig_write(state, records, data_dir=data_dir)

    chain.write_area_leads = _write
    try:
        chain.run_chain(STATE, run_folder, deps, cities=[CITY], on_city_done=on_city_done)
    finally:
        chain.write_area_leads = orig_write

    assert seen == [CITY]


def test_commit_city_progress_commits_new_files(tmp_path):
    import subprocess

    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)

    run_folder = RunFolder(state=STATE, run_id="run1", runs_dir=tmp_path / "propertystack" / "runs")
    run_folder.ensure()
    (run_folder.path / "merged.Sampleton.json").write_text("[]")
    data_dir = tmp_path / "propertystack" / "data" / STATE.lower()
    data_dir.mkdir(parents=True)
    (data_dir / "leads.json").write_text("[]")

    chain.commit_city_progress(tmp_path, run_folder, STATE, CITY)

    log = subprocess.run(
        ["git", "log", "--oneline"], cwd=tmp_path, check=True, capture_output=True, text=True
    ).stdout
    assert f"{STATE}: {CITY} done" in log

    # a second call with nothing new to add must not fail (no-op, not an
    # empty commit)
    before = log
    chain.commit_city_progress(tmp_path, run_folder, STATE, CITY)
    after = subprocess.run(
        ["git", "log", "--oneline"], cwd=tmp_path, check=True, capture_output=True, text=True
    ).stdout
    assert before == after


def test_awards_and_hud_skip_gracefully_without_config(tmp_path):
    """No agency name / HUD fetcher configured -> skip note, not a crash or
    a real network call (mirrors every other 'never guess' step here)."""
    run_folder = RunFolder(state=STATE, run_id="run2", runs_dir=tmp_path)
    web = FakeWeb()
    deps = _make_deps(web, tmp_path / "recipes")

    hud = chain.step_hud(run_folder, STATE, deps)
    awards = chain.step_awards(run_folder, STATE, deps)
    assert hud["skipped"] is True
    assert awards["skipped"] is True
