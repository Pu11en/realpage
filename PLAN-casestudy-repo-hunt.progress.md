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
