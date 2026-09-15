"""T16: the privacy page's contact placeholder is replaced with a real email, everywhere in site/."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_no_placeholder_left_in_site():
    for path in (ROOT / "site").rglob("*"):
        if path.is_file() and path.suffix in {".html", ".js"}:
            assert "CONTACT_EMAIL_TBD" not in path.read_text(encoding="utf-8"), path


def test_privacy_page_has_real_contact_email():
    html = (ROOT / "site/privacy.html").read_text(encoding="utf-8")
    assert 'mailto:drewpullen2003@gmail.com' in html
    assert "drewpullen2003@gmail.com</a>" in html
