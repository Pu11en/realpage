"""T10: the Early Leads table headers are clickable and sort the rows,
clicking again reverses the order, and the Sort dropdown stays in step."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
INDEX = (ROOT / "site/index.html").read_text(encoding="utf-8")


def test_sortable_headers_declared():
    assert 'data-sort-key="score"' in INDEX
    assert 'data-sort-key="property"' in INDEX
    assert 'data-sort-key="city"' in INDEX
    assert 'data-sort-key="units"' in INDEX
    assert 'data-sort-key="signalType"' in INDEX
    assert 'data-sort-key="software"' in INDEX


def test_header_click_toggles_direction():
    assert 'headerSort.dir === "asc" ? "desc" : "asc"' in INDEX


def test_header_sort_used_before_dropdown_sort():
    # headerSort must be checked first so a clicked header wins over the
    # dropdown's own score/size/newest branches.
    idx_header = INDEX.index("if (headerSort) {")
    idx_dropdown = INDEX.index('sort === "size"')
    assert idx_header < idx_dropdown


def test_score_and_units_headers_sync_the_dropdown():
    assert 'document.getElementById("f-sort").value = "score"' in INDEX
    assert 'document.getElementById("f-sort").value = "size"' in INDEX


def test_dropdown_change_clears_header_sort():
    assert 'headerSort = null' in INDEX
