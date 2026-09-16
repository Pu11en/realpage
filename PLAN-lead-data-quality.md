# CraneSignal leads: clean phone numbers, duplicates and missing facts

Goal: Lead answers in the chat show no mangled phone numbers, no project listed twice, and each permit-office phone is clearly labelled as such.
Done when: `python3 tooling/leadcheck/report.py` shows 0 broken phones and 0 duplicates, and the Check tests pass.

Written 2026-09-15 (thread 1549506016125911081). Drew tested the chat and found bad lead data:
a phone shown as "8-773-367-2410" (Austin, South Lamar), the same project listed twice with
different phones, and rows with no unit count. The phones come from state permit records, so
they are the developer's/owner's office, not the leasing desk -- the chat should say so.
No scraping, no new data collection: only check and clean what we already have.
Localhost only; **never push** (Drew pushes after trying it).

Run with: `Do the next unticked task in PLAN-lead-data-quality.md, then tick it and stop.`
Check: `python3 -m pytest -q tooling/qa/fixes_tests/test_lead_data_quality.py chatbot/tests`
Try: `python3 tooling/leadcheck/report.py`
Open: no page; the report prints in the terminal and is saved as `tooling/leadcheck/report.md`

## How to try it (30 seconds)
1. Run `python3 tooling/leadcheck/report.py`: it prints how many lead rows have a broken phone,
   a duplicate twin, or no unit count, per area.
2. After task L2, re-run it: broken phones and duplicates are 0.
3. Ask the local chat "give me top leads any area": phones are labelled as the permit contact,
   and no mangled number appears.

## Tasks

- [ ] **L1 Find the bad rows.** Add `tooling/leadcheck/report.py` (offline, reads
  `propertystack/data/*/chat-leads.csv`): flags phones that are not 10 US digits, duplicate
  projects (same address or same name+city), rows with no unit count, and links that are not
  http(s). Save `tooling/leadcheck/report.md` with counts per area and up to 10 examples each.
  Add `tooling/qa/fixes_tests/test_lead_data_quality.py` checking the flagging rules on a small
  fixture. Run Check. Commit.
- [ ] **L2 Clean them.** Add `tooling/leadcheck/clean.py`: blanks phones that fail the check
  (never guesses a new one), merges duplicate rows (keep the row with more facts; keep the
  earliest opening date), and leaves unit counts alone. Run it over every area's
  `chat-leads.csv`, then re-run the report and put before/after counts in
  `PLAN-lead-data-quality.progress.md`. Extend the test to prove a bad phone is blanked and a
  duplicate pair becomes one row. Run Check. Commit.
- [ ] **L3 Say where the phone came from.** In `chatbot/hermes-profile/SOUL.md` lead lists and
  deep dives: a phone from `office_phone` is shown as `📞 **<phone>** (permit contact)`, and a
  phone found on the building's own website stays plain. Never show a phone that fails the
  10-digit check. Add the rule check to `test_lead_data_quality.py`. Run Check. Commit.
