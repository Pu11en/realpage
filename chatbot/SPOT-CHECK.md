# PropertyStack chatbot — answer-quality spot check (2026-09-10, PLAN-v2 Task 1.3)

Endpoint: `POST https://propertystack-chatbot-production.up.railway.app/chat`
`{"message": "...", "history": []}`. 10 new questions (distinct from
`TEST-ANSWERS-2026-09-10.md`), one at a time, live prod. Every number/citation
below was checked against `propertystack/data/plano-richardson/*.csv`.

## Q1: How many apartment buildings are in the dataset total, and how many units total?

Bot: 204 buildings, 54,784 units [1-apartments.csv].
Check: `tail -n +2 1-apartments.csv | wc -l` = 204; unit sum = 54,784. **Correct.**

## Q2: Table of all software vendors and building counts.

Bot: 11-row markdown table (Yardi 66, unknown 52, RealPage 36, Entrata 22,
ResMan 11, MRI/RentManager 5, in-house:UDR 4, AppFolio 3, in-house:Camden 2,
Yotta 2, Buildium 1), sums to 204.
Check: `cut -d, -f2 3-software.csv | sort | uniq -c` matches exactly. Proper
`|---|` separator row present. **Correct.**

## Q3: Table of upcoming projects, Richardson vs Plano, stage + expected open.

Bot: 8 Plano + 6 Richardson = 14 projects, correct stage/date values per row.
Check: counts and dates match `6-upcoming.csv` (14 data rows, 8/6 split).
Data is correct, but the bot rendered two plain "Project | Stage | Expected
open" header lines with no `|---|---|` separator row and no leading/trailing
pipes on data rows — not real markdown tables. **Table-format issue** (violates
the existing separator rule in SOUL.md).

## Q4: What software does Northside At Legacy I Apartments use?

Bot: unknown, signal none, empty proof_url, reason "no-portal-link" [3-software.csv].
Check: matches row for apt_id 2615335 exactly. **Correct.**

## Q5: Sale details for Vantage At Spring Creek (buyer, seller, date, units).

Bot: buyer TREA ROUTH CREEK TX OWNER LP, seller JDFW (VANTAGE) LLC, date
2026-06-11, 420 units, deed SWDNL.
Check: matches `5-sales.csv` row for apt_id 2748103 exactly. **Correct.** (Minor
cosmetic nit: the citations array truncated the source URL at a stray `)` —
not a factual error, not fixed.)

## Q6: How many buildings have unknown software, and what's the most common reason?

Bot: 52 unknown, most common reason "no-portal-link" (28 of 52), full
breakdown given (no-portal-link 28, no-website 21, in-house-portal 3).
Check: matches `3-software.csv` exactly. Correct numbers, but again rendered
as plain "column   buildings" text, no pipes, no separator row. **Table-format
issue** (same bug as Q3).

## Q7: What is RealPage stock trading at today?

Bot: correctly said "I don't have that," explained RealPage went private
under Thoma Bravo in Dec 2020, cited `01-company/profile.md` and
`04-reddit/index.md`. No fabricated price. **Correct** (unanswerable question
handled properly).

## Q8: Compare RealPage vs Entrata: buildings and total units for each.

Bot: RealPage 36 buildings / 8,688 units, Entrata 22 buildings / 6,052 units.
Check: recomputed by joining `3-software.csv` to `1-apartments.csv` in Python —
exact match. **Correct.**

## Q9: Who is developing Haggard Farm and when is it expected to open?

Bot: Stillwater Capital, under-construction, expected open 2027-10-01,
correctly distinguished from the separate "Haggard Farm Townhomes" zoning-filed
entry. Check: matches `6-upcoming.csv`. **Correct.**

## Q10: Table of every lead scoring above 90 — rank, name, city, score.

Bot: 4 rows (rank 1 Richardson 97, rank 2 Plano 95, rank 3 Plano 92, rank 4
Legacy Arapaho Richardson 92) — numbers and cities all match `leads.csv`. But
the bot added an unprompted closing note: "the top three are upcoming
projects... Legacy Arapaho is a sold lead." `leads.csv` row 4 (Legacy Arapaho)
has `signal = upcoming`, same as the other three — there is no "sold" lead
above score 90 in the data. **Wrong** — invented a status not in the data.
Also missing the `|---|` separator row (table-format issue, same bug as Q3/Q6).

## Summary

| # | Verdict |
|---|---|
| 1 | correct |
| 2 | correct |
| 3 | table-format issue (data correct, no separator row) |
| 4 | correct |
| 5 | correct |
| 6 | table-format issue (data correct, no separator row) |
| 7 | correct |
| 8 | correct |
| 9 | correct |
| 10 | wrong (invented "sold" status) + table-format issue |

**Score: 7/10 clean, 2 table-format issues, 1 factual invention.**

## Issues found and fixed

Two real, recurring issues in `chatbot/hermes-profile/SOUL.md`:

1. **Table separator rule not followed reliably.** The existing rule (already
   correct) was being ignored on 3 of 10 answers — the model rendered
   pipe-less or separator-less "tables." Strengthened the rule to explicitly
   require real pipe characters on every row (including the header) and to
   call out that plain/space-padded lines don't count as a table.
2. **Invented a status word not present in the queried data.** Q10 labeled a
   row "sold" when its `signal` field said `upcoming`. Added an explicit
   instruction under "never invent" to only use the exact value from a row's
   own field (e.g. `signal`) rather than relabeling based on other rows or
   plausibility.

Both edits are in `chatbot/hermes-profile/SOUL.md`. **These take effect only
after the next deploy to Railway (push to `main`)** — the live bot tested above
is still running the previously-deployed prompt. Per task instructions, no
push/deploy was done. Local re-run to confirm the fix was not attempted: the
README's local test path requires building the Docker image and calling
`DEEPSEEK_API_KEY` again, which is additional paid model usage beyond the
~10-question live spot check Drew approved. **The fix is unverified until
deploy** (or until Drew approves a separate local-Docker paid test run).
