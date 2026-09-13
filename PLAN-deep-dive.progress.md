## D1 Validator — done (2026-09-13, commit 154d5d7)
- Added propertystack/skills/deep-dive/validate.py: 8 headings in order, links on every "Why now"/"Who to ask for" line ("not found" allowed), emails/phones only if in any area's contacts.csv, opener never "with RealPage". Accepts a file, '-' for stdin, --contacts to override.
- Fixtures: good.md, bad-order.md, bad-links-contacts.md, bad-realpage-opener.md.
- Checked: self-test failed before fixtures existed, passes (rc 0) after.
- Open: none.
