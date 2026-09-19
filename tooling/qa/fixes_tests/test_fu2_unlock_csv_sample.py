"""Round-2 first-user fixes: say what an account unlocks, offer a spreadsheet, show a sample pack."""
import pathlib

SITE = pathlib.Path(__file__).resolve().parents[3] / "site"
INDEX = (SITE / "index.html").read_text()


def test_unlock_note_appears_before_the_gated_buttons():
    note = INDEX.index('class="unlock-note"')
    assert INDEX.index("manager name") > note
    assert "free during early access" in INDEX.lower()


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
