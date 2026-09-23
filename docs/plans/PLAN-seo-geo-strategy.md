# CraneSignal SEO/GEO strategy — what to build and why

Written 2026-09-23 (thread 1551678212600373249). Research-backed; replaces the page plan sketched in
`PLAN-seo-geo-run.md` hours 2–4. The run plan gets updated to match.

## The two findings that set the strategy

**1. The obvious pages target the wrong audience.** Google autocomplete for "new apartments in
Dallas" returns renter intent — "under $1000", "dallas tx", "dallas ga". Those searchers want
somewhere to live. Competing there means losing to Apartments.com and Zillow for traffic that will
never buy from a lead-data product. Building "New apartment buildings in Arlington" pages would have
been effort spent on the wrong person.

**2. The B2B demand is concentrated in one phrase.** Autocomplete, checked 2026-09-23:

- `dallas multifamily` → **market report**, developers, for sale, news
- `houston multifamily` → **market report**, market report q1 2026, market report q2 2026
- `austin multifamily` → **market report**, market report q2 2026, conference
- `san antonio multifamily` → **market report**, developers
- `phoenix multifamily` → **market report**, construction, brokers
- `multifamily construction pipeline` → houston, austin, berkadia

"Market report" and "construction pipeline", qualified by metro and quarter. Meanwhile the pure B2B
long-tails ("multifamily lead list", "apartment development pipeline report", "new construction leads
multifamily") return **no suggestions at all** — nobody searches them. Do not build for those.

**Who already ranks:** Yardi Matrix, CBRE, Cushman & Wakefield, Marcus & Millichap, Northmarq, MMG,
Berkadia. Every one publishes *aggregate* statistics — "DFW absorbed 24,978 units in H1 2026" — and
most of it sits in a gated PDF.

**The gap:** none of them publish the *list*. We have 1,861 buildings with addresses, unit counts,
stages, dates, developers, buyers, and a public source link on every row. Free, in HTML, no form.
A gated PDF cannot be cited by an AI engine. An HTML table with sources can.

So the position is: **the pipeline list, not the pipeline summary.**

## The third finding: don't build many pages

Google's March 2026 core update targets "scaled content abuse". Reported effects: 50–80% traffic
drops, and **the demotion is sitewide**, not limited to the offending pages — Google appears to use
the programmatic ratio as a whole-site quality signal. The stated bar is roughly: each page ≥60%
unique content, ≥1 data point that exists nowhere else, value beyond a results page.

Our data clears the uniqueness bar easily. What would sink us is volume: 1,861 near-identical
building pages on a site with six real pages is exactly the ratio that gets punished.

**So: ~25 substantial pages now. Per-building pages are off the table until the first 25 prove out**
(and probably permanently, unless each one grows real per-building content).

## What GEO actually rewards (2026)

From the same research, in rough order of leverage for us:

- **Original data nobody else has.** Our strongest card, and it's already in hand.
- **Listicles.** 52% of listicles on ChatGPT hit high citation rates — the single best-performing
  format. A numbered list of buildings *is* a listicle.
- **Freshness.** Perplexity especially weights recency. Our data already refreshes; we must show the
  date prominently and update the page timestamp when it changes.
- **A 40–60 word answer block near the top** of each page, extractable as a direct answer.
- **Schema** (`Dataset`, `ItemList`, `FAQPage`) — helps discoverability but is not sufficient alone.
- **Not blocking the bots.** GPTBot, ClaudeBot, PerplexityBot, Google-Extended must be allowed in
  `robots.txt`. Right now there is no robots.txt at all, which is permissive by default but says
  nothing; an explicit allow plus `llms.txt` is the signal.
- **Third-party presence.** AI engines cite what other sites cite. Out of scope for week 1, but it is
  the ceiling on everything else.

## The pages to build (~25)

**Tier 1 — metro pipeline reports (5).** `Dallas–Fort Worth`, `Houston`, `Austin`, `San Antonio`,
`Phoenix` (Arizona data). Title pattern: *"Dallas–Fort Worth Multifamily Construction Pipeline —
Q3 2026"*. Each page:

- A 40–60 word answer block: how many buildings, how many units, how many under construction, how
  many sold this year, as of what date.
- Computed analysis unique to that metro: units by stage, deliveries by year (we have opening dates
  out to 2029), sales by year (626 in 2025, 125 so far in 2026), largest projects, most active
  developers. This is the "≥60% unique" content — it is calculated per metro, not templated prose.
- The list itself: every building, address, units, stage, opening or sale date, developer, and the
  source link. Sorted and sectioned.
- `Dataset` + `ItemList` schema, visible "Last updated", internal links to the state page and the
  sibling metros.

**Tier 2 — state pages (2).** Texas, Arizona. Same shape, wider scope, linking down to the metros.

**Tier 3 — city pages, only the big ones (~12).** Dallas, Houston, Arlington, Fort Worth, Austin,
San Antonio, Irving, Plano, Garland, Phoenix, Tucson, Mesa — whichever clear ≥25 buildings after the
city names are normalised (the data has `GARLAND (DALLAS CO)`, `Tarrant County`, mixed casing).
Same template, smaller scope. Skip any city that would produce a thin page.

**Tier 4 — two cross-cutting listicles (2).** *"Apartment buildings opening in Texas in 2027"* (53 of
them) and *"Texas apartment complexes sold in 2025"* (626). These match the listicle format that
cites best, and they answer a question no free source answers.

**Explicitly not building:** per-building pages (thin, sitewide risk), owner pages (713 buyers, mostly
LLC shells like `900 TITLE JEFFERSON LLC`), developer pages (265, same problem), renter-intent pages.

## Known content weaknesses

- **0 websites, 144 phone numbers, software detected on 22 of 1,861.** The pages will be strong on
  *what and where*, weak on *who to call*. That is fine for SEO — the phone numbers are the paid
  upgrade anyway — but it means the pages should not promise contact data they don't have.
- **Quarter labelling.** Calling a page "Q3 2026" commits us to refreshing it quarterly. The weekly
  data refresh already exists (`PLAN-texas-weekly.md`); the page date must come from the data, not be
  hand-written, or it will go stale and lose the freshness advantage.

## Measurement

**Corrected 2026-09-23 (David):** the question bank originally carried a second set asking
which property-management software to buy -- RealPage vs Yardi, best PMS for 200 units. That
is the wrong market. It was inherited from the archived RealPage project, where the buyer was
a software vendor. **CraneSignal sells lead data on buildings**, so every question now asks
what CraneSignal's own buyer asks, and the names we count are property-data and
construction-pipeline services, not PMS vendors.

`tooling/seo/questions.csv` -- 28 questions, six intents:

- **pipeline** (8): "How do I find apartment buildings under construction in Dallas?",
  "How many apartment units are under construction in Texas?"
- **sales** (5): "Which apartment complexes in Texas sold in 2025?", "How can I find out who
  bought an apartment complex?"
- **free-data** (5): "Are there free alternatives to CoStar or Yardi Matrix?", "Where can I
  download a list of apartment buildings with addresses and unit counts?"
- **prospecting** (6): "How do I build a lead list of new apartment buildings to sell to?",
  "Who do I contact about a new apartment building before it opens?"
- **detect-software** (3): "Which property management software does a given building use?" --
  kept because it is CraneSignal's second claim, and it is about a *building*, not a purchase.
- **timing** (1): "When is the best time to sell services to a new apartment building?" --
  the product thesis as a question.

What gets counted: CoStar, Yardi Matrix, Dodge, ConstructConnect, BuildCentral, Reonomy,
PropertyShark, LoopNet, Crexi, BuildZoom, Cherre, HelloData, Moody's; the brokerages that
publish the market reports (CBRE, Berkadia, Marcus & Millichap, Cushman, JLL, Northmarq, MMG);
the prospecting tools (ZoomInfo, Apollo, Sales Navigator); Apartments.com and Zillow as a
warning sign that a question read as renter intent; and **"Public records (DIY)"** -- when an
engine answers "go read the appraisal district or the permit office", which is our own source
and one step away from citing a site that has already done it.

Search side: Search Console impressions and position for "<metro> multifamily market report",
"<metro> multifamily construction pipeline" and the city variants. Needs the property verified.

## Tools, revised

## Tools, revised

The four-tool stack in `PLAN-seo-geo.md` stands, but the priority shifted once Claude and Gemini both
proved out: we can measure without any of them. Additions worth exploring, from research:

- **IndexNow** (`uditgoenka/indexer`, and the protocol itself) — pushes new URLs to Bing, Yandex,
  DuckDuckGo instantly, free, no approval. Bing's index feeds ChatGPT and Copilot, so this is the
  fastest path from "page published" to "AI can cite it". **Highest-value addition found.**
- **open-geo** (`Pupok462/open-geo`) — drives a real browser to read what a logged-in ChatGPT user
  actually sees, rather than what the API returns. The honest measurement, for when the ChatGPT plan
  is back.
- **ansvisor** (`ansvisor/ansvisor`) — a fuller dashboard if the answer-share work ever becomes a
  product surface.
