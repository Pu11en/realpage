# Handoff: CraneSignal marketing + outreach (2026-09-15)

PropertyStack was renamed **CraneSignal**. Business work lives in `/home/drewp/main-projects/realpage/business/` (its own local git repo, never push; `BUSINESS.md` is the hub, read it first). The product repo is `realpage` (branch `local-test` → `main`, pushed 2026-09-15 by another session).

## What's live
- **cranesignal.com** (+www): marketing page. Source `business/marketing/landing/index.html`, Railway service `propertystack-landing`. Deploy: `cd business/marketing/landing && railway up --service propertystack-landing --ci`. Tests: `python3 business/tools/test_landing.py` (63 checks) and `bash business/tools/check-biz.sh tools/monday_list.py`.
  - Lean page: short headlines ("New apartment buildings. Before your competitor calls."), no small paragraphs, no Q&A, no bio. "Start free" buttons → **https://app.cranesignal.com/** (the dashboard, not the chat sign-in page). Email "one free building" form kept as backup (signups on the Railway volume; admin key in `~/.config/propertystack/landing-admin.env`).
  - Design: bold blueprint/permit-board look, tower-crane logo (files in `business/marketing/brand/logo/`), Archivo font.
- **app.cranesignal.com**: product dashboard + "CraneSignal Agent" in the side panel. Sign-in: Google or email+password (same email = one account). Free plan: 10 questions/day, 3 deep dives/week; stand-alone chat pages redirect to the dashboard (both in the 2026-09-15 push).
- **Booking (Cal.com)**: https://cal.com/drew-pullen/propertystack-intro and /propertystack-feedback, titles renamed CraneSignal (link slugs kept).
- **Domain**: Porkbun; `business/tools/connect_domain.py` connects subdomains to Railway (Railway CLI custom-domain is broken; script uses the API). Keys: `~/.config/propertystack/porkbun.env`.

## Marketing + outreach assets (all saved, committed, renamed to CraneSignal)
- `business/marketing/assets/outreach.md`: LinkedIn gift-first notes (4 buyer types), gift emails, call/voicemail scripts, objections, early-access offer.
- `business/marketing/assets/journey-messages.md`: 13 customer-journey messages.
- `business/marketing/assets/content.md`: weekly metro post, X and Reddit replies, newsletter template, 60-second demo script, LinkedIn profile makeover.
- `business/marketing/assets/call-kit.md`: call sheet, prep checklist, objections with research quotes, 4 role-plays.
- `business/marketing/assets/pdf/`: one-pager, sample lead pack, deep-dive brief (PDFs rebuilt with the new name).
- `business/marketing/assets/lists/`: associations, 60 vendors (weak: mostly Houston trades), trade shows, podcasts, events, tracking sheet.
- `business/marketing/2026-09-14-gtm-plan.md`, `2026-09-14-customer-journey.md`, `2026-09-14-channels-and-assets.md`, `2026-09-14-copywriting-plan.md`.
- Research: `business/blueprint/` (reddit-evidence, copy-system), `business/idea/research/` (YouTube quotes verified against `business/raw/`).

## Decisions to keep
- No prices anywhere; free early access / freemium. Any US area, never Plano-centric. Guide = Minimalist Entrepreneur skills (not Bizkit).
- Lead buyer = **business development at property management companies**; also software sales, resident tech, suppliers, lease-up agencies.
- Outreach = gift first (a real building in their metro), LinkedIn + email; PM Reddit hates vendor pitches.
- Copy style: short, customer's own words, no AI slop (no-ai-slop skill in `~/.agents/skills`).

## Next steps
1. **Check the pushed app**: sign up a test user on app.cranesignal.com, see the crane icon, ask 11 questions (11th = friendly limit), open a direct chat link (→ dashboard), then delete the test user (Open WebUI sqlite via `railway ssh --service propertystack-chat`, see memory `porkbun-railway-domains`).
2. **Outreach**: update `outreach.md` links to cranesignal.com / app.cranesignal.com ("Start free"), then write Drew's first 10 LinkedIn notes + gift emails to PM business development people (real names by metro; build the list).
3. **Posting**: turn `content.md` into ready-to-post weekly metro post + Reddit/X drafts for CraneSignal.
4. Optional: drew@cranesignal.com email; signup email alerts; LinkedIn banner/one-pager in the new blueprint look.
5. Drew chores: rotate the Porkbun and Cal.com API keys (both were pasted in chat).

## Talking to Drew
Max 5 sentences, plain words, end with one multiple-choice question (4–5 options, recommendation first). Do whole-page design passes, never section by section.
