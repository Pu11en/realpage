# MVP plan — PMS Switch Radar (C1), one metro

Source: planning session 2026-09-10
Fetched: 2026-09-10
Method: plan; depends on `research-run-01-verify.md` (not yet run)
Confidence: medium — status **DRAFT, blocked on research run 01**. Numbers in
  angle brackets `<like this>` get filled from research results.

## 1. What it is (one paragraph)

A dataset and a one-page dashboard that show, for every apartment community in
one metro, which property-management software it runs — read from the public
links on its own website — and when it switched vendors, dated from the Wayback
Machine. Each row links to the evidence. A short market report sits on top, plus
a "why they leave" section built from the public voice-of-customer evidence
already in this repo. Everything comes from public sources; nothing needs
RealPage access.

## 2. Who it's for

- **Primary buyer: RealPage** — the market-intelligence / sales-strategy lead
  (role to confirm in R5). RealPage already knows its own churn from its
  contracts, so the value is what it *can't* see from inside: which software
  every non-customer community runs (conquest targets, especially small
  managers), which vendor its leavers went to and when, and how share shifts
  by metro after bans and settlements. Weekly use: pull the conquest list for a
  territory; check new switch events. (Early warning on its own at-risk
  accounts needs the job-posting signal — v2, cut from the MVP.)
- **Fallback buyers (same dataset):** Entrata, Yardi, AppFolio, ResMan, MRI
  (conquest lists of RealPage properties); PropTech vendors who can only sell
  into a property after checking its PMS integration (smart access, payments,
  screening).
- **Evidence the pain is real:** live migration ("we are making the switch to
  Entrata once our contract with Real Page ends"), known leaver destinations
  (Yardi/Entrata/AppFolio), settling landlords agreeing to stop using the
  pricing software, and exit friction — all in `04-reddit/index.md` §3 and
  `findings.md` (landscape check).

## 3. Definition of done (measurable)

1. `data/communities.csv` holds ≥ `<60% of the metro's 100+ unit communities>`
   (denominator from R4), each with a website URL.
2. ≥85% of listed communities classified to a vendor, the rest marked
   `unknown` with a reason code. Hand check of 30 random rows: ≥27 correct.
3. Switch events have before/after Wayback URLs attached. Hand check of 10
   events (or all, if fewer than 10): ≥9 correct.
4. `dashboard.html` opens locally from a single file (no server) and shows:
   vendor share, a filterable community table, and the switch-event list with
   evidence links. CSV download works.
5. `report.md` — a 2–4 page "<Metro> PMS Market Report, Sept 2026" whose every
   number comes from the data, plus the "why they leave" section citing repo
   evidence.
6. One command (`python radar/run.py --metro <metro>`) refreshes everything in
   under 1 hour, reusing the cached Wayback backfill (the backfill itself is a
   one-time overnight job, see step 5).
7. `pitch/one-pager.md` + `pitch/outreach-draft.md` written (not sent).

## 4. Cut list (deliberately out of the MVP)

Map view · more than one metro · national coverage · unit counts or rents
beyond what the free list gives · job-posting signal (v2 early-warning idea) ·
alerts/email digests · logins or hosting · ML classifier (rules only) ·
database server (CSV/SQLite only) · G2/Capterra/app-store collection · any
contact with RealPage before the pitch is ready.

## 5. Build steps (for the build session — each has an output and a check)

All code under `radar/` in this repo; data under `radar/data/`; Python 3,
`httpx` + `beautifulsoup4` for plain pages, Crawl4AI (already installed, see
`tooling/LOCAL-ASSETS.md`) only for pages that need JavaScript.

| # | Step | Output | Acceptance check |
|---|---|---|---|
| 1 | Turn R2's pattern table into `radar/fingerprints.yaml` (host/path regex → vendor, plus a priority: pay-rent/portal links beat site-builder links) | `fingerprints.yaml` | The 50 R2 communities reclassify with the same results as R2 |
| 2 | Community list builder from the R4 source(s): name, address, manager, website, units if free | `data/communities.csv` | Row count meets DoD 1; no duplicate websites; 20 random URLs load |
| 3 | Fetcher: homepage + one hop to any link whose text matches resident/pay/portal/apply; cache raw HTML to `data/cache/`; 1 req/s per domain; retry once | `data/cache/`, `data/links.jsonl` | ≥90% of sites fetched; failures logged with status code |
| 4 | Classifier: apply `fingerprints.yaml` to links; record vendor, matched link, rule id; conflicts → pick by priority, log the conflict | `data/classified.csv` | DoD 2 hand check (30 rows, ≥27 correct); log conflict count |
| 5 | History (one-time backfill, run overnight, cached): Wayback CDX since 2023-01; fetch a snapshot only when its CDX `digest` changed, max one per quarter; where the vendor differs between two quarters, fetch the monthly snapshots in between to date the change. Classify each; build per-community vendor timeline. Budget ≤12 h at 1 req/2 s | `data/timeline.csv` | Timeline exists for ≥ `<R3 coverage %>` of communities; backfill finished within budget |
| 6 | Switch detector: vendor A for ≥2 consecutive snapshots → vendor B for ≥2 = one event, dated to the first B snapshot; attach before/after URLs | `data/switch_events.csv` | DoD 3 hand check |
| 7 | Dashboard: single `dashboard.html` with embedded JSON; share bar, filter table (vendor/manager/switched), event list with links, CSV export | `radar/dashboard.html` | Opens from disk in a browser with no errors; numbers match CSVs |
| 8 | Report: fill `report.md` from the CSVs (script prints the numbers; prose written around them) + "why they leave" section citing `04-reddit/index.md` and `raw/reviews/` | `radar/report.md` | Every number traceable to a CSV query in `radar/report_numbers.txt` |
| 9 | `run.py` wires steps 2–8 end to end | `radar/run.py` | DoD 6: fresh run under 1 hour |
| 10 | Pitch pack: one-pager (the three most striking numbers, one chart, what a national version would add, the ask), outreach draft for the R5 role, the C2 public-voice brief as appendix | `pitch/` | Reviewed by Drew; nothing sent |

Timebox: ~8 working days for steps 1–10 (steps 5–6 are the riskiest).

## 6. Risks and how they're handled

| Risk | Handling |
|---|---|
| RealPage/Yardi already own this data | R1 is a kill gate before building. If they own current-state but not history, lead the pitch with switch events + "why" layer |
| Site vendor ≠ PMS vendor | Portal/pay-rent links take priority; conflicts logged; hand checks measure it |
| Wayback coverage thin for small properties | R3 measures it; report states coverage honestly; current-state still valuable |
| Crawl blocked by some sites | Crawl4AI fallback; remaining failures go in `unknown` with a reason; never Browser Use at scale |
| Terms of use | Only public pages, polite rate, no login, cache kept local; Wayback via its public API |
| Pitch goes nowhere at RealPage | Same dataset goes to fallback buyers; decide after 3 weeks of outreach |
| **This repo is public** | Pitch strategy, target names and outreach drafts would be readable by RealPage if pushed. See open decision 2 |

## 7. Pricing hypothesis (to test, not to quote)

- Pitch ask to RealPage: paid pilot to extend the radar to their top N metros,
  with a monthly refresh. Price anchor to be set after R1 shows what existing
  data vendors charge.
- Fallback buyers: per-metro subscription or one-off conquest list.
- RealPage will ask whether their competitors get the same data. Proposed
  answer: a first-look / exclusive window for the pitch period (length is a
  Drew decision, default 60 days), then the dataset opens to other buyers.

## 8. Open decisions for Drew

1. **Go with C1?** (default: yes, if research run 01 passes)
2. **Make the GitHub repo private before pushing pitch material?** (default:
   yes — or keep `radar/` and `pitch/` out of the public repo)
3. **Any paid data source allowed if R4 needs it** (e.g. Google Places for the
   community list)? (default: up to ~$50, ask above that)
4. **Exclusivity window for RealPage?** (default: 60-day first look, then open)

Review: `review-mvp-plan-switch-radar.md` — GO WITH FIXES, fixes applied.
