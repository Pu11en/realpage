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

