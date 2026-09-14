---
name: lead-finder-software
description: PropertyStack lead finder part 4.1. Detects which leasing/property-management software a project's website runs, using our own Wappalyzer-format rules file and the same portal/hop/asset approach proven in tooling/pms_detect.py.
---

# lead-finder-software

Part 4.1 of the lead finder chain (see `propertystack/skills/lead-finder/SKILL.md`), first
step of Part 4.

Fills in `software` on every `LeadRecord` (`propertystack/skills/lead-finder/record.py`) that
has a `website` and no software verdict yet. Any area: no state, city or vendor-list is
hard-coded to one place -- `rules.json` and the code both work for any project's website.

## Files

- `rules.json` -- our own vendor fingerprint rules in Wappalyzer's `technologies` JSON shape
  (`url` and `html` regex per vendor). Written from scratch for this project, not copied from
  the GPL-licensed webappanalyzer/Wappalyzer technologies file.
- `detect.py` -- `detect_software(url, web, rules)`: fetches the site via the shared
  `WebHelper` (`lead-finder/fetch.py`) and classifies it.
- `run.py` -- `fill_software(records, web)`: batch entry point over a list of `LeadRecord`s;
  also runnable as a script (`python3 run.py in.json out.json`).

## How detection works (cheapest signal first)

1. **portal** -- a known vendor host inside a resident/login/pay/apply-type link on the
   homepage. Strongest evidence.
2. **hop-portal** -- none on the homepage, so follow up to 3 resident/login/pay-type links one
   hop and re-check.
3. **asset** -- a vendor host anywhere on the homepage (e.g. an asset CDN), not in a
   portal-type link.
4. **text** -- a plain-text vendor mention (`rules.json`'s `html` patterns) with no matching
   link at all. Cheapest and weakest signal.
5. **in-house** -- known self-hosted portals (`residents.udr.com`, `mycamden.com`) as a last
   resort.
6. Otherwise `unknown`, with `unknown_reason` set (`no-website`, `blocked`/fetch failure
   reason, or `no-portal-link`).

"Cheap check first, full browser only if unclear" comes for free from `WebHelper.fetch()`,
which already tries crawl4ai before Scrapling/Playwright and only when a page looks blocked --
this skill never opens a browser directly.

**Part 4.2 -- double check before a verdict.** A `portal`, `asset` or `text` hit came
from a single page, so before it's final `detect_software` fetches a second page (the
resident-portal link itself, or another link on the homepage) and checks it still shows
the same vendor. No agreement, no second page, or a failed fetch → the verdict drops to
`unknown` (`unknown_reason=unconfirmed`). `hop-portal` already required two pages to
agree (the homepage link and the page it points to), so it's confirmed by construction
and isn't re-checked.

`fill_software` (`run.py`) then applies the plan's rule: a confirmed **RealPage**
building is dropped from the output entirely (it's not a lead); everything else keeps
the confirmed competitor name, or becomes `"not picked"` once the site has actually been
checked and no vendor was confirmed. A record with no website to fetch stays `"unknown"`.

## Check after running

- `unknown_reason` counts show how much of the run needs a second look.
- `asset` and `text` signals are weaker evidence than `portal`/`hop-portal` -- that's why
  4.2 requires a second page to agree before either becomes a final verdict.

## Limits

- Fingerprints are string/regex matches on URLs and page text, not a certified technology
  database -- new vendor domains or renamed products show as `unknown`.
- In-house detection only covers UDR and Camden; other self-hosted portals fall through to
  `no-portal-link`.
