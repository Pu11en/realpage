# RealPage Knowledge Base

Single source of truth for everything we know about RealPage (realpage.com) —
property management software company.

**The constraint: outside-in only.** We have no access to RealPage — no
insiders, no product login, no customer data, nobody there to ask. Everything
here comes from public sources. **The goal:** build a finished, working MVP
from this evidence that RealPage (or a business like theirs) would actually
use, show from outside that they don't already have it, and pitch it. Drew
makes the calls; ask him when a decision is his.

Current direction and plans: `09-build-ideas/brainstorm-2026-09-10-pitch-to-realpage.md`.
Every plan passes `/mvp-plan-review` (`.claude/skills/mvp-plan-review/`) before
a build session starts.

## How to use this KB (for any future session)

1. Read this README first.
2. For the live work plan read `PLAN-v5.md` (Open WebUI chat + Google sign-in).
3. Older plans, handoffs and QA logs live in `archive/` (see `archive/README.md`).
   These are the resume-cold files — trust them over any chat memory.
4. Every folder holds markdown files. Synthesized files cite raw files; raw
   files carry source URL + fetch date. Trust raw over summary on conflict.
4. Add new evidence as files, register them in the folder's index section
   below, never delete raw evidence.

## Conventions

- One topic per file. File names: lowercase-hyphenated, dated `YYYY-MM-DD-`
  prefix only when multiple snapshots of the same thing exist.
- Every file starts with a header block: `Source:`, `Fetched:`, `Method:`,
  `Confidence:` (high/medium/low).
- Raw captures live in `raw/` (verbatim excerpts, JSON dumps, page text).
  Distilled insight lives in the numbered folders and must link the raw file.
- Voice-of-customer files preserve **exact phrases** in quotes — never
  paraphrase complaints; paraphrase belongs in the analysis line below the quote.
- Claims without a linked source are marked `(unsourced)`.

## Map

| Folder | What's inside |
|---|---|
| `01-company/` | Profile, ownership, leadership, timeline, financials |
| `02-products/` | Product lines, pricing, tech stack, integrations |
| `03-reviews/` | G2, Capterra, TrustRadius, Glassdoor, app-store reviews |
| `04-reddit/` | Subreddit evidence packs with URLs + dates |
| `05-social/` | X posts (`x/`), LinkedIn observations |
| `06-news/` | DOJ antitrust case, press, product launches |
| `07-competitors/` | Yardi, AppFolio, Entrata, Buildium, etc. |
| `08-voice-of-customer/` | Distilled pain themes, personas, exact language |
| `09-build-ideas/` | Ranked things we could build, tied to evidence |
| `raw/` | Unprocessed captures (never edit, only add) |
| `tooling/` | Local scraping assets, how to run them |

## Ground rules

- Collection is read-only toward third parties: no posting, voting, or
  account actions. Rate-limit politely. Respect logged-in-session boundaries
  (X session belongs to Drew; use it only for reads).
- LinkedIn is auth-walled and bot-hostile: capture manually or via Drew's
  logged-in browser only when he initiates it; label those captures clearly.
