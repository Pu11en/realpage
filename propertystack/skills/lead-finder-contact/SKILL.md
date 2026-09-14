# lead-finder-contact

PropertyStack lead finder part 4.4: who to call, for any area.

Given a `LeadRecord` (record.py) that already has a developer/owner name and,
usually, a `permit`/`agenda`/`news` link:

- `find_website(developer, search_fn)` -- one search for the developer/owner's
  own website (never guesses a URL).
- `find_office_phone(html)` -- pulls phone numbers out of page HTML with the
  `phonenumbers` package; an office/leasing number wins over a fax line
  (never returned) or a cell/mobile line (kept only as a last-resort
  fallback).
- `find_named_contact(text)` -- a person's name, but **only** pulled from the
  text of a permit, agenda, or news page already linked on the record --
  never guessed from a generic developer "About Us" page.
- `fill_contacts(records, search_fn, fetch_fn)` -- the batch entry point:
  fills `office_phone` (and `website` if still blank) from the developer's
  own site, and folds `(contact: Name)` onto `developer` when a linked
  permit/agenda/news page names someone. Every fact filled gets a `sources`
  entry with the URL it came from, per `docs/LEAD-FORMAT.md`.

Area-agnostic: no place names anywhere in this skill's code.
