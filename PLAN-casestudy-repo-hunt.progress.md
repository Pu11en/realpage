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
