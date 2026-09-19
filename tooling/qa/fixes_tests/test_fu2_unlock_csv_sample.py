"""Round-2 first-user fixes: say what an account unlocks, offer a spreadsheet, show a sample pack."""
import pathlib

SITE = pathlib.Path(__file__).resolve().parents[3] / "site"
INDEX = (SITE / "index.html").read_text()


def test_account_terms_sit_next_to_the_gated_buttons():
    # Layout 2026-09-19: one short "Take the list with you" row instead of three sentences.
    row = INDEX.index('class="take-it-row"')
    assert INDEX.index('id="download-lead-pack"') > row
    assert "Free account. No card. Also unlocks who to call." in INDEX


def test_spreadsheet_download_exists_and_is_account_gated():
    assert 'id="download-csv"' in INDEX
    csv_block = INDEX.split("function requestCsv", 1)[1].split("document.getElementById(\"download-csv\")", 1)[0]
    assert "requireAuth" in csv_block
    assert "text/csv" in csv_block
    cols = INDEX.split("const cols = [", 1)[1].split("]", 1)[0]
    for column in ("Building", "City", "Units", "Phone", "Why now", "Source"):
        assert f'"{column}"' in cols


def test_sample_lead_pack_is_public():
    assert 'href="sample-lead-pack.pdf"' in INDEX
    assert (SITE / "sample-lead-pack.pdf").exists()
