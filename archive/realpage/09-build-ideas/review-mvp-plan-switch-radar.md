# Review — mvp-plan-switch-radar.md

Source: `/mvp-plan-review` skill run on `09-build-ideas/mvp-plan-switch-radar.md`
Fetched: 2026-09-10
Method: gate-by-gate check against the plan text, `findings.md`, `04-reddit/index.md`
Confidence: medium (research run 01 not yet executed)

Verdict: **GO WITH FIXES** — fixes 1–3 applied to the plan in the same session;
build still blocked on research run 01.

| Gate | Result | Why |
|---|---|---|
| G1 Outside-in | PASS | Inputs are public websites, Wayback's public API, and repo evidence; the one paid possibility (community list) is flagged as a Drew decision |
| G2 Named buyer | FIX → applied | The plan sold RealPage "spot portfolios that moved off RealPage." RealPage already knows its own churn from its contracts, so that's the weakest value for this buyer. The real value to RealPage is what it *can't* see: which software every non-customer runs, where its leavers went, and how share shifts after bans and settlements |
| G3 Absence provable | PASS | R1 is an explicit kill gate with KILL / PIVOT-SIGNAL / PASS rules |
| G4 MVP scope | PASS | One metro, one dataset, a measurable DoD, an explicit cut list, an 8-day timebox |
| G5 Feasibility | FIX → applied | Wayback volume breaks DoD 6. ~1,000 communities × ~44 monthly snapshots ≈ 44k fetches; at 1 request per 2 s that's ~24 h, not "under 1 hour," and it isn't polite. Also unproven: that pay/portal links sit on the homepage in old snapshots |
| G6 Executable by cheaper model | PASS | Ordered steps, each with an output file and an acceptance check. Step 2 depends on R4's source choice, which is correct for a blocked plan |
| G7 Pitch | FIX → applied | Artifact and fallback buyers are named. The route to a human is an R5 hypothesis (fine), but the plan said nothing about the fact that the same data goes to RealPage's competitors — RealPage will ask |

## Required fixes

1. **(applied)** §2: rewrite RealPage's weekly use around competitor-installed
   properties, where leavers went, and share shifts; move "early warning on
   our own accounts" to v2 (it needs the job-posting signal, which is cut).
2. **(applied)** Step 5 + DoD 6: use the CDX `digest` field so a snapshot is
   fetched only when the page content changed, cap it at one snapshot per
   quarter, then fill in monthly around a detected change. History is a
   one-time backfill (budget ≤12 h, run overnight, cached); DoD 6's "under
   1 hour" applies to a refresh with cached history. Add R3 check: do old
   homepage snapshots still carry the portal link?
3. **(applied)** §7: add the exclusivity question — offer RealPage a
   first-look/exclusive period for the pitch window (Drew decision).

## Risks accepted

- Rules-only classifier will miss odd setups; `unknown` with a reason is
  acceptable for an MVP and gets measured by the hand check.
- One metro can't prove national value; the pitch sells the extension.

## Open decisions for Drew

1. Go with C1 if research run 01 passes? — default **yes**
2. Private repo (or keep `radar/` and `pitch/` out of the public repo) before
   pitch material is pushed? — default **yes**
3. Exclusivity window for RealPage vs. selling to competitors in parallel? —
   default **60-day first look for RealPage, then open**
