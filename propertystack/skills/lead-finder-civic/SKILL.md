---
name: lead-finder-civic
description: PropertyStack lead finder part 3.5. For a city whose 3.3 recipe names a CivicPlus/AgendaCenter, Granicus, PrimeGov or CivicClerk agenda system, reads its agenda packets and finds pages near a multifamily/rezoning keyword hit.
---

# lead-finder-civic (part 3.5)

3.4 covers Legistar's free web API; this covers the other agenda systems 3.3 can identify
(AgendaCenter/CivicPlus, Granicus, PrimeGov, CivicClerk) plus plain PDF packets -- none of
these have a structured API, so the agenda listing page and its PDF packets are fetched
and read directly. No civic-scraper dependency (not installed in this environment); a
small self-contained reader does the same job for these four systems.

Packets over 25 MB are skipped without being fully fetched into memory. Only the pages
within 5 pages of a keyword hit (multifamily/apartment/unit count/rezoning/site plan) are
extracted with PyMuPDF -- not the whole packet. OCR only runs on a page PyMuPDF finds no
text on at all, via an injectable `ocr_fn` (no OCR engine ships with this repo, so real
runs supply one; tests never need it). This part only surfaces the raw hit text; 3.6 turns
a hit into a planned-project record.

Files:
- `civic_agendas.py` -- `find_civic_agenda_items()` (listing -> links -> packets -> keyword
  windows), `find_agenda_links()`, `extract_pdf_pages()`, `keyword_hit_windows()`,
  `is_pdf()`.
- `tests/test_civic_agendas.py` -- fixture-only, no network, no real PDF library calls
  except through PyMuPDF against tiny in-memory PDFs built with PyMuPDF itself.
