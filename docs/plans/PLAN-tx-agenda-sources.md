# Plan: Texas city agendas as an early-warning lead source (written 2026-09-20, for later)

Goal: add planning-stage apartment projects from Texas city agendas, 18 months to 3 years before
a building permit exists, without breaking the rule that a lead must be callable.

**Not started. Nothing here is committed to yet.** This plan exists so the live checks already
done on 2026-09-20 are not repeated.

## What was already verified live on 2026-09-20

Called `https://webapi.legistar.com/v1/<client>/` directly, no key, no login.

**Answered with real data, free:**

| city | Legistar client | bodies | planning/council meetings, last 12 months |
| --- | --- | --- | --- |
| Dallas | `cityofdallas` | 124 | 68 (21 of them City Plan Commission) |
| McKinney | `mckinney` | 28 | 93 |
| Plano | `plano` | 6 | 21 |
| Mesquite | `mesquite` | 1 (City Council only) | 25 |

**Not on Legistar at all** — the API replies "LegistarConnectionString setting is not set up in
InSite for client", which is *not* a key problem and no key will fix: Fort Worth, Arlington,
Irving, Frisco, Garland, Denton, Carrollton, Richardson, Lewisville, Allen, Austin, Houston,
El Paso, Grand Prairie (Grand Prairie resolves but then 400s on a settings error of theirs).

**San Antonio** (`sanantonio`) resolves, lists a real Planning Commission and Zoning Commission,
and returned **0 meetings since 2025-09-20**. Treat as a frozen feed, not a bug — the same shape
as Albuquerque. Re-check before wiring it.

Volume, from the 12 most recent planning/council meetings per city (a sample, not the full year):
Dallas **127** multifamily/rezoning agenda items, McKinney **19**, Plano **1**.

A real Dallas item, verbatim from the 2026-09-17 City Plan Commission:

> An application for MF-2(A) Multifamily District on property zoned CR Community Retail District
> and R-7.5(A) Single Family District, on the north line of Scyene Road and west line of N Prairie
> Creek Road, **AKA 3125 N Prairie Creek Road**. Staff Recommendation: Approval. **Applicant:
> Kittle Property Group** / Jana Darmon. Representative: Baldwin Associates / Robert Baldwin.
> Planner: Wayne Powell. Council District: 5. **Z-26-000158**

## The blocker this plan has to answer

**Zero of the 147 items read stated a unit count.** Not one.

The bar for a lead is: real building name, real address, **unit count**, genuinely recent date.
An agenda item supplies address, date, applicant and case number — three of four. The unit count
is likely inside the attached PDF, not the title.

**So T1 is a go/no-go, and the rest of this plan does not start until it passes.**

## What already exists (do not rebuild)

`propertystack/skills/lead-finder-legistar/` reads bodies -> events -> eventitems, keeps
multifamily/rezoning matters, and emits `planned`-stage LeadRecords with the agenda link. It is
wired to exactly one recipe today: `propertystack/recipes/agendas-pima-county-unincorporated-area.json`
(Arizona). **No Texas city uses it.**

Note for whoever writes the recipe: Legistar `$filter` values contain spaces and must be
percent-encoded, the same class of bug that kept Dallas County broken for months. The runner's
`_safe_url` in `tooling/run_area.py` already handles this — use the shared fetcher, do not
hand-roll a URL.

Check: python3 -m pytest -q tooling/qa/fixes_tests/ propertystack/skills && python3 tooling/qa/check_lead_data.py
Try: bash tooling/dev.sh
Open: http://localhost:8765/index.html

## Quality gates (after every task)
- The Check command passes.
- No existing state loses leads.
- Every agenda lead carries a working link back to the real agenda item.
- An agenda lead is never shown as if construction has started.

## Tasks

- [ ] A1 **Go/no-go on the unit count.** Take 20 real Dallas City Plan Commission multifamily
  items from the last 12 months. For each, check whether a unit count can be got at all: from the
  title, from the attached agenda PDF, or from the matter's own fields. Report the plain number —
  how many of 20 yielded a unit count and from where. Write it into `propertystack/runs/`.
  **If under half yield one, stop and bring the answer back before A2.**
- [ ] A2 Wire **Dallas only**. One recipe at `propertystack/recipes/tx/agendas-dallas.json` using
  client `cityofdallas` and the City Plan Commission body. Cap it to the last 12 months. Prove it
  returns real leads with address, date, applicant and agenda link. Tests.
- [ ] A3 Make the stage honest. An agenda lead must read as **"zoning application, not built"**
  on the site, with the staff recommendation shown when present, and must never be counted in the
  "recent news" number alongside permits and sales. Tests over the site data.
- [ ] A4 Verify **2 Dallas agenda leads against an independent public source** — the case number
  should be findable and the applicant real. Record the evidence.
- [ ] A5 Add **McKinney** (`mckinney`, 93 meetings) the same way, once Dallas is proven. Decide on
  Plano by its real full-year count, not the 1 item found in the sample — if it stays near zero,
  record that and skip it rather than shipping a source that looks healthy and returns nothing.
- [ ] A6 Record **Fort Worth and Arlington** in `propertystack/runs/needs-a-source.md` with the
  exact reason (not on Legistar), then spend one task finding where each actually publishes
  planning agendas. Stop after that one task whether or not it succeeds.
- [ ] A7 Record **San Antonio Legistar** as a frozen feed with its evidence, and add it to
  whatever freshness alarm exists by then so it announces itself if it ever wakes up.

## How to try it

1. Run `bash tooling/dev.sh` and open http://localhost:8765/index.html — the list still loads and
   the totals have not dropped.
2. Find a Dallas lead marked as a zoning application. It should have a street address, a date, the
   applicant's name, and a link that opens the real city agenda item.
3. Check the header's "last 6 months" number did **not** jump by the number of agenda leads —
   applications are not recent construction news.
