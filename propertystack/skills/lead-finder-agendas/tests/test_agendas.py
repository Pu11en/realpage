"""lead-finder-agendas (3.3) tests: fake search + fetch, no network."""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import agendas  # noqa: E402


def test_legistar_identified_from_url_and_saved(tmp_path):
    results = [{"url": "https://rivertown.legistar.com/Calendar.aspx", "title": "Meeting Calendar"}]

    def search_fn(query):
        return results

    def fetch_fn(url):
        raise AssertionError("should not need to fetch when URL matches")

    recipe = agendas.find_meeting_system("Rivertown", "TX", search_fn, fetch_fn, recipes_dir=tmp_path)
    assert recipe["system"] == "legistar"
    assert recipe["city"] == "Rivertown"
    saved = json.loads((tmp_path / "agendas-rivertown.json").read_text())
    assert saved == recipe


def test_system_identified_from_page_html_not_just_url(tmp_path):
    results = [{"url": "https://cedarville-example.gov/planning/agendas", "title": "Planning Agendas"}]

    def search_fn(query):
        return results

    def fetch_fn(url):
        return "<html>Powered by PrimeGov</html>"

    recipe = agendas.find_meeting_system("Cedarville", "TX", search_fn, fetch_fn, recipes_dir=tmp_path)
    assert recipe["system"] == "primegov"


def test_nothing_found_online_returns_skip_note_and_saves_nothing(tmp_path):
    def search_fn(query):
        return [{"url": "https://oakford-example.gov/about", "title": "About the city"}]

    def fetch_fn(url):
        return "<html>Welcome to our city</html>"

    result = agendas.find_meeting_system("Oakford", "TX", search_fn, fetch_fn, recipes_dir=tmp_path)
    assert result == {"city": "Oakford", "state": "TX", "skipped": True, "reason": "no agenda system identified"}
    assert not list(tmp_path.glob("*.json"))


def test_identify_system_directly():
    assert agendas.identify_system("https://rivertown.legistar.com/x") == "legistar"
    assert agendas.identify_system("/AgendaCenter/planning") == "agendacenter"
    assert agendas.identify_system("nothing here") is None


def test_slugify():
    assert agendas.slugify("Oakford County") == "oakford-county"


def test_saved_recipe_is_reused_across_calls_without_searching_again(tmp_path):
    """S2: agenda-system detection is cached across runs (a new run-id
    starts a fresh run folder, but this cache lives under recipes_dir,
    outside any run folder), so a later call for the same city never
    re-searches or re-fetches."""
    results = [{"url": "https://rivertown.legistar.com/Calendar.aspx", "title": "Meeting Calendar"}]
    calls = []

    def search_fn(query):
        calls.append(query)
        return results

    def fetch_fn(url):
        raise AssertionError("should not need to fetch when URL matches")

    first = agendas.find_meeting_system("Rivertown", "TX", search_fn, fetch_fn, recipes_dir=tmp_path)
    assert len(calls) == 1

    def search_fn_should_not_be_called(query):
        raise AssertionError("cached recipe should have been used instead of searching again")

    second = agendas.find_meeting_system(
        "Rivertown", "TX", search_fn_should_not_be_called, fetch_fn, recipes_dir=tmp_path
    )
    assert second == first
    assert len(calls) == 1
