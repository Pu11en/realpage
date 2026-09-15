"""C4: a source opens a page a person can read. Raw ArcGIS/Socrata query URLs
become the dataset's public page, and internal tags like "[county record]" or
"[houston-weekly-xlsx]" become plain names. Offline: reads the built data."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "site/data"))
import build_data  # noqa: E402

RAW_API = re.compile(
    r"(query\?|\.json\?|/rest/services|FeatureServer|MapServer|arcgis\.com/sharing/rest|resource/[a-z0-9-]+\.json)",
    re.I,
)
INTERNAL = {"county record", "website", "news", "permit", "houston-weekly-xlsx"}


def _rows(slug):
    return json.loads((ROOT / f"site/data/areas/{slug}.json").read_text())["leads"]


def _all_sources():
    for slug in ("tx", "az", "ny"):
        for l in _rows(slug):
            for s in l.get("sources") or []:
                yield slug, l["id"], s


def test_every_source_has_a_plain_label_and_no_raw_query():
    for slug, lid, s in _all_sources():
        assert isinstance(s, dict), (slug, lid, s)
        assert s.get("label"), (slug, lid, s)
        assert not RAW_API.search(s.get("url") or ""), (slug, lid, s)
        assert s["label"] not in INTERNAL, (slug, lid, s)
        assert not s["label"].startswith("["), (slug, lid, s)


def test_known_datasets_map_to_public_pages():
    labels = {s["label"] for _, _, s in _all_sources()}
    for expected in (
        "City of Mesa building permits",
        "City of Scottsdale building permits",
        "City of Tempe building permits",
        "City of Phoenix planning permits",
        "Town of Gilbert building permits",
        "City of Tucson building permits",
        "Maricopa County building permits",
        "Maricopa County Assessor sales records",
        "City of San Marcos building permits",
        "City of Fort Worth development permits",
        "City of Buffalo building permits",
        "Texas county property records",
        "Houston weekly permit list",
    ):
        assert expected in labels, expected


def test_mapping_offline():
    mesa = build_data.source_entry(
        "https://data.mesaaz.gov/resource/dzpk-hxfb.json?type_of_work=Multi-Family+Residential"
    )
    assert mesa["label"] == "City of Mesa building permits"
    assert mesa["url"].startswith("https://data.mesaaz.gov/")

    tx = build_data.source_entry("https://data.texas.gov/resource/5tkr-3759.json?$where=1")
    assert tx["label"] == "Texas county property records"
    assert tx["url"] == "https://data.texas.gov/d/5tkr-3759"

    assert build_data.source_entry("houston-weekly-xlsx")["label"] == "Houston weekly permit list"
    assert build_data.source_entry("county record")["label"] == "County property records"

    # A link that is already a page a person can open keeps its URL, with a label.
    tdlr = build_data.source_entry("https://www.tdlr.texas.gov/TABS/Search/Project/TABS2025001287")
    assert tdlr["url"].startswith("https://www.tdlr.texas.gov/") and tdlr["label"] == "State project record"


def test_frontend_never_brackets_a_source():
    index = (ROOT / "site/index.html").read_text()
    assert "[${s}]" not in index and "sourceLinks(" in index
    assert "sourceItems(" in (ROOT / "site/property.html").read_text()
