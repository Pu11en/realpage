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

## D3 Run it on 3 real leads — done (2026-09-13)
- Wrote propertystack/data/plano-richardson/briefs/2748103.md (Vantage At Spring Creek), richardson-legacy-arapaho.md (Legacy Arapaho), 2058512.md (Creekside At Legacy).
- 17 Jina searches total (budget 36), reads via crawl4ai + a few Jina reads.
- Checked: validate.py passes on all 3; --self-test rc 0.
- Findings: Vantage manager after the June 2026 sale is unconfirmed (listings say Bell Partners, Bell Yelp listing closed); Legacy Arapaho contact Brian McNally (VP Development, public article); Creekside contact Caitlin Roniger (Key's systems director, team page). Opening date conflict for Legacy Arapaho: CSV 2028-11 vs city "Oct 2029".
- SKILL.md: added note that Yelp/ApartmentRatings/ForRent block readers.
- Open: Drew must review the 3 briefs and OK them (or ask for changes to SKILL.md) before D4.
