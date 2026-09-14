import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from civic_agendas import (
    MAX_PACKET_BYTES,
    find_agenda_links,
    find_civic_agenda_items,
    is_pdf,
    keyword_hit_windows,
)


def make_pdf(pages_text: list[str]) -> bytes:
    import fitz

    doc = fitz.open()
    for text in pages_text:
        page = doc.new_page()
        if text:
            page.insert_text((72, 72), text)
    data = doc.tobytes()
    doc.close()
    return data


def test_find_agenda_links_filters_to_agenda_packet_links():
    html = """
    <a href="/AgendaCenter/ViewFile/Agenda/1_09-01-2026-Agenda.pdf">Agenda</a>
    <a href="/AgendaCenter/ViewFile/Minutes/1_09-01-2026-Minutes.pdf">Minutes</a>
    <a href="/other/page.html">Unrelated page</a>
    """
    links = find_agenda_links(html, "https://example.civicplus.example/AgendaCenter")
    assert any("Agenda.pdf" in link for link in links)
    assert not any("page.html" in link for link in links)


def test_find_agenda_links_resolves_relative_urls():
    html = '<a href="/docs/packet.pdf">Agenda Packet</a>'
    links = find_agenda_links(html, "https://city.example.com/meetings")
    assert links == ["https://city.example.com/docs/packet.pdf"]


def test_is_pdf():
    assert is_pdf(b"%PDF-1.4 ...")
    assert not is_pdf(b"<html>not a pdf</html>")


def test_keyword_hit_windows_keeps_only_pages_near_a_hit():
    pages = ["cover page", "budget item", "rezoning of 123 Main St for apartments", "closing remarks", "appendix"]
    windows = keyword_hit_windows(pages, window=1)
    kept_pages = [i for i, _ in windows]
    assert kept_pages == [1, 2, 3]


def test_keyword_hit_windows_no_hit_returns_empty():
    assert keyword_hit_windows(["cover page", "budget item", "closing remarks"]) == []


def test_extract_pdf_pages_reads_real_text():
    pdf_bytes = make_pdf(["Cover page", "Rezoning request for 500 units apartments"])
    from civic_agendas import extract_pdf_pages

    pages = extract_pdf_pages(pdf_bytes)
    assert len(pages) == 2
    assert "Cover" in pages[0]
    assert "Rezoning" in pages[1] or "units" in pages[1]


def test_extract_pdf_pages_uses_ocr_fn_when_page_has_no_text():
    pdf_bytes = make_pdf(["Cover page", ""])  # second page has no text at all

    def fake_ocr(_png_bytes: bytes) -> str:
        return "OCR: apartments rezoning 200 units"

    from civic_agendas import extract_pdf_pages

    pages = extract_pdf_pages(pdf_bytes, ocr_fn=fake_ocr)
    assert pages[0] == "Cover page"
    assert "OCR" in pages[1]


def test_find_civic_agenda_items_unsupported_system_skips():
    result = find_civic_agenda_items(
        "Rivertown", "ZZ", {"system": "legistar", "agenda_url": "https://x.example/agenda"}, fetch_fn=lambda url: None
    )
    assert result["skipped"] is True
    assert "legistar" in result["reason"]


def test_find_civic_agenda_items_no_agenda_url_skips():
    result = find_civic_agenda_items("Rivertown", "ZZ", {"system": "granicus"}, fetch_fn=lambda url: None)
    assert result["skipped"] is True


def test_find_civic_agenda_items_listing_unreachable_skips():
    result = find_civic_agenda_items(
        "Rivertown", "ZZ", {"system": "granicus", "agenda_url": "https://x.example/agenda"}, fetch_fn=lambda url: None
    )
    assert result["skipped"] is True
    assert "unreachable" in result["reason"]


def test_find_civic_agenda_items_no_links_found_skips():
    listing_html = b"<html><body>No documents here</body></html>"
    result = find_civic_agenda_items(
        "Rivertown",
        "ZZ",
        {"system": "primegov", "agenda_url": "https://x.example/agenda"},
        fetch_fn=lambda url: listing_html,
    )
    assert result["skipped"] is True
    assert "no agenda documents" in result["reason"]


def test_find_civic_agenda_items_end_to_end_finds_keyword_hits():
    listing_html = b'<html><a href="https://x.example/packet.pdf">Agenda Packet</a></html>'
    packet_bytes = make_pdf(["cover page", "rezoning for 300 unit apartment complex at 200 Oak St", "appendix"])

    def fetch_fn(url: str):
        if url == "https://x.example/agenda":
            return listing_html
        if url == "https://x.example/packet.pdf":
            return packet_bytes
        return None

    hits = find_civic_agenda_items(
        "Rivertown", "ZZ", {"system": "civicclerk", "agenda_url": "https://x.example/agenda"}, fetch_fn=fetch_fn
    )
    assert not isinstance(hits, dict)
    assert len(hits) >= 1
    assert any("rezoning" in hit.text.lower() for hit in hits)
    assert all(hit.url == "https://x.example/packet.pdf" for hit in hits)


def test_find_civic_agenda_items_skips_oversized_packet():
    listing_html = b'<html><a href="https://x.example/big.pdf">Agenda Packet</a></html>'
    huge = b"%PDF" + b"0" * (MAX_PACKET_BYTES + 1)

    def fetch_fn(url: str):
        if url == "https://x.example/agenda":
            return listing_html
        return huge

    hits = find_civic_agenda_items(
        "Rivertown", "ZZ", {"system": "granicus", "agenda_url": "https://x.example/agenda"}, fetch_fn=fetch_fn
    )
    assert hits == []


def test_find_civic_agenda_items_skips_non_pdf_link():
    listing_html = b'<html><a href="https://x.example/agenda.html">Agenda Packet</a></html>'

    def fetch_fn(url: str):
        if url == "https://x.example/agenda":
            return listing_html
        return b"<html>rezoning apartments</html>"

    hits = find_civic_agenda_items(
        "Rivertown", "ZZ", {"system": "agendacenter", "agenda_url": "https://x.example/agenda"}, fetch_fn=fetch_fn
    )
    assert hits == []
