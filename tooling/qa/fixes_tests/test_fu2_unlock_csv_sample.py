"""Round-2 first-user fixes: say what the downloads cost, offer a spreadsheet, show a sample pack.

These tests were written on 2026-09-19 when both downloads sat behind a free account. Two
later commits deliberately removed that wall -- 7ec4b52 "Let visitors download the PDF call
list without an account" and e8d956c "Make the lead spreadsheet download free too" -- and
nobody updated the tests, so they went red on 2026-09-21 and stayed red. They now pin the
decision that replaced the wall, so re-gating a download is a visible test change rather
than a quiet one.
"""
import pathlib

SITE = pathlib.Path(__file__).resolve().parents[3] / "site"
INDEX = (SITE / "index.html").read_text()
PANEL = (SITE / "js" / "chat-panel.js").read_text()


def test_the_download_row_says_what_is_free_and_what_is_not():
    # Layout 2026-09-19: one short "Take the list with you" row instead of three sentences.
    row = INDEX.index('class="take-it-row"')
    assert INDEX.index('id="download-lead-pack"') > row
    assert INDEX.index('id="download-csv"') > row
    # The two halves of the offer. Both have to be said, in this order, or the row either
    # undersells what is free or oversells what an account is for.
    assert "Free download, no account needed." in INDEX
    assert "Make a free account to ask who to call." in INDEX


def test_neither_download_is_behind_the_account_wall():
    """Decided 2026-09-21: the leads, the PDF and the spreadsheet are all free without an
    account, and only the agent asks for one. The wall is still in chat-panel.js as
    requireAuth() -- these assertions are what says it must not be wired to a download."""
    for function_name in ("requestCsv", "requestLeadPack"):
        block = INDEX.split(f"function {function_name}", 1)[1].split("\n      }\n", 1)[0]
        assert "requireAuth" not in block, f"{function_name} re-gated a free download"
    assert "Make a free account to download your call list" not in INDEX
    assert "Make a free account to download the spreadsheet" not in INDEX
    # The wall itself is not deleted: the agent still uses this path.
    assert "function requireAuth(purpose, onSuccess)" in PANEL


def test_the_spreadsheet_carries_the_columns_a_caller_needs():
    assert 'id="download-csv"' in INDEX
    csv_block = INDEX.split("function requestCsv", 1)[1].split('document.getElementById("download-csv")', 1)[0]
    assert "text/csv" in csv_block
    cols = INDEX.split("const cols = [", 1)[1].split("]", 1)[0]
    for column in ("Building", "City", "Units", "Phone", "Why now", "Source"):
        assert f'"{column}"' in cols


def test_sample_lead_pack_is_public():
    assert 'href="sample-lead-pack.pdf"' in INDEX
    assert (SITE / "sample-lead-pack.pdf").exists()
