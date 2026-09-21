# CraneSignal Public Records Section: Brainstorm

## Agreed Scope

- This is a proposed section inside the existing CraneSignal app.
- Keep its planning in this worktree, separate from other ongoing work.
- Brainstorm with Drew before implementing anything.
- No separate app, repository, deployment, scraper build or paid-agent work is authorized by this brainstorm.
- The separate clone created by mistake was moved to the system Trash.

## Input and Context

- The supplied Texas Public Records Research Plan proposes turning public filings
  about construction, openings, expansion and ownership changes into vendor leads.
- It describes collecting records, matching them to vendors, and offering a feed
  or introductions. These are proposals, not validated business outcomes.
- It proposes TDLR, appraisal rolls, TABC, health permits, TCEQ and city planning
  and permit records, beginning with Brazos and expanding to DFW counties.
- The existing CraneSignal app focuses on apartment properties, their software,
  and signals that they might need new vendors.
- The supplied transcript describes a Windows scraper project but does not
  establish that it is available or verified in this checkout.

## First Decision: What Is This Section For?

All options below are suggestions awaiting Drew's answer.

- A. New opportunities: show new projects, openings and ownership changes with
  the source and why a vendor might care. Recommended as a concrete starting
  point; less historical detail than a project timeline.
- B. Project timelines: show how each development moves from planning through
  construction to opening. Richer context, but depends on linking records.
- C. Leads for my service: a vendor picks their trade and sees relevant prospects.
  More tailored, but requires agreeing on the first buyer types.
- D. Research desk: search and inspect public records, sources and collection
  status. Useful for investigation, but leaves more interpretation to the user.

## Later Questions

- Stay focused on apartments, or include other commercial businesses?
- Who is the first person using the section, and what action should it help them take?
- Which existing data and tools can support the chosen experience?
- How will it relate to the existing leads views without repeating them?
- What evidence must a result show before it is useful?

## Confirmed Customer: Masiate Construction

Drew identified Masiate Construction as the company this section should help.
The section stays inside CraneSignal; we are still brainstorming, not building.

The [company website](https://masiateconstruction.com/) lists Brazos Valley,
Texas, and residential/commercial remodeling, custom homes, fencing, flooring,
roofing, painting, concrete, siding, plumbing and lighting. The founder says he
grew up in Hearne; this does not establish an exact service radius.

Suggested starting area: Bryan and College Station in Brazos County. Additional
Brazos Valley towns should depend on how far Masiate actually wants to travel.
Do not assume the PDF's DFW expansion is appropriate for this customer.

## How Records Could Become Work

1. Check [Bryan building reports](https://www.bryantx.gov/development-services/monthly-building-reports/),
   [College Station permit and development lists](https://www.cstx.gov/business-development/planning-and-building-publications/),
   and [Texas project registrations](https://www.tdlr.texas.gov/tabs/search)
   filtered to the chosen area. Source pages were checked on 2026-09-20;
   individual local projects have not yet been collected or qualified.
2. Keep projects matching Masiate's work: new homes, commercial renovations,
   additions and other projects whose descriptions suggest relevant work.
3. Find the owner or builder and an available public business contact, then
   confirm who hires the trades and whether they are still taking quotes.
4. Give Masiate a short list showing the address, work needed, source/date,
   contact when available, and whether the opportunity is confirmed or inferred.
5. Masiate asks about the specific work and offers to quote it; track the reply.

Illustrative matches, not actual leads:

- New homes -> ask the builder about fencing, driveways, painting or flooring.
- Pool project -> ask the pool contractor about fencing or concrete work.
- Shop renovation -> ask the owner or main contractor about flooring, painting
  or framing, depending on the actual plans.
- Early development plans -> a longer-term builder relationship to follow up.

A filing proves a project was recorded, not that Masiate can still win the job.
The builder may already have hired the relevant trades. For issued permits,
subcontract work can be a more realistic opening than replacing the main builder.
Small painting/flooring jobs may not appear in these records at all.

## Next Customer Decision

Which jobs does Masiate want more of: fencing/concrete subcontract work,
homeowner remodels, commercial renovations, or whole-home builds?
Suggested first lane: fencing/concrete through local builders, because the
project records offer a concrete reason to contact them, though Masiate would
usually be doing part of the job rather than the entire project.

## Confirmed Product And Collection Direction

On 2026-09-20 Drew clarified that this should be a regular public section inside
CraneSignal, not a private area, and that the existing agent must have the data.
The first planning deliverable is a broad crawl for relevant Masiate prospects
across its services. Do not restrict the collection to one trade based on the
earlier suggested options.

The source-by-source design, tool choices, evidence checks and integration
requirements are in [Masiate: First Lead Collection Plan](masiate-first-crawl.md).
Geographic boundary remains an open question; no implementation tasks are
running and no outreach has been sent.
