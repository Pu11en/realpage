"""G3: Leads shows honest freshness information without a fake New count."""
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
INDEX = (ROOT / "site/index.html").read_text(encoding="utf-8")


def test_stats_keep_the_three_useful_cards_without_a_new_count_or_badge():
    stats_markup = INDEX.split(
        'document.getElementById("lead-stats").innerHTML = `', 1
    )[1].split("`;", 1)[0]

    assert stats_markup.count('class="stat-card"') == 3
    assert ">Leads<" in stats_markup
    assert ">Units in play<" in stats_markup
    assert ">Opening soon<" in stats_markup
    assert "newThisWeek" not in stats_markup
    assert ">New<" not in stats_markup
    assert 'class="new-badge"' not in INDEX


def test_sidebar_uses_the_selected_areas_real_snapshot_date():
    area = json.loads((ROOT / "site/data/areas/tx.json").read_text(encoding="utf-8"))

    assert area["updated"] == "2026-09-19"
    assert "setLastUpdated(data.updated);" in INDEX
    assert "setLastUpdated(new Date" not in INDEX


def test_data_date_and_area_request_follow_the_stats():
    note = INDEX.index('Data from ${formatDataDate(data.updated)}')
    stats = INDEX.index('<div class="stats-row" id="lead-stats"></div>')
    lead_search = INDEX.index('<form class="lead-agent-search"')

    assert note < stats < lead_search
    assert "Data from ${formatDataDate(data.updated)}" in INDEX
    assert "Texas &amp; Arizona" not in INDEX
