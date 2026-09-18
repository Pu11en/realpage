---
name: deep-dive
description: PropertyStack — one-lead sales brief (Bottom line, who they are, why now, who to ask for, opener, questions, objections, sources) for a single lead from leads.csv. Use when asked for a "deep dive" or "brief" on one apartment community or upcoming project.
---

# deep-dive

**Inputs:** `--area` (e.g. `plano-richardson`) + one lead, by `ref_id` (the `leads.csv`
column: an `apt_id` for existing buildings, a project id for upcoming ones) **or** by name
(case-insensitive match on `leads.csv` `name`; if several match, ask which one).
**Reads:** `data/<area>/leads.csv`, `master.csv`, `5-sales.csv`, `contacts.csv`,
`6-upcoming.csv` (upcoming leads), plus the web.
**Writes:** `data/<area>/briefs/<ref_id>.md` (create `briefs/` if missing; overwrite an
older brief for the same lead).
**Checks:** `python3 skills/deep-dive/validate.py data/<area>/briefs/<ref_id>.md` must pass.

All paths are relative to `propertystack/`.

## Steps

1. **Find the lead.** Pull its row from `leads.csv` (rank, score, signal, units, software,
   why, sources). Then join by `ref_id`:
   - `master.csv` (`apt_id`): address, year built, owner, website, software, `proof_url`.
   - `5-sales.csv` (`apt_id`): sale date, new/previous owner, `source_url`.
   - `contacts.csv` (`apt_id`): leasing-office phone/email + `source_url`. These are the
     **only** phones/emails allowed in the brief.
   - Upcoming leads (`signal` = `upcoming`): `6-upcoming.csv` (`project_id`): developer,
     stage, stage date, expected opening, `source_url`.
2. **Web research** (budget: **max ~12 Jina searches per brief**; count them and stop at 12).
   - Search with Jina (`lib/jina.py`, `Jina().search(q)`), e.g.
     `"<name>" <city> apartments management company`, `"<name>" <city> sold`,
     `"<name>" reviews portal OR payment`, `"<management company>" regional manager Dallas`.
   - Read pages with **crawl4ai at `http://localhost:11235`** first
     (`POST /md` with `{"url": "<page>", "f": "fit"}`, markdown back). If crawl4ai is down or
     the page comes back empty, fall back to `Jina().read(url)`. Reads don't count toward the
     12-search budget but keep them reasonable (~10).
   - Find: the **owner** and **management company** (property site footer, "managed by",
     news); **resident reviews** mentioning the portal, online payments, rent app or
     maintenance requests (Google/ApartmentRatings/Yelp pages); **news** (sale, renovation,
     new manager, lease-up); and the **decision-maker** (below).
3. **Decision-maker ("Who to ask for").** The regional manager / VP of operations /
   director of property management at the management company that covers this building,
   taken from a **public page only** (company team page, press release, news article,
   public LinkedIn result title). Give name, title, company and the link. **Never guess an
   email or phone**, never build one from a name pattern. If nothing public is found, write
   `- Not found: <what was searched>` — that's a correct answer, not a failure.
4. **Write the brief** in the layout below, then run `validate.py` on it and fix anything it
   reports before finishing.

## The layout (every brief, these 8 headings, in this order)

```markdown
# Deep dive: <name>

## Bottom line
- 2–4 bullets: call or not, why (the strongest reason), who to ask for.

## Who they are
- <name>, <city> TX, <units> units, built <year>. Owner: <owner>. Manager: <manager>.
- Leasing office: <phone/email from contacts.csv only, or leave the line out>
- Current software: <software> (<proof_url>)

## Why now
- One bullet per reason, each with its link: sale, new manager, lease-up,
  resident complaints about portal/payments.

## Who to ask for
- <Name>, <title>, <company>: <public link>   (or "Not found: ...")

## 30-second opener
Hi, this is [your name] with [your company]. ... (2–4 sentences, tied to the Why now)

## 3 questions
1. ...
2. ...
3. ...

## 2 objections + answers
- "<objection>" <answer>
- "<objection>" <answer>

## Sources
- every link used anywhere above, one per line
```

**Upcoming projects:** same layout. "Who they are" = project name, city, units, **developer**
and **expected opening date** (from `6-upcoming.csv` or news); software = **"not chosen
yet"**. "Who to ask for" = the developer's (or chosen manager's) person in charge of
lease-up/operations, same public-page rule.

## Rules

- Every line under **Why now** and **Who to ask for** carries a URL (or says "not found").
- No email or phone anywhere unless it's in `contacts.csv`.
- The opener says "[your name]" and "[your company]" and **never** claims to work for the company
  you're calling ("with [their company]", "from [their company]"). The seller could be any
  property-management software vendor.
- Facts only from the CSVs or a page you actually read; if unsure, say "unconfirmed".
- Plain words, short bullets. No PDF — the brief is text (the site chat has a Copy button).
- Bottom line comes **first**, always.

## Limits

- ~12 searches is the cap; if the budget runs out, write what you have and mark missing
  pieces "not found".
- Yelp, ApartmentRatings and ForRent block both crawl4ai and Jina read (CAPTCHA/403). Use
  their search snippets marked "(search snippet only; unconfirmed)", or HAR.com reviews,
  which do load. Company team pages (e.g. keyrealestateco.com/team/) are the best source
  for the decision-maker.
- Reviews and team pages go stale; the brief is a snapshot of the day it was written.
