import datetime as dt
import importlib.util
import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
MODULE_PATH = HERE.parent / "find_source.py"
SPEC = importlib.util.spec_from_file_location("find_source_skill", MODULE_PATH)
find_source = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = find_source
SPEC.loader.exec_module(find_source)

TODAY = dt.date(2026, 9, 19)


def _rows(count=6, *, address=True, date=True, apartment=True):
    rows = []
    for number in range(count):
        row = {
            "address": f"{number + 1}00 Main St" if address else "",
            "issued": "2026-09-01" if date else "",
            "units": 40 if apartment else 2,
            "description": "New apartment building" if apartment else "Fence repair",
        }
        rows.append(row)
    return rows


def test_recorded_responses_write_exact_auto_found_recipe_after_full_gate(tmp_path):
    replay = find_source.RecordedResponses.from_path(
        HERE.parent / "fixtures" / "recorded-responses.json"
    )
    result = find_source.find_source(
        "Exampleville",
        "NM",
        replay.search,
        replay.fetch,
        root=tmp_path,
        today=TODAY,
    )

    assert result.found
    assert result.searches == 1
    recipe_path = tmp_path / "propertystack/recipes/nm/exampleville.json"
    recipe = json.loads(recipe_path.read_text())
    assert recipe["endpoint"] == "https://data.example.test/permits.json"
    assert recipe["source"] == "auto-found"
    assert recipe["validation"]["apartment_rows"] == 6
    assert recipe["validation"]["lead_data_check"] == "passed"
    assert not (tmp_path / "propertystack/runs/needs-a-source.md").exists()


def test_searches_in_required_order_and_rejects_weak_candidate(tmp_path):
    calls = []
    weak_url = "https://data.example.test/too-small.json"
    good_url = "https://exampleville.example.test/arcgis/query"

    def search(stage, query, city, state):
        calls.append(stage)
        assert city == "Exampleville" and state == "NM"
        assert city in query and state in query
        if stage == "city-open-data":
            return [{"title": "Exampleville permits", "url": weak_url}]
        if stage == "socrata":
            return []
        if stage == "arcgis":
            return [{"title": "Exampleville permit layer", "url": good_url}]
        raise AssertionError("search continued after a source passed")

    def fetch(url):
        if url == weak_url:
            return _rows(4)
        return {"features": [{"attributes": row} for row in _rows()]}

    result = find_source.find_source(
        "Exampleville", "NM", search, fetch, root=tmp_path, today=TODAY
    )
    assert result.found
    assert calls == ["city-open-data", "socrata", "arcgis"]
    assert result.recipe["system"] == "arcgis"


def test_missing_required_facts_never_writes_recipe_and_records_need(tmp_path):
    candidates = {
        "city-open-data": _rows(address=False),
        "socrata": _rows(date=False),
        "arcgis": _rows(apartment=False),
    }

    def search(stage, _query, _city, _state):
        if stage not in candidates:
            return []
        return [{"title": "Exampleville permits", "url": f"https://example.test/{stage}.json"}]

    def fetch(url):
        return candidates[url.rsplit("/", 1)[-1].removesuffix(".json")]

    result = find_source.find_source(
        "Exampleville", "NM", search, fetch, root=tmp_path, today=TODAY
    )
    assert not result.found
    assert result.searches == len(find_source.SEARCH_STAGES)
    assert not list((tmp_path / "propertystack/recipes").rglob("*.json"))
    note = (tmp_path / "propertystack/runs/needs-a-source.md").read_text()
    assert "Exampleville, NM" in note
    assert "5 searches" in note


def test_per_city_and_whole_run_caps_return_cleanly(tmp_path):
    assert find_source.MAX_SEARCHES_PER_CITY == 20
    assert find_source.MAX_SEARCHES_PER_RUN == 100

    def no_results(_stage, _query, _city, _state):
        return []

    city_budget = find_source.SearchBudget(per_city_limit=2, run_limit=100)
    first = find_source.find_source(
        "Exampleville", "NM", no_results, lambda _url: [],
        root=tmp_path, budget=city_budget, today=TODAY,
    )
    assert not first.found and first.searches == 2
    assert "limit reached" in first.note

    run_budget = find_source.SearchBudget(per_city_limit=20, run_limit=1)
    second = find_source.find_source(
        "Sampletown", "NM", no_results, lambda _url: [],
        root=tmp_path, budget=run_budget, today=TODAY,
    )
    third = find_source.find_source(
        "Testborough", "NM", no_results, lambda _url: [],
        root=tmp_path, budget=run_budget, today=TODAY,
    )
    assert second.searches == 1
    assert third.searches == 0
    assert run_budget.total == 1


def test_batch_entry_point_owns_one_budget_and_never_starts_search_101(tmp_path):
    calls = []

    def no_results(stage, _query, city, state):
        calls.append((stage, city, state))
        return []

    locations = [(f"City {number}", "NM") for number in range(1, 22)]
    results = find_source.find_sources(
        locations,
        no_results,
        lambda _url: [],
        root=tmp_path,
        today=TODAY,
    )

    assert len(calls) == find_source.MAX_SEARCHES_PER_RUN == 100
    assert len(results) == 21
    assert results[-2].searches == len(find_source.SEARCH_STAGES)
    assert results[-1].searches == 0
    assert "limit reached" in results[-1].note


def test_cli_batches_city_state_pairs_through_shared_run_budget(tmp_path, monkeypatch):
    received = []

    def fake_find_sources(locations, _search_fn, _fetch_fn, **kwargs):
        received.extend(locations)
        assert kwargs["root"] == tmp_path
        return [
            find_source.FindResult(city, state, None, 0, "search limit reached")
            for city, state in locations
        ]

    monkeypatch.setattr(find_source, "find_sources", fake_find_sources)
    monkeypatch.setattr(find_source, "LiveSearch", lambda _root: lambda *_args: [])

    assert find_source.main([
        "Santa Fe", "NM", "Rio Rancho", "NM", "Austin", "TX", "--root", str(tmp_path)
    ]) == 0
    assert received == [("Santa Fe", "NM"), ("Rio Rancho", "NM"), ("Austin", "TX")]


def test_unrelated_search_result_is_not_fetched(tmp_path):
    fetched = []

    def search(_stage, _query, _city, _state):
        return [{"title": "Another jurisdiction permits", "url": "https://other.example.test/data"}]

    def fetch(url):
        fetched.append(url)
        return _rows()

    result = find_source.find_source(
        "Exampleville", "NM", search, fetch, root=tmp_path, today=TODAY
    )
    assert not result.found
    assert fetched == []
