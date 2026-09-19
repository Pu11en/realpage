"""T14: Leads must not dump every row on screen at once (e.g. 593 Texas
rows). It should start at 50 rows with a "Show more" button, while filters
and counts (stats, header rank numbers via `rows`) still see every matching
row. Offline: checks the pagination logic in site/index.html by source
inspection, since it's inline page JS with no Node test runner in this repo."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
INDEX = (ROOT / "site/index.html").read_text()


def test_page_size_is_fifty():
    assert "const PAGE_SIZE = 50;" in INDEX


def test_show_more_button_exists_and_is_wired():
    assert 'id="show-more-btn"' in INDEX
    assert 'document.getElementById("show-more-btn").addEventListener("click"' in INDEX
    assert "visibleCount += PAGE_SIZE;" in INDEX


def test_table_renders_a_slice_not_the_full_filtered_list():
    # pageRows (sliced) feeds the table body, not the full `rows`.
    assert "const pageRows = rows.slice(0, visibleCount);" in INDEX
    assert 'document.getElementById("leads-tbody").innerHTML = pageRows.map((l, i) =>' in INDEX


def test_stats_and_counts_use_the_full_filtered_rows_not_the_page():
    # leadStats() must run on the full `rows`, before slicing to pageRows.
    stats_call = INDEX.index("const s = leadStats(rows);")
    slice_call = INDEX.index("const pageRows = rows.slice(0, visibleCount);")
    assert stats_call < slice_call


def test_visible_count_resets_on_filter_and_sort_changes():
    # A filter/sort/header-click/metro change must reset paging back to page 1.
    assert INDEX.count("visibleCount = PAGE_SIZE;") >= 3
