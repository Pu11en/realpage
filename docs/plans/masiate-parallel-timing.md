# Masiate: Parallel Work And Delivery Time

## What Can Run Together

- **Drew selected eight workers; the inspected /gowork code still supports only three per run.** Eight-worker execution needs a tested per-run setting; editing this plan does not enable it.
- Use eight slots inside one coordinated run, not fifty simultaneous agents or several loops competing for the same downloads and credits; preserve the three-worker default for unrelated runs.
- The bot reported ten total session slots and two running sessions during the check, not eight reserved worker slots; coordinator overhead and other projects can cause queuing.
- Different counties and different websites can be worked on together after the shared download/record rules are ready.
- Requests to the same portal still share one paced lane; for example, do not run all seven TABS county searches at full speed independently.
- Merging records, ranking the combined results and making the final PDF depend on earlier outputs and cannot all happen at the start.

## Honest Time Estimate

- **There is no measured eight-worker delivery estimate yet.** The revised 50-task schedule has 14 waves; at an assumed 15-30 minutes per wave the arithmetic baseline is 3 hours 30 minutes to 7 hours, BEFORE extra batches, setup of eight-worker support and the delays below. It is not a delivery promise.
- The earlier three-worker estimate was roughly 6-12 hours, derived from 23 waves at 15-30 minutes; do not divide that estimate by eight or claim linear acceleration.
- Agent startup, review, merging, retries, shared-machine load and provider limits add time; measured timings may move the estimate up or down.
- The first real sample is targeted after the initial setup, source-reader check and first collection wave, roughly 1-2 hours under those assumptions; it is not the finished regional PDF.
- No completed Masiate collection task timings or verified yield measurements were available when this estimate was written; the earlier worker was stopped during the first foundation task, with no completed task recorded.
- Obtaining missing records from offices has no reliable ETA and is excluded from these estimates; requests remain unsent.

## The Parallel Schedule

- **Wave 1:** establish shared record formats and isolated output rules; this prerequisite is serial.
- **Wave 2, eight tasks:** download controls, allowance checks and six county inventories; inventories start from existing research and wait for shared controls before network work.
- **Wave 3, eight tasks:** the seventh inventory, state/local readers and first Navasota, Hearne and Caldwell source checks.
- **Wave 4, eight tasks:** early Brazos state records, College Station/Bryan/Brenham collection, and Leon/Madison local-source checks.
- **Wave 5, eight tasks:** remaining six county TABS batches, public bids and TCEQ; TABS workers share one paced host queue, not six unrestricted download lanes.
- **Wave 6, three tasks:** TABC, sales-tax and occupancy/health source checks and accessible collection batches.
- **Waves 7-8:** reconcile coverage and insert remaining accessible-source work, then combine records once; preserve units and phases.
- **Wave 9, seven tasks:** match owners across the seven counties, with separate county outputs.
- **Waves 10-14:** rank, deepen research, audit evidence, generate the PDF and check/deliver it; enrichment continuations may overlap only with disjoint candidate assignments and shared allowance controls. Do not create filler tasks merely to keep eight workers busy.
- Additional source or research batches extend this full-coverage schedule; they are not hidden inside the estimate as unlimited work.

## Measure Actual Progress

- Each task records when it started and ended, time waiting on websites, time testing/merging, source records read, new distinct projects found and what remains.
- Report elapsed time separately from total worker effort: eight workers each spending 20 minutes is 160 worker-minutes, but can be about 20 elapsed minutes if they truly overlap.
- After the first completed collection batches, revise the forecast using observed source throughput and remaining work rather than repeating the original estimate.
- Group estimates by activity: creating a new reader, downloading from a proven source, reviewing a property and generating a PDF do not have the same speed.
- Missing sources, exhausted allowances and code failures are reported separately; more agents do not remove those limits.
- This is a proposed execution schedule; no automatic wall-clock deadline has been implemented or selected.

## Faster Delivery Choices

- **A. Four-hour first report, recommended:** aim to collect from the strongest accessible sources, cover as much of the seven-county area as time permits, and reserve the final 45-60 minutes for checking and the PDF; show every gap, with deeper coverage later as separate work.
- **B. One-hour pilot:** test access and deliver whatever real, verified sample can be collected; no promise of a finished regional PDF, but an early way to measure actual speed.
- **C. Two-hour quick report:** prioritize fewer proven sources and a smaller verified shortlist, reserving report/checking time; less geographic coverage and less research per property.
- **D. Full accessible-source pass:** keep the original coverage intent, with the 14-wave baseline and additional batches/delays described above; maximize breadth without pretending blocked records are available.
- A, B and C reduce first-delivery scope; they cannot honestly promise the same coverage as D. A time target is not permission to fabricate leads or skip evidence checks; report a shortfall if verified output is not ready.
- No new purchases, subscriptions, agency messages or publishing are added by choosing parallel work.

## Current Run Status

- The earlier /gowork worker exists but reported stopped; no new collection workers were launched during this timing review.
- Updated the planner's collection steps for eight slots and 14 dependency waves with separate task ownership; this does not prove the stopped worker has loaded the update or resumed.
- Before resuming, implement and test per-run eight-worker support without changing other runs' defaults, verify available capacity and the worker's loaded plan, then confirm actual concurrent workers in the bot's status. No selected deadline means full scope remains, not an automatic four-hour cutoff.
- Code inspected: `claude_code_core/task_loop.py` sets `MAX_PARALLEL = 3` and groups eligible steps; `claude_discord/cogs/task_loop.py` creates separate child copies, records durations and merges results.
- Raw source files must be retained in a shared run-specific storage location, not left only in temporary child copies that the bot removes after merging.
