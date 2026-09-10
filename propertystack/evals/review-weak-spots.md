# Review: two weak spots — 2026-09-10 — area: plano-richardson

Review only, no pipeline changes made. Method: sampled 15 of the 67 no-trusted-website
rows (random seed 42, stratified across `confidence=none/low`), checked each with an
independent web search; then reproduced 5 of them by calling the real `Jina().search()`
used in `skills/find-website/run.py` directly (key read from the gitignored `.env`,
never printed/logged/committed). For find-upcoming, read `6-upcoming-candidates.jsonl`
and `6-upcoming-extract-notes.md` (the extraction agent already logged a lot of this —
confirmed it and added the Aura Northline root cause, which wasn't in the notes).

## 1. find-website — 67/207 apartments with no trusted website

### Sample verdicts (n=15)

| apt_id | name | got | real site found independently | verdict |
|---|---|---|---|---|
| 2571968 | Maa At Market Center Ii | none | maac.com/texas/dallas/maa-market-center/ | FIX — miss |
| 2143049 | Cortland North Plano | none | cortland.com/apartments/cortland-north-plano/ (cortland.com is explicitly an accepted domain per SKILL.md) | FIX — miss |
| 1747612 | Preserve At Preston | low | birchstonewestplano.com (community was **renamed** to Birchstone West Plano) | PASS (correctly low — real page surfaced, name mismatch is real, needs human rename) |
| 2779499 | Bridge At Heritage Creek | none | thebridgeplano.com ("Heritage Creek" vs actual "Heritage Creekside") | FIX — miss |
| 2693849 | Standard At Cityline Ph 2 | none | thestandardatcitylineapts.com | FIX — miss, reproduced live: query returns **0 results** |
| 2006652 | Villas Of Preston Creek | none | no distinct official site found, only listing sites + a management-co portal (rentanapt.com) | PASS-ish (true negative, or borderline — see fix 3) |
| 2803398 | Amber Vista | none | ambervistaplano.com | FIX — miss |
| 1503260 | Creekside Village Apts | low | livecreeksidevillage.com (pipeline picked something else — notes say "Communities With Care") | FIX — wrong pick |
| 2107914 | Villas Of Mission Bend Senior | none | no official site exists (confirmed live: query returns 0 results) | PASS (true negative) |
| 2693848 | Standard At Cityline Ph 1 | none | thestandardatcitylineapts.com | FIX — miss (same cause as Ph 2) |
| 2710065 | Overture Plano Senior | none | liveoverture.com/communities/overture-plano/ | FIX — miss, reproduced live: query returns 0-1 irrelevant results |
| 2652395 | Estancia At Ridgeview Ranch | none | no distinct official site, only rentanapt.com | PASS-ish (true negative, or borderline — see fix 3) |
| 2936294 | Novum Independent Living | none | novumplanoapartments.com | FIX — miss |
| 1716655 | Hathaway At Willow Bend | low | liveatthehathaway.com (pipeline picked an unrelated foreclosure news article instead) | FIX — wrong pick |
| 2544026 | Legacy Village Apts Phase Ii | none | udr.com/dallas-apartments/plano/legacy-village-apartment-homes/ (udr.com is explicitly accepted per SKILL.md) — address match for the "Phase II" building specifically is uncertain | FIX — likely miss, confidence caveat noted |

**11 of 15 are clear misses** (a real, accepted-pattern official website exists and the
pipeline returned `none`/wrong pick). **2 of 15 are true negatives** (no distinct site).
**1 of 15 is a correct low-confidence rebrand** (working as designed, needs a human to
notice the rename). **1 of 15 is a correct low-confidence borderline case.**

### Root causes (confirmed by calling the real Jina search, not guessed)

1. **Exact-phrase quoting on the raw, messy CAD name.** The query is
   `"<CAD name>" <address> <city> TX apartments` — literally quoted. CAD names carry
   suffixes no real webpage ever phrases verbatim: "Ph 2", "Ii", "Tc", doubled
   "Apartments"/"Senior". Reproduced live: `"Standard At Cityline  Apartments Ph 2" ...`
   and `"Villas Of Mission Bend Senior Apartments Tc" ...` both return **0 results** from
   Jina — not "found nothing acceptable," genuinely zero hits, because no page contains
   that exact string. The fallback query (drop address) has the same problem since it
   still quotes the raw name.
2. **Real sites get out-ranked by aggregators even when the query does return results.**
   For "Cortland North Plano Apartments" — reproduced live — Jina's top 6 results are
   yelp, apartmentlist, har.com, umovefree, apartmenthomeliving, safebutler; the real
   `cortland.com` page (an explicitly-accepted domain per SKILL.md) never appears at all.
   This isn't a classifier bug (`classify()`'s domain/title matching is lenient — one
   word match is enough), it's that the real page just isn't in the result set to
   classify.
3. **Management-company multi-property portals aren't policy-covered.** `rentanapt.com`
   is "Management Support"'s own booking site (a real, ~13,000-unit TX/AZ operator) —
   structurally the same pattern as the already-accepted `cortland.com`/`udr.com`, but
   it isn't in any allow-list and isn't consistently surfacing/classifying. Two of the
   three true-negative samples both dead-end at this same domain.
4. **`pick_best` takes the first accepted-domain result per tier, not the best one.**
   For Hathaway At Willow Bend and Creekside Village, an accepted-but-wrong page (a
   foreclosure news article, a generic content page) got picked at `low` confidence
   while the real site was reachable lower in the result set or via a cleaner query.

### Fixes, priority order

1. **HIGH — normalize the CAD name before querying, and stop quoting it exactly.**
   Strip phase/unit-type suffixes (Ph 1/2, I/II/III, Tc, duplicate Apartments/Senior/
   Apts) with a small regex before building `q1`/`q2`, and use the cleaned name
   unquoted (or quoted without the boilerplate words) so Jina can match real page
   titles. This directly fixes the 0-result cases (at least 3 of the 11 misses, likely
   more across the full 67).
2. **HIGH — add a third query variant and stop biasing toward listing sites.** The
   current 2-query fallback (name+address, then name+city) still says "apartments" every
   time, which is exactly the keyword aggregators rank for. Add a variant like
   `<clean name> <city> TX official website` or drop "apartments" from the query text,
   and consider requesting more results per call if the Jina Search API supports a
   `count`/`num` parameter (not currently passed).
3. **MED — add known management-company portal domains to an allow-list** (starting
   with `rentanapt.com`, matching the existing `cortland.com`/`camdenliving.com`/
   `udr.com` treatment), so `pick_best` doesn't have to choose between "reject as
   aggregator" and "accept as if it were the community's own site" — call these out
   explicitly at `medium` confidence like the SKILL.md doc already describes for other
   manager sites.
4. **MED — in `pick_best`, prefer a same-tier result whose domain/title look like a
   property's own marketing page over one that reads like a news article or directory
   feature**, instead of always taking the first accepted result in the tier. (This
   overlaps with the existing "Biggest problem left" note in
   `manual-spotcheck-2026-09-10.md` about the blocklist not generalizing — same
   underlying gap, opposite direction: false accepts instead of false rejects.)
5. **LOW — no code fix for the true-negative/rebrand cases** (Villas Of Mission Bend
   Senior, Estancia At Ridgeview Ranch, Preserve At Preston). These already fall to
   `none`/`low` as designed; SKILL.md already says a human should look at them. Preserve
   At Preston specifically needs a manual note that it's now branded "Birchstone West
   Plano."

## 2. find-upcoming — 3 known misses + 1 false positive

The extraction agent already logged most of this in `6-upcoming-extract-notes.md`
under "Recall gaps" — confirmed those entries are accurate and complete. Aura Northline's
wrong inclusion was **not** in the notes; found and root-caused below.

| Issue | Status | Root cause |
|---|---|---|
| Preston Road project (~351 units) missed | FIX (documented) | Source is a `content.civicplus.com` city staff-report PDF; GATHER's Legistar/TDLR/news queries never surfaced it — a search-recall gap, not an extraction miss (candidate never entered the jsonl at all). |
| Spring Creek project (~304 units) missed | FIX (documented) | Same civicplus PDF, same recall gap. |
| The Glenville (390 units, Central Expressway, approved Jan 2024) missed | FIX (documented) | GATHER's queries only surfaced a same-word-different-project TDLR filing, "Glenville Independent Living" (161 units, N Glenville Dr, opened 2024 — correctly excluded). The actual 390-unit "Glenville" project was never surfaced by any query; a name collision masked the recall gap rather than causing it. |
| Aura Northline wrongly included as upcoming | **FIX — confirmed live** | Independently verified via web search: Aura Northline is now an actively-leasing property (grand-opening-special listing, live pages on RentCafe/Apartments.com/Zillow/its own site auranorthline.com). The only source candidate for this row is a **Feb 12, 2024** dallasnews article projecting completion "early 2026." EXTRACT took that stage/date at face value with no freshness check. Today is 2026-09-10 — past the projected completion — and nothing in the pipeline re-verifies whether a project's projected completion date has already passed before finalizing it as "upcoming." This is the same class of bug as the exclusion rule ("opened/fully leased before 2025") but for projects that opened *during* the run's own review window, which the rule as written doesn't catch. |

### Fixes, priority order

1. **HIGH — add a current-status freshness check to EXTRACT for `under-construction`/
   `leasing` rows.** For any candidate whose only source is older than ~6-9 months *and*
   whose stated/expected completion date is on or before today, do one more Jina read/
   search (e.g. `"<project>" apartments now leasing`) before finalizing the row, and
   exclude it if the property is confirmed already open — this is the direct fix for
   Aura Northline and will catch the same failure mode for future runs as more of the
   12 current rows age past their projected completion dates.
2. **MED — add a civicplus/city-staff-report query to GATHER** for Plano (and check if
   Richardson has an equivalent packet host) to close the Preston Road / Spring Creek
   recall gap.
3. **MED — broaden the Glenville-style queries** so a same-neighborhood, similarly-named
   project doesn't crowd out the real one — e.g. don't stop at the first TDLR hit for a
   name, search variations like `"<name>" apartments <city> council approved <units>
   units` when a units figure is already known from another source (research-01 in this
   case).
4. **LOW — no fix needed for the extraction-notes process itself**; the agent's
   documentation of merges/exclusions/recall-gaps in `6-upcoming-extract-notes.md` is
   already thorough and made this review much faster to do.

## Fixes applied — 2026-09-10

All HIGH and MED find-website fixes (1-4) and all find-upcoming fixes (1-3) implemented and
re-run end to end (skills 2 → 3 → 4 → 6 → 7). Results:

- **find-website**: `none`+`low` (no trusted website) dropped from **67/207 to ~18/207**.
  `high` confidence rows went from 139 to 187. Verified specific miss cases now resolve to
  their real domains (cortland.com, thebridgeplano.com, thestandardatcitylineapts.com,
  ambervistaplano.com, livecreeksidevillage.com, liveoverture.com, udr.com,
  liveatthehathaway.com). Two more leaking domains found and blocked during verification
  (`traded.co`, `livingpath.com`, `yieldpro.com`, `rentseeker.com`) beyond what the review
  sample predicted.
- **detect-software / build-table**: software-identified rows went from 104 to **145/207**
  as a direct downstream effect of the website fix.
- **find-upcoming**: added the 3 missing projects — Preston Road (351-unit project at 4701 W
  Park Blvd), Spring Creek (304-unit project at Spring Creek Pkwy & K Ave), and The Glenville
  (390-unit project at 2520 N Central Expressway) — each grounded in a live-fetched source,
  not guessed. Excluded Aura Northline (confirmed already leasing). Also found and fixed a
  real bug while chasing the Preston Road miss: `TRIM_CHARS=4000` was truncating the
  ~85,000-char Plano civicplus Development Review List before reaching later entries;
  raised to 90,000 chars for `civicplus.com` sources specifically (tagged `source_type=city`
  per CONTRACTS.md, not `news`).
- **score-leads**: re-ran scoring and regenerated all 42 `why` sentences from
  `leads-facts.jsonl` only (no invented facts); `why_check.py` passes clean.
- Residual gap: `Spring Creek Project`'s exact application date wasn't confirmed (used the
  civicplus document's snapshot date, 2026-07-02, as a lower-confidence stand-in) — the
  entry had already rolled off the live rolling report by the time of the automated re-run,
  so it was added by hand from a web-search-quoted snapshot rather than the pipeline itself.
