# PropertyStack lead finder, part 4: software, sales, who to call, ranking

Part of the lead finder. **Read the rules in `PLAN-lead-finder.md` first** (area-agnostic: no place
names in code; Plano is never rerun; never guess facts; SearXNG first, Jina fallback; localhost only,
no push). **NOT approved to run yet.** Starts after part 1 is merged; can run **at the same time as parts 2, 3 and 5**. Touches only its own skill folders.

Run with: `Do the next unticked task in PLAN-lf-4-software-contacts.md, then tick it and stop.`
Check: `bash tooling/qa/check-lead-finder.sh`
Try: `bash tooling/dev.sh`
Open: (behind the scenes; results show on the site after part 6)

## How to try it (30 seconds)
1. Run the Check line: it passes.
2. Sample building pages come back as RealPage (dropped), "on Yardi today", or "not picked yet".
3. Sample leads are ranked: soonest opening first, bigger next, planned projects under permitted ones, each with a one-line reason.

## Tasks

- [ ] **4.1 Software fingerprints.** `detect-software` gets a rules file in the Wappalyzer JSON
  format with **our own** rules (RealPage / OneSite / loftliving / activebuilding, Yardi RentCafe /
  securecafe, Entrata, AppFolio, ResMan, MRI, Knock, SightMap …), merged with `tooling/pms_detect.py`.
  Cheap page check first; full browser only if unclear. Any area (remove Plano paths). Fixture tests.
  Commit.
- [ ] **4.2 Double check + drop RealPage.** Before a RealPage or competitor verdict, a second check
  (another page on the site or the resident portal link) must agree, else "unknown". RealPage
  buildings dropped; others "on <competitor> today" / "not picked yet". Fixture tests. Commit.
- [ ] **4.3 `find-sales-news` (new).** GDELT (free news index) + SearXNG news: apartment sales in
  the state's cities, last 24 months → building, buyer, date, units, link (stage sold). Fixture
  tests. Commit.
- [ ] **4.4 Who to call, any area.** `find-website` + `contact-scrape` take any area: developer (or
  new owner) office phone + website; `phonenumbers` pulls and de-duplicates numbers, office lines
  above fax/cell; a named person only if a permit, agenda or news page names one. Fixture tests.
  Commit.
- [ ] **4.5 `score-leads`, any area.** Remove Plano bits. Order: soonest opening → more units → not
  picked above competitor; unknown opening ranked by permit date and shown "Opens: not public yet";
  **Planned below permitted**; one-line "why" per lead. Fixture tests. Commit.
