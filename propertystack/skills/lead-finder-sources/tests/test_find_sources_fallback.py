"""lead-finder-sources (2.3) tests: fake search + fetch, no network."""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import find_sources_fallback as fsf  # noqa: E402


ACCELA_HTML = (
    "<html><body>" +
    "".join(f"<tr>Permit No: {1000 + i} - multifamily apartment new construction</tr>" for i in range(6)) +
    "</body></html>"
)

NO_PERMIT_HTML = "<html><body>Welcome to our city</body></html>"

REPORT_PDF_TEXT = "".join(f"Permit # {2000 + i} multifamily\n" for i in range(6))


def test_accela_portal_marked_no_free_data(tmp_path):
    """Accela is a portal-only, permit-by-permit lookup with no bulk free data --
    it must be marked "no free data" and never treated as a usable recipe."""
    results = [{"url": "https://aca-prod.accela.com/RIVERTOWN/Default.aspx", "title": "Citizen Access"}]

    def search_fn(query):
        return results

    def fetch_fn(url):
        return ACCELA_HTML

    result = fsf.find_sources_fallback("Rivertown", "TX", search_fn, fetch_fn, recipes_dir=tmp_path)
    assert result["skipped"] is True
    assert result["no_retry"] is True
    assert "accela" in result["reason"]
    assert not list(tmp_path.glob("*.json"))


def test_system_identified_from_page_html_not_just_url(tmp_path):
    results = [{"url": "https://permits.cedarville-example.gov/portal", "title": "Permits"}]

    def search_fn(query):
        return results

    def fetch_fn(url):
        return "<html>Powered by Tyler EnerGov CSS</html>" + ACCELA_HTML

    result = fsf.find_sources_fallback("Cedarville", "TX", search_fn, fetch_fn, recipes_dir=tmp_path)
    assert result["skipped"] is True
    assert "tyler-energov" in result["reason"]


def test_too_few_sample_permits_rejected_then_report_file_used(tmp_path):
    results = [
        {"url": "https://aca-prod.accela.com/OAKFORD/Default.aspx", "title": "Citizen Access"},
        {"url": "https://oakford-example.gov/permits/monthly-report.pdf", "title": "Monthly Permit Report"},
    ]

    def search_fn(query):
        return results

    def fetch_fn(url):
        if url.endswith(".pdf"):
            return REPORT_PDF_TEXT
        return NO_PERMIT_HTML  # accela URL matches system but page has no permit rows

    recipe = fsf.find_sources_fallback("Oakford", "TX", search_fn, fetch_fn, recipes_dir=tmp_path)
    assert recipe["system"] == "report-file"
    assert recipe["endpoint"].endswith(".pdf")


def test_nothing_found_online_returns_skip_note_and_saves_nothing(tmp_path):
    def search_fn(query):
        return [{"url": "https://oakford-example.gov/about", "title": "About the city"}]

    def fetch_fn(url):
        return NO_PERMIT_HTML

    result = fsf.find_sources_fallback("Oakford", "TX", search_fn, fetch_fn, recipes_dir=tmp_path)
    assert result == {"city": "Oakford", "state": "TX", "skipped": True, "reason": "no permits online"}
    assert not list(tmp_path.glob("*.json"))


def test_identify_system_and_counters_directly():
    assert fsf.identify_system("https://aca-prod.accela.com/x") == "accela"
    assert fsf.identify_system("https://cityname.smartgovcommunity.com/x") == "smartgov"
    assert fsf.identify_system("nothing here") is None
    assert fsf.count_sample_permits(ACCELA_HTML) == 6
    assert fsf.count_multifamily_hits(ACCELA_HTML) == 12  # "multifamily" and "apartment" both match per row


def test_slugify():
    assert fsf.slugify("Oakford County") == "oakford-county"
