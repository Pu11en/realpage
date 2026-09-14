"""lead-finder-legistar (3.4) tests: fake http_get, no network."""
import datetime
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import legistar  # noqa: E402

TODAY = datetime.date(2026, 9, 14)


def _fake_http_get(bodies, events, eventitems_by_event):
    def _get(url):
        if url.endswith("/bodies"):
            return bodies
        if "/events?" in url:
            return events
        for event_id, items in eventitems_by_event.items():
            if f"/events/{event_id}/eventitems" in url:
                return items
        return []
    return _get


def test_multifamily_matter_becomes_planned_record():
    bodies = [{"BodyId": 1, "BodyName": "Planning and Zoning Commission"},
              {"BodyId": 2, "BodyName": "Parks Board"}]
    events = [{"EventId": 100, "EventBodyId": 1, "EventDate": "2026-06-01T00:00:00"},
              {"EventId": 200, "EventBodyId": 2, "EventDate": "2026-06-02T00:00:00"}]
    eventitems = {
        100: [{"EventItemMatterName": "Z-2026-014: rezoning 500 Main St for a 220 unit apartment community",
               "EventItemMatterId": 555}],
        200: [{"EventItemMatterName": "Approve park bench purchase", "EventItemMatterId": 777}],
    }
    http_get = _fake_http_get(bodies, events, eventitems)

    records = legistar.find_legistar_matters("Rivertown", "TX", "tx", "rivertown", http_get, today=TODAY)

    assert len(records) == 1
    r = records[0]
    assert r.stage == "planned"
    assert r.units == 220
    assert "500 Main St" in r.address
    assert "Z-2026-014" in r.why
    assert r.links["agenda"] == "https://rivertown.legistar.com/LegislationDetail.aspx?ID=555"


def test_non_matching_body_and_non_keyword_items_dropped():
    bodies = [{"BodyId": 1, "BodyName": "Planning and Zoning Commission"}]
    events = [{"EventId": 100, "EventBodyId": 1, "EventDate": "2026-06-01T00:00:00"}]
    eventitems = {100: [{"EventItemMatterName": "Approve minutes", "EventItemMatterId": 1}]}
    http_get = _fake_http_get(bodies, events, eventitems)

    records = legistar.find_legistar_matters("Rivertown", "TX", "tx", "rivertown", http_get, today=TODAY)
    assert records == []


def test_token_required_or_unreachable_returns_skip_note():
    def http_get(url):
        raise PermissionError("token required")

    result = legistar.find_legistar_matters("Rivertown", "TX", "tx", "rivertown", http_get, today=TODAY)
    assert result == {"city": "Rivertown", "state": "TX", "skipped": True, "reason": "legistar token required or unreachable"}


def test_no_planning_or_zoning_body_returns_skip_note():
    bodies = [{"BodyId": 1, "BodyName": "Parks Board"}]

    def http_get(url):
        if url.endswith("/bodies"):
            return bodies
        return []

    result = legistar.find_legistar_matters("Rivertown", "TX", "tx", "rivertown", http_get, today=TODAY)
    assert result == {"city": "Rivertown", "state": "TX", "skipped": True, "reason": "no planning/zoning/council body found"}


def test_duplicate_matter_across_events_deduped():
    bodies = [{"BodyId": 1, "BodyName": "City Council"}]
    events = [{"EventId": 100, "EventBodyId": 1, "EventDate": "2026-06-01T00:00:00"},
              {"EventId": 101, "EventBodyId": 1, "EventDate": "2026-07-01T00:00:00"}]
    eventitems = {
        100: [{"EventItemMatterName": "Site plan for 50 unit apartment project", "EventItemMatterId": 42}],
        101: [{"EventItemMatterName": "Site plan for 50 unit apartment project", "EventItemMatterId": 42}],
    }
    http_get = _fake_http_get(bodies, events, eventitems)

    records = legistar.find_legistar_matters("Rivertown", "TX", "tx", "rivertown", http_get, today=TODAY)
    assert len(records) == 1
