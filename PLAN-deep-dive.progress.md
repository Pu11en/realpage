## D1 Validator — done (2026-09-13, commit 154d5d7)
- Added propertystack/skills/deep-dive/validate.py: 8 headings in order, links on every "Why now"/"Who to ask for" line ("not found" allowed), emails/phones only if in any area's contacts.csv, opener never "with RealPage". Accepts a file, '-' for stdin, --contacts to override.
- Fixtures: good.md, bad-order.md, bad-links-contacts.md, bad-realpage-opener.md.
- Checked: self-test failed before fixtures existed, passes (rc 0) after.
- Open: none.

## D2 The skill — done (2026-09-13, commit 5bdc76b)
- Added propertystack/skills/deep-dive/SKILL.md: inputs (area + ref_id or name), CSV joins (leads/master/5-sales/contacts/6-upcoming), web research (Jina search, max ~12; crawl4ai localhost:11235 for reading, Jina read fallback), decision-maker from public pages only, the 8-section layout, upcoming-project variant, rules, write-out to data/<area>/briefs/<ref_id>.md, validate.py as the finish check.
- Auto-discovered via propertystack/.claude/skills symlink.
- Checked: validate.py --self-test rc 0.
- Open: crawl4ai /md endpoint shape not live-tested (D3 will exercise it; Jina read is the fallback).
