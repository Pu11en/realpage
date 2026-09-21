# Finish Masiate Contacts For Every Property

Check: python3 -m pytest propertystack/skills/lead-finder/tests -q
Try: python3 tooling/masiate_pdf/render_table.py

## Goal And Authorization

Drew explicitly said "ok do go work for this plan out the nessary" after
identifying that many linked records had usable business contacts that had not
been researched. Finish the contact lookup for ALL 49 existing property rows,
not merely the nine named construction companies, then produce a new PDF-only
table. Do not restart the paused Masiate website/agent build or old collection
plans. Do not collect another property list.

Start from the session branch containing 2524068 and this committed plan.
Use the loop's isolated copy and local commits; no push, PR, main mutation,
deployment, shared-service changes or new workers outside Go Work.
The parent/report thread is 1551377360756940940. Harness/model are selected by
the human through the bot because none was named in this request.

## What Must Be Delivered

- One new PDF table covering exactly the original 49 stable property IDs, with
  short scope briefs, clearly visible PHONE numbers, contact/company names,
  actual roles, available email/website, evidence links and verification dates.
- Every row must end in a sourced contact, a clearly provisional contact, or a
  specific researched explanation for why no suitable public number was found.
  Never leave a generic blank because the contractor name is unknown.
- A private-to-the-repository research ledger recording every row, actors
  checked, exact sources, results, gaps, identity-match basis and disposition.
  This is not a new private app or login feature; the deliverable remains a
  regular downloadable PDF suitable for the company.
- Derive counts from actual results: rows checked, rows with a published phone,
  stronger company/association sources, provisional numbers, rows without a
  suitable number, and contact-role totals. Do not confuse rows with distinct
  companies/numbers or present 49 rows as 49 buying decision-makers.
- Preserve the original pilot JSON, original 63-page PDF and both previous
  table PDFs. This run produces a separately named all-row-contacts revision.

## Inputs And Existing Work

Read the current project instructions. Main inputs are in
`propertystack/data/masiate/pilot-20260920/`:
`masiate-reviewed-properties.json`, `masiate-business-phone-update.json`,
`masiate-report-summary.json`, and existing PDF artifacts.
Relevant notes: `docs/research/masiate-business-phone-check-20260920.md` and
`docs/research/masiate-contractor-check-20260920.md`.
Renderer: `tooling/masiate_pdf/render_table.py` and `table_review.json`.
Tests: `propertystack/skills/lead-finder/tests/test_masiate_table_pdf.py`.
Baseline: 85 lead-finder tests passed before this plan; nine construction-company
numbers include eight company/association-sourced numbers and one provisional
Valco directory match. Three engineering-contact profiles already have routes.
These saved contacts are reusable evidence, not permission to skip their rows.

## Contact Research Rules

1. Read EVERY public source link already attached to the assigned property,
   following relevant contact links rather than only looking at search snippets.
   Record inaccessible/irrelevant links honestly; deduplicate repeated URLs.
   Inspect the actual phone fields on the permit/registration or linked business
   site before claiming no number is present. A failed text extraction is not a
   failed search: try the available browser/PDF reader when appropriate.
2. Identify the relevant actors and their exact roles. Prefer a named builder's
   estimating/business office, then the actual owner/developer or tenant doing
   the buildout. A project representative, property manager, architect or
   engineer is a valid clearly labeled fallback. Do not silently drop these
   useful routes just because they are not a confirmed buyer.
3. Reuse a phone actually in a source when it is explicitly a public business
   contact. Otherwise follow the business's official website/contact page;
   search exact company name plus location and corroborate the entity match.
   A business published mobile is acceptable when explicitly a business line.
   Exclude personal home information and private-owner numbers whose business
   purpose cannot be established. Never infer emails, numbers or hiring demand.
4. Show one best route and up to two useful alternatives per property, with
   whose number it is, what they might clarify, source type and exact URL.
   A company main line is acceptable if labeled; it is not a direct project
   manager. Do not use an unrelated store, call-center, registered-agent or
   fax number just to fill a cell. If a generic routing office is the only
   relevant public route, label it as a routing office, not a project contact.
5. Prefer official company/institution pages and primary public records;
   membership directories can corroborate. Directory-only or ambiguous entity
   matches must be provisional and excluded from stronger-contact counts.
   A number's publication is not proof it still connects; no test calls.
6. Before "no suitable public number found", document linked sources checked,
   official-contact lookup, at least one targeted alternate lookup when there
   is an identifiable business, and the precise blocker. Missing contractor,
   a single tool error, or an untouched link is not sufficient. An inaccessible
   portal, missing actor identity, privacy-only number or ambiguous name can be
   a valid documented gap. No account creation, bypasses or requests to offices.
7. Reuse free public sources and existing permitted tools; no new subscriptions,
   paid enrichment purchases or live paid-model tests. Do not expose credentials.
   Respect access restrictions/rate limits. Save partial progress promptly if a
   source is down; do not retry indefinitely or fabricate complete coverage.

Keep the exact-suite distinction at Barron #12; other units' builders do not
belong to Suite 204. Glo #14 is tenant-funded, not automatically landlord-bought.
Atlas #4 is sign/wall-only. Lay #42 is a representative; Oxbow #39 is an owner/
developer; engineers #36/#38/#39 are not appointed builders. Valco #33 remains
provisional unless the exact company/project link is established. Planned dates
and permit status still do not establish a current request for contractors.

## Small Go Work Tasks

- [ ] MC1: Establish the all-row contact ledger and offline checks (15-25 minutes; foundation).
  Own `tooling/masiate_pdf/contact_coverage.py`, related focused tests, and `propertystack/data/masiate/pilot-20260920/contact-research/manifest.json` plus schema notes. Create an inventory keyed by all 49 immutable property IDs with original ranks, actors and source links, four non-overlapping batch assignments, and explicit not-yet-researched status. Design a structured per-property research result containing sources checked/results, contact name/role/phone/email/site, public-business basis, match evidence, source type, checked date, selected route, alternatives and researched gap where applicable. Reuse the existing nine-number supplement without changing original records. Provide a standard-library validation command that reports partial versus complete coverage and fails a final gate on missing IDs, duplicate IDs, unchecked links without a disposition, missing phone provenance, role loss, ambiguous contacts counted as strong, or unsupported generic "not found". Initial/partial checks must allow unfinished batches without claiming done. Document the exact contract for workers, keep fixture tests offline, run Check and commit. Do not crawl or alter the PDF in this task.

- [ ] MC2: Finish contact research for original rows 1-13 (20-30 minutes; depends on MC1; independent of MC3-MC5).
  Own only `contact-research/batch-01.json` and its scoped evidence notes beneath that directory. Follow the research rules for Citizens National Bank through Hub College Station Phase II, inclusive. Important missing routes include Grace Community Fellowship, Brennan Taylor Developments, Stanpac, Pink's owner/designer, TSC, Baylor Scott & White, Barron Suite 204 and Hub's developer/designer. Reuse the saved EBCO/Rhodes/Atlas/United/Guardian numbers but follow and disposition every project source, rather than treating a reused number as proof every link was checked. Every assigned ID must end researched with a sourced business route or justified gap. Save dates and identity caveats, run partial ledger validation and Check, commit. Do not modify another batch, shared renderer, manifest or other worker's notes.

- [ ] MC3: Finish contact research for original rows 14-26 (20-30 minutes; depends on MC1; independent of MC2/MC4/MC5).
  Own only `contact-research/batch-02.json` and scoped evidence notes. Cover Glo Tanning through Field House Addition, inclusive. Follow tenant/company and professional-team routes for Glo, Snook Watering Hole, The Owl, Sourdough, TCP, Taco Bell, SpinXpress, Pickleball and Studio 6; public district/city office and designer routes may be relevant for Somerville City Hall, Brazos Valley GCD and Franklin ISD. Distinguish local construction contacts from consumer booking/order numbers. The two Franklin projects remain separate rows even if they share one contact. Follow every existing source with a recorded outcome, document fallback roles and researched gaps, run partial validation and Check, commit only this batch.

- [ ] MC4: Finish contact research for original rows 27-39 (20-30 minutes; depends on MC1; independent of MC2/MC3/MC5).
  Own only `contact-research/batch-03.json` and scoped evidence notes. Cover Donald Steven Davis Gymnasium through Oxbow Business Park, inclusive. Reuse Davis/SpawGlass/Collier contact evidence; verify Valco's identity if possible, otherwise retain the explicit provisional label and seek another relevant public business route. Research the schools, Arete, Adamson, Brenham Rodeo, Galaxy and apartment/business-park owners and professional teams. Follow the actual linked records for named business contact numbers, including rechecking the saved engineering routes without promoting engineers to buyers. Preserve the interim/not-for-bidding warning on Tabor plans. Finish all assigned IDs with evidence or precise gaps, run partial validation and Check, commit only this batch.

- [ ] MC5: Finish contact research for original rows 40-49 (15-25 minutes; depends on MC1; independent of MC2-MC4).
  Own only `contact-research/batch-04.json` and scoped evidence notes. Cover MDS Maintenance through AutoZone Navasota, inclusive. Research business contacts for MDS, Somerville ISD, Navasota Ventures/Lay, TxDOT, Icon's development team, First Financial Bank, Altura Capital, Murphy Commercial Holdings and the Dollar General/AutoZone development actors actually named in source records. Corporate/store customer service is not a substitute for a construction contact; label an institutional routing office if that is the only suitable public route. Verify geographic/entity matches for generic LLC names. Follow and disposition all source links; finish all ten IDs with contacts or justified gaps, run partial validation and Check, commit only this batch.

- [ ] MC6: Combine the research, rebuild the PDF and deliver it (20-30 minutes; depends on MC2-MC5).
  Own final merged contact data/coverage summary, `tooling/masiate_pdf/render_table.py`, `table_review.json`, focused rendering tests, the new PDF and final delivery notes. Read all four batches and resolve duplicate actors or conflicting numbers without merging distinct property IDs/suites. Preserve disagreements and provisional status instead of selecting by convenience. Include sourced owner/tenant/designer/engineer fallbacks in each row rather than filtering them out because a contractor name is absent. Replace generic empty contact cells with a specific researched explanation and checked date. Print phone prominently, actual contact role and source link next to it; keep the short project brief, dates, caveats and source links. Derive honest contact/coverage counts. Create `Masiate-All-Property-Contacts-2026-09-20.pdf`, explicitly distinguish the original project snapshot from actual new contact-check dates, and leave all older PDFs and original JSON unchanged. Run the final coverage gate requiring all 49 IDs researched plus Check, inspect PDF page images and test text bounds, unsplit rows, links and phone/role alignment, correct any in-scope issues, then commit. Attach the actual new PDF to parent thread 1551377360756940940 using the bot's attachment mechanism; never merely claim it was delivered or return a path. Give a short plain-English count of useful numbers, provisional contacts and honest gaps, and report unverified items. No site build, outreach, push or deployment.

## Scheduling, Checkpoints And Completion

Dependency order: MC1 -> [MC2, MC3, MC4, MC5] -> MC6. Research batches own
disjoint files and are parallel-ready if this Go Work runner supports it;
do not claim parallel execution until actual worker receipts prove it. Use
the runner's supported capacity, not new manual agents or changed bot limits.
If the runner is sequential, run the same tasks sequentially without inventing
extra orchestration. Rough estimate: 110-170 worker-minutes; about 60-90 elapsed
minutes with four concurrent research slots, or roughly two to three hours
sequentially, excluding model-selection waits and unusually blocked sources.
These are estimates, not deadlines or promises of 49 discoverable phone numbers.

Commit each task and checkpoint a completed property during research. If a
batch cannot finish in one sitting, preserve its unfinished IDs explicitly;
continue that same small batch in a fresh task session before final delivery.
Do not turn timeout into "no number found" or mark a partially researched batch
complete. Write scoped worker notes; only the coordinator/final task updates
the adjacent plan progress file. Check is offline and self-contained, expected
under two minutes; live research checks are separate so a source outage cannot
make the regression suite flaky. The final completeness gate must actually
evaluate these new results, not just the preexisting 85 tests.

## How To Try It

1. Open the newly attached PDF and find a formerly blank row such as Glo,
   Pink or an owner-listed permit: it now has a relevant labeled business route
   or a precise explanation of the completed search.
2. Pick a phone number, click its evidence link and confirm the source identifies
   the same business; check whether the recipient is a builder, owner or designer.
3. Check the first-page totals and unresolved list: all 49 rows are accounted
   for, and no contact or planned date is presented as proof of available work.
