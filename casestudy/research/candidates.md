# Repo hunt: candidates for the case-study bot

One `### ` entry per candidate, in this exact shape (the checker enforces it):

    ### <repo name>
    **URL:** https://github.com/...
    **Area:** <which hunt task found it>
    **License / stars / last commit:** ...
    **What we'd take:** <file, module, pattern or data>
    **Verdict:** USE | MIRROR PATTERN | VENDOR DATA | SKIP
    **In plain words:** <one sentence a non-engineer understands>

Already covered by earlier research (do not re-add unless the verdict changes): python-phonenumbers,
tcpa-quiet-hours, fair-housing phrase lists, CommonRegex, sms-toolkit, instructor, outlines,
guardrails-ai, NeMo Guardrails, promptfoo, Python rules engines.

## Candidates

### zillow/fair-housing-guardrail
**URL:** https://github.com/zillow/fair-housing-guardrail
**Area:** H3 Compliance and guardrails
**License / stars / last commit:** custom OSS license (NOASSERTION, review terms before use) / 39 stars / active (pushed 2026-04-08)
**What we'd take:** Not the model itself (it's a fine-tuned BERT classifier and the training data/weights are gated behind a partner request to Zillow, not in the public repo) — the README's framework for what counts as illegal "steering" language is useful to read once, but our existing phrase-list approach (`lint-fair-housing.py` + `fair-housing-patterns.ts`, already vendored) covers the same ground far more cheaply.
**Verdict:** SKIP
**In plain words:** Zillow built a real fair-housing AI checker, but the actual trained model is locked behind a partner request, so we can't just copy it — our simpler word-list approach already does the job for this project's size.

### DataFog (datafog-python)
**URL:** https://github.com/DataFog/datafog-python
**Area:** H3 Compliance and guardrails
**License / stars / last commit:** MIT / 72 stars / active (pushed today)
**What we'd take:** Confirms our regex-first approach is the current best practice — DataFog's own pitch is "regex cascade first, NER only if you opt in," same shape as our planned `pii.py`. Not worth installing (pulls in more than we need for a handful of fields), but their regex pattern list for phone/email/SSN/address is a decent second reference to CommonRegex if we want to double-check a pattern.
**Verdict:** SKIP
**In plain words:** This tool detects personal info offline without a big AI model, same idea as our plan — it validates our approach but is bigger than we need, so we write our own six regexes instead of installing it.

### piisa/pii-extract-plg-regex
**URL:** https://github.com/piisa/pii-extract-plg-regex
**Area:** H3 Compliance and guardrails
**License / stars / last commit:** Apache-2.0 / 14 stars / last push 2024-01-24 (stale, 2+ years)
**What we'd take:** Nothing new — it's a plugin for a larger PII-detection framework (piisa) and its regex patterns overlap with CommonRegex, which we already vendored.
**Verdict:** SKIP
**In plain words:** Same idea as a tool we already picked, but this one hasn't been updated in over two years and needs a bigger framework around it, so it's not worth adding.

### Twilio opt-out keyword set (reference, not a repo)
**URL:** https://www.twilio.com/docs/proxy/opt-out-keywords
**Area:** H3 Compliance and guardrails
**License / stars / last commit:** N/A (vendor documentation, not code) / N/A / current (2026)
**What we'd take:** The canonical opt-out keyword list Twilio treats as opt-out by default: STOP, STOPALL, UNSUBSCRIBE, CANCEL, END, QUIT, REVOKE, OPTOUT — matches and confirms the list already in `RULEBOOK-research.md`. No library needed; this is a 10-line constant, not a dependency.
**Verdict:** VENDOR DATA
**In plain words:** This is the official list of words carriers treat as "stop texting me" — we just type the eight words into our own code instead of installing anything.

### Novu
**URL:** https://github.com/novuhq/novu
**Area:** H1 Messaging orchestration platforms
**License / stars / last commit:** MIT (core, enterprise features separately licensed) / ~40k / active (recent)
**What we'd take:** Workflow/step model (workflow → steps: channel step vs action step like delay/digest), the digest engine pattern (jobs linked via `_parentId` for aggregation), and the embeddable subscriber preferences component concept. Look under `apps/api/src/app` for digest/preference use-cases and `libs/framework` for the step DSL.
**Verdict:** MIRROR PATTERN
**In plain words:** Novu is the closest real product to what we're building — it already models "steps," "digests," and per-user preferences, so we copy its vocabulary and workflow shape rather than its code.

### Dittofeed
**URL:** https://github.com/dittofeed/dittofeed
**Area:** H1 Messaging orchestration platforms
**License / stars / last commit:** MIT / ~2.9k / active (1,757+ commits)
**What we'd take:** Event-triggered "journeys" model and git-based versioning of messaging campaigns — useful pattern for treating cadence rules as versioned config rather than hardcoded logic. No confirmed built-in quiet-hours/frequency-cap code found in the README; would need to check `packages/backend-lib` directly to confirm before relying on it.
**Verdict:** MIRROR PATTERN
**In plain words:** Dittofeed shows a clean way to define "when this happens, send this" journeys, but it doesn't clearly have quiet-hours or frequency-cap features we could just copy.

### Laudspeaker
**URL:** https://github.com/laudspeaker/laudspeaker
**Area:** H1 Messaging orchestration platforms
**License / stars / last commit:** AGPL-3.0 (with enterprise exception) / ~2.6k / repo states it is no longer actively developed
**What we'd take:** Visual journey-builder concept and its segmentation-by-engagement-history pattern, if we ever want a visual editor reference.
**Verdict:** SKIP
**In plain words:** Laudspeaker is abandoned (no longer maintained) and AGPL-licensed, so it's not safe or current enough to build on.

### listmonk
**URL:** https://github.com/knadh/listmonk
**Area:** H1 Messaging orchestration platforms
**License / stars / last commit:** AGPLv3 / ~23.5k / active
**What we'd take:** Its subscriber/list/unsubscribe data model (Postgres schema) as a reference for consent state, not for quiet-hours or throttling — those features weren't found.
**Verdict:** SKIP
**In plain words:** listmonk is a solid newsletter tool but it's about sending campaigns, not deciding channel/timing per person like our bot needs.

### Mautic
**URL:** https://github.com/mautic/mautic
**Area:** H1 Messaging orchestration platforms
**License / stars / last commit:** GPL / ~10.5k / active (7.x branch)
**What we'd take:** Campaign/segment data model as a reference for how a mature marketing-automation tool structures contacts and consent, but no confirmed quiet-hours, frequency-cap, or DND code found in this pass.
**Verdict:** SKIP
**In plain words:** Mautic is a big marketing platform but doesn't clearly show the specific "don't message too often, respect quiet hours" logic we're after.

### Apache Unomi
**URL:** https://github.com/apache/unomi
**Area:** H1 Messaging orchestration platforms
**License / stars / last commit:** Apache 2.0 / ~375 / active (2,782+ commits, requires Java 17/Karaf/Elasticsearch)
**What we'd take:** Nothing concrete found — it's a customer-data/profile backend (OASIS Context Server spec) for personalization/A-B testing, not a messaging-cadence engine.
**Verdict:** SKIP
**In plain words:** Unomi stores user profile data for personalization but doesn't handle sending messages or timing rules, so it's off-target for this bot.

### notifkit
**URL:** https://github.com/devkitshq/notifkit
**Area:** H1 Messaging orchestration platforms
**License / stars / last commit:** MIT / ~114 / active (64 commits)
**What we'd take:** This is the most directly on-target find: explicit "timezone-aware quiet hours that defer non-urgent sends," "user preferences, topic opt-outs, and consent gates," "ordered multi-channel fallback (push, then email, then sms)" with exponential backoff, "priority scheduling with sendAt," and "stateful multi-step workflows with wait/waitForEvent." Check `notifkit.dev/docs/guides/preferences.html` and `.../routing.html` for the documented logic, then the source repo for the matching implementation files.
**Verdict:** USE
**In plain words:** notifkit is a small open-source project built almost exactly for our problem — quiet hours, channel fallback order, and opt-outs — so it's worth pulling actual code or config patterns from it, though its small size (114 stars) means it should be double-checked for maturity.

### zoneinfo + dateutil (stdlib/dateutil, no new library needed)
**URL:** https://github.com/dateutil/dateutil
**Area:** H2 Send-time and business-day logic
**License / stars / last commit:** Apache-2.0/BSD dual / ~2.6k / active (pushed 2026-05-19)
**What we'd take:** Nothing needs vendoring — Python's built-in `zoneinfo` (already required by the plan) plus plain `datetime.timedelta` arithmetic is enough to compute "next 09:00 local strictly after reference, rolling forward, window Mon–Sat 09:00–20:00, Sunday not before 12:00." `dateutil.rrule` is only useful if the rule ever needs a real recurrence spec (e.g. "every weekday"); for a single next-send-time calculation it's unneeded complexity. Its `tz` module is a reasonable fallback reference for DST edge-case tests if `zoneinfo` behavior needs double-checking.
**Verdict:** SKIP
**In plain words:** The send-time rule in the plan is simple enough (roll forward to 9am, respect a Mon–Sat/Sunday window) that Python's built-in date tools already do the job — pulling in a recurrence-rule library would be over-engineering a 20-line function.

### pendulum
**URL:** https://github.com/python-pendulum/pendulum
**Area:** H2 Send-time and business-day logic
**License / stars / last commit:** MIT / ~6.7k / active (pushed 2026-08-20)
**What we'd take:** Nothing directly — it's a nicer datetime API (fluent `.add()`, `.at()`, built-in DST-safe arithmetic) but does the same job `zoneinfo` already does, and the plan explicitly requires numeric offsets rendered via `zoneinfo`/`tzdata`, which pendulum would just wrap. Worth knowing about only as a design reference for how a mature library documents its DST-safety guarantees, in case the sample tests (`America/Phoenix` no-DST, `America/Los_Angeles` December `-08:00`) need a second implementation to cross-check against.
**Verdict:** SKIP
**In plain words:** Pendulum is a well-liked alternative to Python's date tools, but since the plan already commits to `zoneinfo`, adding pendulum too would just be a second way to do the same thing.

### workalendar
**URL:** https://github.com/workalendar/workalendar
**Area:** H2 Send-time and business-day logic
**License / stars / last commit:** MIT / ~950 / last commit 2024-04-12 (>18 months old as of 2026-09, borderline-stale)
**What we'd take:** If holidays ever matter, its `Calendar.is_working_day()` / `add_working_days()` per-country logic (including US federal holidays and some state-specific ones) is the standard reference implementation to copy the *pattern* from, not to import as a dependency for one rule.
**Verdict:** SKIP
**In plain words:** workalendar is the well-known library for "is this a business day," but it hasn't been updated in over two years and the plan's send-time rule doesn't mention holidays at all, so it's not worth adding.

### holidays (vacanza/holidays)
**URL:** https://github.com/vacanza/holidays
**Area:** H2 Send-time and business-day logic
**License / stars / last commit:** MIT / ~1.9k / active (pushed 2026-09-16, this is the actively maintained successor to the old `dr-prodigy/python-holidays` project)
**What we'd take:** `holidays.US()` gives an instantly checkable US federal holiday calendar (`date in holidays.US()`) if the bot ever needs to skip sends on holidays. Not needed for the plan as written — the send-time spec only names Mon–Sat/Sunday rules, no holiday exception — but this is the correct, current library to reach for if that requirement is added later (avoid the archived `dr-prodigy/python-holidays` name, which redirects here).
**Verdict:** SKIP
**In plain words:** This is the right library if we ever need to skip US holidays, but the plan doesn't ask for that, so we shouldn't add the dependency now — just remember the name if the rule changes.

### pandas CustomBusinessDay / exchange_calendars
**URL:** https://github.com/gerrymanoim/exchange_calendars
**Area:** H2 Send-time and business-day logic
**License / stars / last commit:** Apache-2.0 / ~667 / active (pushed 2026-09-15)
**What we'd take:** Nothing — this is a trading-calendar library (NYSE, NASDAQ session hours) built for financial market hours, not general business-day math. It's included here to rule it out explicitly: pandas' `tseries.offsets.CustomBusinessDay` and this package are the "professional" tools people reach for, but they're overkill and mismatched (market sessions, not messaging windows) for a Mon–Sat 09:00–20:00 send window.
**Verdict:** SKIP
**In plain words:** This is a stock-market trading-hours library, not a messaging one — it looked promising by name but doesn't fit; mentioned here so nobody wastes time checking it again.

### Decision: holidays do not matter for this task
**URL:** https://github.com/vacanza/holidays
**Area:** H2 Send-time and business-day logic
**License / stars / last commit:** (see holidays entry above)
**What we'd take:** N/A — this is a decision note, not a code pull. `PLAN-casestudy-bot.md` task C2 defines the send-time window purely as Mon–Sat 09:00–20:00 local, Sunday not before 12:00, with explicit test cases for DST (`America/Phoenix`, `America/Los_Angeles`) and weekends. It never mentions holidays, and C3's tour-scheduling rule ("first two weekdays at least two days out") also only checks weekday-ness, not holiday-ness. Adding a holiday check would be scope creep not asked for by the sample tests.
**Verdict:** SKIP
**In plain words:** We looked specifically at whether US holidays should affect send-time or tour-day logic, and the answer is no — the plan's own test cases never test a holiday, so building or importing holiday-awareness now would be solving a problem nobody asked for; `vacanza/holidays` is noted above in case that changes later.

### indranilbanerjee/digital-marketing-pro
**URL:** https://github.com/indranilbanerjee/digital-marketing-pro
**Area:** H4 LLM copywriting for CRM / real estate
**License / stars / last commit:** MIT / 824 stars / active (pushed 2026-09-07)
**What we'd take:** Not the whole "marketing OS" (way too heavy) — the pattern behind its `/check` skill, a pre-publish gate that runs three cheap, deterministic checks before anything ships: an AI-tell scanner (`ai-tell-scan.py`, catches generic-sounding phrases and adverb clustering), a `brand_voice_match` score (0–1 distance against a stored `brand-profile.json`, gate at ≤0.15), and a regex-based `claim-verifier.py` that flags unverifiable numeric claims (e.g. `%` figures). This is the same shape as our planned C4 validators — worth copying the idea of scoring "distance from brand voice" as one more automatic check, and the idea of a small `claim-verifier` regex for anything that looks like a factual promise (e.g. "guaranteed", specific dollar amounts) in generated leasing copy.
**Verdict:** MIRROR PATTERN
**In plain words:** A large open-source marketing tool has a neat, cheap trick for catching AI-sounding or unsupported copy before it ships — three small automatic checks instead of one big AI judge — and we can copy that idea (not the tool) for our own message-checking step.

### efeoncepro/voice.md
**URL:** https://github.com/efeoncepro/voice.md
**Area:** H4 LLM copywriting for CRM / real estate
**License / stars / last commit:** Apache-2.0 / 1 star / active (pushed 2026-05-16)
**What we'd take:** Nothing to install (too new/unproven, 1 star), but the idea is worth stealing: a single `VOICE.md` file per brand with forbidden words, emoji rules, and per-channel length limits, plus a tiny CLI that lints a candidate message string against it and reports which rule failed. That's basically a spec for what a `brand-voice.json` + `check_brand_voice()` function in our own `casestudy/templates.py`/validators could look like.
**Verdict:** SKIP
**In plain words:** This is a neat idea for writing brand voice rules as a small checklist file, but the project itself is brand new with almost no users, so we should borrow the concept, not the code.

### KRASA-AI/real-estate-ai-skills
**URL:** https://github.com/KRASA-AI/real-estate-ai-skills
**Area:** H4 LLM copywriting for CRM / real estate
**License / stars / last commit:** MIT / 7 stars / active (pushed 2026-07-31)
**What we'd take:** Unclear — the README advertises 30+ real-estate prompt "skills" including multi-touch SMS/email nurture sequences, but the actual prompt files were not visible without cloning, and with only 7 stars and no verifiable working examples in the page content, it reads more like a marketing landing page than proven code.
**Verdict:** SKIP
**In plain words:** This repo claims to have ready-made real-estate texting/email prompts, but we could not confirm the actual files are there or good, and almost nobody has starred it, so it is not trustworthy enough to build on.

### CTIA Messaging Principles and Best Practices (reference document, not a repo)
**URL:** https://www.ctia.org/the-wireless-industry/industry-commitments/messaging-interoperability-sms-mms
**Area:** H4 LLM copywriting for CRM / real estate
**License / stars / last commit:** N/A — industry PDF/webpage, no code, updated periodically (latest cited 2023, still the active version)
**What we'd take:** Not code — a vocabulary and rule check. It confirms our already-vendored opt-out keyword list (STOP/HELP etc.) and "Msg & Data rates may apply" disclosure pattern are the actual industry standard for any generated SMS copy, so C4's copy validator should also reject generated SMS text that promises anything the record doesn't support, per CTIA's anti-deception rule.
**Verdict:** VENDOR DATA
**In plain words:** This is the official rulebook the wireless carriers use for text-message marketing; it backs up the STOP/HELP wording we already planned and reminds us generated text should never promise something not in the data.

### No open real-estate/leasing marketing-copy dataset or eval benchmark found
**URL:** https://arxiv.org/abs/2506.17863
**Area:** H4 LLM copywriting for CRM / real estate
**License / stars / last commit:** N/A — research paper, no released dataset/code found
**What we'd take:** Nothing directly — searched for open leasing/real-estate SMS or email template datasets and marketing-copy evaluation benchmarks specifically; found only paywalled vendor blog "template lists" (Dexatel, Textus, EZ Texting) with no license or downloadable data, and one arXiv paper on LLM-as-judge for ad copy that does not release its dataset. Confirms C5's plan to hand-write a small set of templates per (intent × channel × language) is the right call — there is no reusable open dataset to import instead.
**Verdict:** SKIP
**In plain words:** We looked hard for a ready-made, free set of real leasing text/email examples or a scoring benchmark for marketing copy and found nothing open and trustworthy — writing our own dozen templates by hand, as already planned, is still the right move.

### Joinn99/RocketEval-ICLR
**URL:** https://github.com/Joinn99/RocketEval-ICLR
**Area:** H5 Evaluation that grades against a reference
**License / stars / last commit:** MIT / 18 stars / active (pushed 2025-08-21)
**What we'd take:** `src/run_task.py` shows the concrete three-step pipeline: turn the expected/reference answer into a per-record checklist, grade each checklist item yes/no with a cheap LLM, then reweight items against human labels. This confirms RocketEval (cited in our STATE-OF-THE-ART-research.md as a paper) has real published code, but it's a research artifact hardcoded to its own benchmark, not an installable library.
**Verdict:** MIRROR PATTERN
**In plain words:** This project proves the "turn the expected answer into a yes/no checklist, then grade each item" idea has real code behind it, but the code itself is built for a research benchmark, not for us to install — we should copy the idea, not the code.

### UKGovernmentBEIS/inspect_ai
**URL:** https://github.com/UKGovernmentBEIS/inspect_ai
**Area:** H5 Evaluation that grades against a reference
**License / stars / last commit:** MIT / ~2,800 stars / active (daily commits)
**What we'd take:** Its `model_graded_qa` scorer (`inspect_ai/scorer/_model.py`) grades free-text output against a reference `target` using an LLM judge and returns a clean `Score` object with `value`, `answer`, `explanation` and `metadata` fields. That field shape is a good template for our own eval's per-record judge output, even though it doesn't natively compute a confidence interval across a sample.
**Verdict:** MIRROR PATTERN
**In plain words:** This is a serious, actively maintained UK government AI-safety evaluation tool; we're too small to install the whole framework, but its tidy "score + reason" output format is worth copying for our own grader.

### confident-ai/deepeval
**URL:** https://github.com/confident-ai/deepeval
**Area:** H5 Evaluation that grades against a reference
**License / stars / last commit:** Apache-2.0 / ~18,300 stars / active (near-daily commits)
**What we'd take:** Its G-Eval metric prompt template (`deepeval/metrics/g_eval/template.py`) asks the judge for a JSON object with an integer score plus a `reason` field — a clean, widely-used prompt contract worth reusing verbatim in our own tone judge, without installing the full framework (test cases, synthesizer, cloud dashboard).
**Verdict:** MIRROR PATTERN
**In plain words:** This is a very popular, actively maintained eval library; we don't need the whole thing, but its "ask the judge for a score and a reason as JSON" prompt pattern is worth copying directly.

### wandb/weave
**URL:** https://github.com/wandb/weave
**Area:** H5 Evaluation that grades against a reference
**License / stars / last commit:** Apache-2.0 / ~1,100 stars / active
**What we'd take:** It is genuinely open source and can run local scoring functions without the paid cloud UI, but the entire value of the tool is the hosted tracing/dashboard — running it purely local throws away most of what it offers.
**Verdict:** SKIP
**In plain words:** This is a real open-source tool, but it's built around a cloud dashboard we don't need for a one-time, ~100-record grading job — too heavy for what we're doing.

### jacobgil/confidenceinterval
**URL:** https://github.com/jacobgil/confidenceinterval
**Area:** H5 Evaluation that grades against a reference
**License / stars / last commit:** MIT / 144 stars / last commit 2024-05-24 (18+ months, but a small stable utility, not abandoned functionality)
**What we'd take:** scikit-learn-style calls (e.g. `precision_score`) that return both the point estimate and a proper confidence interval (Wilson score by default for small samples, bootstrap/BCa as an option) — exactly right for turning "73% pass" into "73% pass, 95% CI [64%, 81%]" on a 100-200 record eval set without hand-writing statistics.
**Verdict:** MIRROR PATTERN
**In plain words:** This tiny, well-made library computes the "give or take" range around a pass rate; the underlying formula (Wilson score interval) is simple enough to copy as a 10-line function instead of adding a new dependency, but it's a solid reference if we'd rather install it.

### wandb/weave and DeepEval/Inspect AI honest comparison (no single repo — cross-cutting note)
**URL:** https://github.com/UKGovernmentBEIS/inspect_ai
**Area:** H5 Evaluation that grades against a reference
**License / stars / last commit:** N/A — this entry is a decision note, not a new repo
**What we'd take:** None of DeepEval, Inspect AI or Weave is the standard tool for a one-off 100-200 row labelled eval — they're built for teams running continuous evals across many models. The professional-but-right-sized move for this project is to hand-roll a small script that borrows RocketEval's checklist-extraction idea, DeepEval's "JSON score + reason" judge prompt, and a Wilson-interval confidence calculation — MIRROR PATTERN across the board, install nothing new.
**Verdict:** MIRROR PATTERN
**In plain words:** After comparing the well-known eval tools, the honest answer is that all of them are built for bigger, ongoing jobs than ours — the professional choice here is to steal their best ideas into one small script rather than install any of them.

### AntoineF23/vasari
**URL:** https://github.com/AntoineF23/vasari
**Area:** H6 Human review screens
**License / stars / last commit:** MIT / 1 star / pushed 2026-07-12 (recent, but essentially unused so far)
**What we'd take:** Not the tool itself (too new and unverified to trust for real work) — the concept it's built around is exactly right: review traces, do "open and axial coding" error analysis, then validate the LLM judge against a small set of human labels using a confusion matrix, true-positive/true-negative rate and Cohen's kappa. That last piece — checking whether the automated judge agrees with a human on a sample — is worth adding as a small script even though we won't install Vasari.
**Verdict:** SKIP
**In plain words:** A tiny brand-new project (basically untested) that has the right idea — check that the AI grader agrees with a human before trusting it — but it's too new to depend on, so we'll write that agreement check ourselves in a few lines.

### promptfoo
**URL:** https://github.com/promptfoo/promptfoo
**Area:** H6 Human review screens
**License / stars / last commit:** MIT / ~25,200 stars / active (pushed today)
**What we'd take:** Its local `promptfoo view` grid — a red/green pass-fail table per test case with expandable diffs and a one-click human override button — is the cleanest reference for a "look at 100-200 rows, mark pass/fail fast" screen. Not worth installing the whole eval framework just for the viewer, but its layout (table + expand + override) is worth copying into shipcheck's existing `grade_server.py`.
**Verdict:** MIRROR PATTERN
**In plain words:** A hugely popular, actively developed AI-testing tool; we don't need the whole thing, but the way its results screen shows pass/fail as a color grid you can click through is worth copying into the review page we already have.

### argilla-io/argilla
**URL:** https://github.com/argilla-io/argilla
**Area:** H6 Human review screens
**License / stars / last commit:** Apache-2.0 / ~5,100 stars / active (pushed today)
**What we'd take:** Nothing to install — it's a full multi-annotator server (Docker, database, web UI, disagreement adjudication) built for teams labeling thousands of records with agreement tracking. For one person grading 100-200 records with pass/fail, that's substantially more infrastructure than the job needs.
**Verdict:** SKIP
**In plain words:** This is a serious, actively maintained team-labeling tool (now owned by Hugging Face), but it's built for many reviewers checking each other's work on big datasets — way more than we need for one person clicking through 100-200 answers.

### HumanSignal/label-studio
**URL:** https://github.com/HumanSignal/label-studio
**Area:** H6 Human review screens
**License / stars / last commit:** Apache-2.0 / ~28,300 stars / active (pushed today)
**What we'd take:** Same verdict as Argilla — it's a general-purpose, multi-format (image/text/audio/video) labeling platform with its own server and database. Its keyboard-shortcut binary-choice interface is a nice UX touch, but standing up the whole platform for a one-off pass/fail pass on generated messages is overkill.
**Verdict:** SKIP
**In plain words:** A big, well-known labeling tool used across many industries; too heavy to install just to press pass/fail on our messages — our existing simple review screen already does this job.

### Arize-ai/phoenix
**URL:** https://github.com/Arize-ai/phoenix
**Area:** H6 Human review screens
**License / stars / last commit:** Elastic-2.0-style custom OSS license (NOASSERTION on GitHub, check terms) / ~11,500 stars / active (pushed today)
**What we'd take:** Its trace-review UI lets a human attach a thumbs-up/down "annotation" directly onto a logged LLM call, which is a clean pattern for tagging pass/fail alongside the exact prompt/response that produced it — but Phoenix is an observability platform (tracing server, storage backend) and installing it just for that one annotation widget is not worth it.
**Verdict:** SKIP
**In plain words:** A well-known AI-observability tool; its "thumbs up/down on this specific AI response" idea is nice, but the tool itself is built for tracking live production traffic, not a one-time grading pass — too heavy for us.

### langfuse/langfuse
**URL:** https://github.com/langfuse/langfuse
**Area:** H6 Human review screens
**License / stars / last commit:** Source-available custom license (not fully open, some enterprise features gated) / ~34,700 stars / active (pushed today)
**What we'd take:** Its "annotation queue" concept — a persistent worklist of records still needing a human pass/fail label, with progress tracked per queue — is a good vocabulary/pattern reference (queue, label, score) even though we won't self-host Langfuse for a one-off job with a source-available license.
**Verdict:** MIRROR PATTERN
**In plain words:** A very popular AI-monitoring tool with a "to-do list of things a human still needs to grade" feature; worth borrowing that to-do-list idea for our own review screen, but not worth installing the whole product.
