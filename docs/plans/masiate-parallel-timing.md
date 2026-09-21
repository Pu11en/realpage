# Masiate: Parallel Work And Delivery Time

## What Can Run Together

- **The inspected /gowork code supports up to three tasks at once**, in separate working copies, when the tasks do not depend on each other or edit the same files.
- Use that capability inside one coordinated run, not fifty simultaneous agents or several loops competing for the same downloads and credits.
- Different counties and different websites can be worked on together after the shared download/record rules are ready.
- Requests to the same portal still share one paced lane; for example, do not run all seven TABS county searches at full speed independently.
- Merging records, ranking the combined results and making the final PDF depend on earlier outputs and cannot all happen at the start.

## Honest Time Estimate

- **The original full scope: roughly 6-12 hours of elapsed working time with three-worker parallelism**, before extra continuation batches, major failures or long waits for external access; it is a planning estimate, not a promise.
- The estimate comes from 50 starting tasks at an assumed 15-30 minutes each, grouped into 23 dependency waves; 23 waves at 15-30 minutes is about 5 hours 45 minutes to 11 hours 30 minutes, rounded for planning.
- Agent startup, review, merging, retries, shared-machine load and provider limits add time; measured timings may move the estimate up or down.
- The first real sample is targeted after the initial setup, source-reader check and first collection wave, roughly 1-2 hours under those assumptions; it is not the finished regional PDF.
- No completed Masiate collection task timings or verified yield measurements were available when this estimate was written; the earlier worker was stopped during the first foundation task, with no completed task recorded.
- Obtaining missing records from offices has no reliable ETA and is excluded from these estimates; requests remain unsent.

## The Parallel Schedule

- **Waves 1-3:** establish record/download/allowance rules, start county inventories and verify the TABS reader; separate files keep these tasks from colliding.
- **Waves 4-11:** one state-record lane runs alongside local permit, agenda or inventory work; up to three tasks can make progress together on independent sources.
- **Wave 12:** reconcile coverage and insert missing accessible-source batches before downstream work; a missing source stays visible.
- **Waves 13-14:** public bids and supporting records from different agencies can run together when access and allowances permit.
- **Wave 15:** combine records once, preserving separate units and project phases.
- **Waves 16-18:** match owners in different counties concurrently, writing separate county outputs.
- **Waves 19-23:** rank, deepen research, audit evidence, generate the PDF and check/deliver it; independent enrichment batches can overlap only after disjoint candidate assignments and shared allowance controls are established.
- Additional source or research batches extend this full-coverage schedule; they are not hidden inside the estimate as unlimited work.

## Measure Actual Progress

- Each task records when it started and ended, time waiting on websites, time testing/merging, source records read, new distinct projects found and what remains.
- Report elapsed time separately from total worker effort: three workers each spending 20 minutes is 60 worker-minutes, but can be about 20 elapsed minutes if they truly overlap.
- After the first completed collection batches, revise the forecast using observed source throughput and remaining work rather than repeating the original estimate.
- Group estimates by activity: creating a new reader, downloading from a proven source, reviewing a property and generating a PDF do not have the same speed.
- Missing sources, exhausted allowances and code failures are reported separately; more agents do not remove those limits.
- This is a proposed execution schedule; no automatic wall-clock deadline has been implemented or selected.

## Faster Delivery Choices

- **A. Four-hour first report, recommended:** aim to collect from the strongest accessible sources, cover as much of the seven-county area as time permits, and reserve the final 45-60 minutes for checking and the PDF; show every gap, with deeper coverage later as separate work.
- **B. One-hour pilot:** test access and deliver whatever real, verified sample can be collected; no promise of a finished regional PDF, but an early way to measure actual speed.
- **C. Two-hour quick report:** prioritize fewer proven sources and a smaller verified shortlist, reserving report/checking time; less geographic coverage and less research per property.
- **D. Full accessible-source pass:** keep the original coverage intent, with the rough 6-12 hour estimate plus additional batches or delays; maximize breadth without pretending blocked records are available.
- A, B and C reduce first-delivery scope; they cannot honestly promise the same coverage as D. A time target is not permission to fabricate leads or skip evidence checks; report a shortfall if verified output is not ready.
- No new purchases, subscriptions, agency messages or publishing are added by choosing parallel work.

## Current Run Status

- The earlier /gowork worker exists but reported stopped; no new collection workers were launched during this timing review.
- Updated the planner's collection steps with explicit dependency waves and separate task ownership; this does not prove the stopped worker has loaded the update or resumed.
- Before resuming, verify the selected timing scope and the worker's loaded plan, then confirm actual concurrent workers in the bot's status.
- Code inspected: `claude_code_core/task_loop.py` sets `MAX_PARALLEL = 3` and groups eligible steps; `claude_discord/cogs/task_loop.py` creates separate child copies, records durations and merges results.
- Raw source files must be retained in a shared run-specific storage location, not left only in temporary child copies that the bot removes after merging.
