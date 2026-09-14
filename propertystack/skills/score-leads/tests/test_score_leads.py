import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lead-finder"))

from record import LeadRecord  # noqa: E402
from score_leads import score_and_rank  # noqa: E402


def _lead(**kwargs) -> LeadRecord:
    base = dict(area="tx", city="Somecity")
    base.update(kwargs)
    return LeadRecord(**base)


def test_active_leads_rank_before_sold_and_planned():
    leads = [
        _lead(name="Planned One", stage="planned", units=100),
        _lead(name="Sold One", stage="sold", sale_date="2026-01-01", units=100),
        _lead(name="Active One", stage="leasing", opening_date="2026-06-01", units=100),
    ]
    ranked = score_and_rank(leads)
    assert [r.name for r in ranked] == ["Active One", "Sold One", "Planned One"]


def test_active_leads_sort_by_soonest_opening_then_units():
    leads = [
        _lead(name="Later big", stage="leasing", opening_date="2026-08-01", units=500),
        _lead(name="Soonest small", stage="permitted", opening_date="2026-05-01", units=50),
        _lead(name="Soonest big", stage="permitted", opening_date="2026-05-01", units=300),
    ]
    ranked = score_and_rank(leads)
    assert [r.name for r in ranked] == ["Soonest big", "Soonest small", "Later big"]


def test_unknown_opening_ranks_after_known_and_by_permit_date():
    leads = [
        _lead(name="Known opening", stage="under construction", opening_date="2027-01-01", units=10),
        _lead(name="Unknown newer permit", stage="under construction", permit_date="2026-06-01", units=10),
        _lead(name="Unknown older permit", stage="under construction", permit_date="2025-01-01", units=10),
    ]
    ranked = score_and_rank(leads)
    assert ranked[0].name == "Known opening"
    assert ranked[1].name == "Unknown older permit"
    assert ranked[2].name == "Unknown newer permit"
    assert "not public yet" in ranked[1].why


def test_active_leads_prefer_undecided_software_on_tie():
    leads = [
        _lead(name="On competitor", stage="leasing", opening_date="2026-05-01", units=100, software="Entrata"),
        _lead(name="Not picked", stage="leasing", opening_date="2026-05-01", units=100, software="not picked"),
    ]
    ranked = score_and_rank(leads)
    assert [r.name for r in ranked] == ["Not picked", "On competitor"]


def test_sold_leads_sort_newest_first():
    leads = [
        _lead(name="Old sale", stage="sold", sale_date="2024-01-01", units=100),
        _lead(name="New sale", stage="sold", sale_date="2026-06-01", units=100),
        _lead(name="No date", stage="sold", units=100),
    ]
    ranked = score_and_rank(leads)
    assert [r.name for r in ranked] == ["New sale", "Old sale", "No date"]


def test_planned_leads_sort_by_soonest_expected_then_units():
    leads = [
        _lead(name="No date big", stage="planned", units=400),
        _lead(name="Soonest small", stage="planned", opening_date="2027-01-01", units=50),
        _lead(name="Soonest big", stage="planned", opening_date="2027-01-01", units=200),
    ]
    ranked = score_and_rank(leads)
    assert [r.name for r in ranked] == ["Soonest big", "Soonest small", "No date big"]


def test_why_is_facts_only_and_populated_for_every_stage():
    leads = [
        _lead(name="A", stage="leasing", opening_date="2026-05-01", units=100, software="unknown"),
        _lead(name="B", stage="sold", sale_date="2026-01-01", buyer="Acme Corp", units=100),
        _lead(name="C", stage="planned", units=100),
    ]
    ranked = score_and_rank(leads)
    for record in ranked:
        assert record.why
        if record.units:
            assert str(record.units) in record.why
    assert "2026-05-01" in ranked[0].why
    assert "Acme Corp" in [r for r in ranked if r.stage == "sold"][0].why


def test_empty_input_returns_empty_list():
    assert score_and_rank([]) == []
