import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agenda_projects import agenda_hits_to_projects, hit_to_project  # noqa: E402


@dataclass
class FakeHit:
    url: str
    text: str


def test_kept_when_address_present():
    hit = FakeHit(url="https://x/packet.pdf", text="Site plan for 123 Main St, 180 units, Applicant: Acme Development LLC")
    record = hit_to_project(hit, area="tx", city="Somecity")
    assert record is not None
    assert record.address.lower().startswith("123 main")
    assert record.units == 180
    assert "Acme Development" in record.developer
    assert record.stage == "planned"
    assert record.links["agenda"] == hit.url


def test_kept_when_case_number_present():
    hit = FakeHit(url="https://x/1", text="Rezoning request Z-2025-0042 for a new apartment complex")
    record = hit_to_project(hit, area="tx", city="Somecity")
    assert record is not None
    assert "Z-2025-0042" in record.why


def test_dropped_when_neither_address_nor_case():
    hit = FakeHit(url="https://x/1", text="General discussion of multifamily housing policy citywide")
    assert hit_to_project(hit, area="tx", city="Somecity") is None


def test_pulls_name_when_present():
    hit = FakeHit(url="https://x/1", text="123 Main St -- Sunset Ridge Apartments, 200 units, rezoning request")
    record = hit_to_project(hit, area="tx", city="Somecity")
    assert record.name == "Sunset Ridge Apartments"


def test_merges_same_case_across_two_meetings():
    hits = [
        FakeHit(url="https://x/pz", text="Case Z-2025-0099: 456 Oak Ave rezoning, 150 units, Developer: Beta Builders"),
        FakeHit(url="https://x/council", text="Case Z-2025-0099 council approval, 456 Oak Ave"),
    ]
    projects = agenda_hits_to_projects(hits, area="tx", city="Somecity")
    assert len(projects) == 1
    assert projects[0].units == 150
    assert "Beta Builders" in projects[0].developer


def test_merges_by_address_when_no_case_number():
    hits = [
        FakeHit(url="https://x/1", text="789 Elm Rd apartment site plan, 90 units"),
        FakeHit(url="https://x/2", text="789 Elm Rd -- final approval"),
    ]
    projects = agenda_hits_to_projects(hits, area="tx", city="Somecity")
    assert len(projects) == 1


def test_two_different_cases_stay_separate_projects():
    hits = [
        FakeHit(url="https://x/1", text="Case Z-2025-0001: 111 First St apartments, 80 units"),
        FakeHit(url="https://x/2", text="Case Z-2025-0002: 222 Second St apartments, 60 units"),
    ]
    projects = agenda_hits_to_projects(hits, area="tx", city="Somecity")
    assert len(projects) == 2


def test_no_hits_returns_empty_list():
    assert agenda_hits_to_projects([], area="tx", city="Somecity") == []


def test_all_weak_hits_dropped_returns_empty_list():
    hits = [FakeHit(url="https://x/1", text="Housing policy update, no specifics")]
    assert agenda_hits_to_projects(hits, area="tx", city="Somecity") == []
