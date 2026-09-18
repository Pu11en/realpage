# Repo hunt progress log

## H1 Messaging orchestration platforms
Searched Novu, Dittofeed, Laudspeaker, listmonk, Mautic, Apache Unomi via GitHub/web search, plus
an open-ended search for "quiet hours frequency cap notification github" that surfaced a strong
extra find. Best find: **notifkit** (devkitshq/notifkit) — a small MIT project built almost
exactly for this problem: timezone-aware quiet hours, channel fallback order (push→email→sms),
and preference/consent opt-out gates. Novu is the closest big product (workflow/step/digest
vocabulary worth mirroring) but too heavy to adopt directly. Laudspeaker is abandoned (no longer
maintained) despite looking promising, so it was skipped. Mautic, listmonk and Unomi turned out to
be adjacent (contact/profile data models) rather than message-timing engines, so all three are
SKIP. 7 candidates added to candidates.md, all pass the format checker.

## H2 Send-time and business-day logic (2026-09-17)
Searched GitHub for dateutil, pendulum, workalendar, holidays (python-holidays/vacanza), pandas
CustomBusinessDay, exchange_calendars. Verified each repo's license/stars/last-commit via the
GitHub API. Best find: none needed as a dependency — the plan's send-time rule (next 09:00 local,
Mon-Sat 09:00-20:00, Sunday not before 12:00, DST via zoneinfo) is fully coverable with Python's
stdlib zoneinfo + timedelta, so C2 should stay dependency-free. Surprising: the old
`dr-prodigy/python-holidays` project has been superseded by `vacanza/holidays` (same MIT license,
still actively maintained) — noted the rename so nobody imports the stale name. Also confirmed via
re-reading PLAN-casestudy-bot.md that holidays are out of scope for both the send-time window (C2)
and the tour-day picker (C3): neither rule nor its test cases mention holidays, so no
holiday-awareness library should be added.

## H3 Compliance and guardrails (2026-09-17)
Searched for Zillow's Fair Housing Classifier, TCPA/CTIA opt-out keyword libraries, and
lightweight offline PII detectors, avoiding everything already vendored (python-phonenumbers,
tcpa-quiet-hours, fair-housing phrase lists, CommonRegex). Found the real repo:
zillow/fair-housing-guardrail (MIT-adjacent custom license, 39 stars, active) — but its actual
trained classifier and training data are gated behind a partner request to Zillow, not in the
public repo, so SKIP in favor of our already-vendored phrase lists. Checked DataFog
(datafog-python) and piisa/pii-extract-plg-regex as alternative PII detectors — both SKIP
(DataFog validates our regex-first approach but is heavier than needed; piisa is stale since
2024). Confirmed Twilio's canonical opt-out keyword list (STOP, STOPALL, UNSUBSCRIBE, CANCEL,
END, QUIT, REVOKE, OPTOUT) as VENDOR DATA — a 10-line constant, no library needed. Surprising:
no area produced a "USE" verdict — compliance/guardrails for this project's size is best served
by small hand-written lists, not by installing frameworks. 4 candidates added, all pass the
format checker.


## H4 LLM copywriting for CRM / real estate (2026-09-17)
Searched for real-estate/leasing prompt libraries, brand-voice linters, open leasing SMS/email
datasets, and marketing-copy evaluation benchmarks. Best find: **digital-marketing-pro**
(indranilbanerjee, MIT, 824 stars, active) — its `/check` pre-publish gate combines an AI-tell
scanner, a brand-voice distance score (≤0.15 threshold against a stored brand profile), and a
regex claim-verifier; worth mirroring as a pattern for our C4 validators, not worth installing.
Also found `efeoncepro/voice.md`, a tiny (1 star) but well-shaped spec for a per-brand
forbidden-words/length-limits file with a CLI linter — concept worth stealing, code too new to
trust. `KRASA-AI/real-estate-ai-skills` looked promising but couldn't be verified (7 stars, no
visible working prompt files) — SKIP. Confirmed via the CTIA Messaging Principles page that our
already-planned STOP/HELP opt-out wording matches the real industry standard (VENDOR DATA).
Searched hard for an open leasing-SMS dataset or a marketing-copy eval benchmark and found none
usable or free — this confirms C5's plan to hand-write the dozen templates is correct, no import
shortcut exists. 5 candidates added, all pass the format checker.


## H5 Evaluation that grades against a reference (2026-09-17)
Searched for actual code (not just papers) behind RocketEval/Check-Eval/TICK, plus Inspect AI,
DeepEval, Weave, and confidence-interval libraries for small labelled eval sets. Confirmed
RocketEval does have a public code repo (Joinn99/RocketEval-ICLR) proving the "checklist from
reference, graded yes/no, reweighted" idea is real, but it's a research artifact, not installable.
Inspect AI (UK AI Safety Institute, ~2,800 stars) and DeepEval (~18,300 stars) are both
professional, actively maintained frameworks, but both are sized for teams running many evals
continuously — too heavy for our one-off 100-200 record job. Best find: jacobgil/confidenceinterval
— a tiny MIT library that turns "73% pass" into "73% pass, 95% CI [64%, 81%]" via a Wilson score
interval, small enough to either install or copy as a 10-line function. wandb/weave is real
open-source but its whole value is a cloud dashboard we don't need, so SKIP. Verdict across the
area: no single tool is the "known professional choice" for this size of eval — the right move is
to hand-roll a small script mirroring RocketEval's checklist idea, DeepEval's JSON-score-plus-reason
judge prompt, and a Wilson-interval confidence calculation. 6 candidates added to candidates.md,
all pass the format checker (28 total).

## H6 Human review screens (2026-09-17)
Searched Argilla, Label Studio, Langfuse annotation queues, Arize Phoenix, promptfoo's viewer, and
Hamel Husain's annotation-app writing/tools, verifying each repo's license/stars/last-commit via
the GitHub API. The existing shipcheck `grade_server.py` (a minimal local keypress 1/2 pass/fail
server) was checked for as reuse-target but does not exist in this worktree — it's referenced only
as something PLAN-casestudy-bot.md plans to copy later; confirmed via PLAN-casestudy-bot.md line
144. Best find: a real but brand-new (1 star) tool called **vasari** (AntoineF23/vasari, MIT) whose
core idea is worth stealing even though the repo itself is too unproven to install — validate the
LLM judge against a small set of human labels with a confusion matrix / Cohen's kappa before
trusting it on the full batch. promptfoo's local `view` grid (pass/fail color table with expandable
diffs) is the best UI pattern to borrow for shipcheck's existing review screen. Argilla, Label
Studio, Phoenix and Langfuse are all real, actively maintained, well-known tools, but every one is
built for teams/continuous pipelines with their own server+database — installing any of them for a
single person grading 100-200 records once would be a downgrade in simplicity, not an upgrade.
Honest comparison verdict: shipcheck's existing lightweight keypress screen is already the right
size for this job; the only things worth taking from this whole area are two small patterns
(judge-vs-human agreement check, pass/fail color grid), not a new dependency. 6 candidates added to
candidates.md, all pass the format checker (34 total).
