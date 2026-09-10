# Later value layers — saved for after the MVP

Source: Drew + planning session 2026-09-10
Fetched: 2026-09-10
Method: brainstorm; each idea needs more data runs, so it's parked
Confidence: medium (ideas, not yet tested)

These sit on top of the base table (apartment → software → proof). Ideas 1–4
reuse fields already in the Collin CAD data (`imprvunits`, `ownername`,
`deedeffdate`, `imprvyearbuilt`).

1. **Share by units, not properties** — "RealPage runs X% of Plano's apartment
   units." Uses the county unit counts.
2. **Group by owner/landlord** — one owner with 6 properties on Yardi = one
   deal to flip 6. Gives a sales list sorted by deal size.
3. **Recently sold = hot leads** — a new owner often changes software. Use the
   county deed date to flag properties sold in the last 12 months.
4. **New buildings** — properties built 2024–2026 are choosing software now.
   Easiest targets.
5. **Switch history (v2)** — Wayback snapshots show who changed software and
   when. More work; not tested yet.

Pitch line: "Every apartment near your HQ, what software it runs, who owns it,
and which ones are about to choose."
