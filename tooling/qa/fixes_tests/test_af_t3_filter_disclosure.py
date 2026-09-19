"""AF-T3: Early Leads keeps its working controls in a closed filter disclosure."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
INDEX = (ROOT / "site/index.html").read_text(encoding="utf-8")
STYLES = (ROOT / "site/css/styles.css").read_text(encoding="utf-8")


def test_filters_are_closed_by_default_under_an_accessible_toggle():
    toggle = INDEX.split('id="filters-toggle"', 1)[0].rsplit("<button", 1)[1]
    toggle += INDEX.split('id="filters-toggle"', 1)[1].split(">", 1)[0]
    assert 'type="button"' in toggle
    assert 'aria-expanded="false"' in toggle
    assert 'aria-controls="lead-filters"' in toggle
    assert ">\n            Filters " in INDEX
    assert '<div class="filters-disclosure-body" id="lead-filters" hidden>' in INDEX
    assert ".filters-disclosure-body[hidden] { display: none; }" in STYLES


def test_all_existing_filter_controls_stay_inside_the_disclosure():
    filters = INDEX.split('id="lead-filters"', 1)[1].split("</div>", 1)[0]
    for control_id in (
        "f-search",
        "f-signal",
        "f-city",
        "f-software",
        "f-sort",
        "f-hide-mine",
    ):
        assert f'id="{control_id}"' in filters
    assert 'placeholder="Search property"' in filters


def test_toggle_opens_and_closes_without_replacing_filter_controls():
    handler = INDEX.split(
        'filtersToggle.addEventListener("click"', 1
    )[1].split("});", 1)[0]
    assert "const opening = leadFilters.hidden" in handler
    assert "leadFilters.hidden = !opening" in handler
    assert 'filtersToggle.setAttribute("aria-expanded", String(opening))' in handler


def test_state_and_region_pills_remain_outside_the_fold():
    disclosure = INDEX.index('<div class="filters-disclosure">')
    assert INDEX.index('class="pick-row"><span class="pick-label">State</span>') < disclosure
    assert INDEX.index('<span class="pick-label">Region</span>') < disclosure


def test_existing_filter_listeners_are_unchanged():
    listener_block = INDEX.split(
        '["f-search", "f-signal", "f-city", "f-software", "f-sort", "f-hide-mine"]', 1
    )[1].split("});", 1)[0]
    assert "visibleCount = PAGE_SIZE" in listener_block
    assert "renderRows()" in listener_block
