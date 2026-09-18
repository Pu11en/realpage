# Progress: investor launch site (2026-09-18)

## T1 ✅
Check script already passes with 0 violations. Only 1 RealPage reference in business/ (in vendor list, which is allowed). Ticked the box.

## T2 ✅
Created landing page at business/marketing/landing/index.html with:
- Investor headline: "See which apartment buildings just sold, who bought them, and what's being built"
- "Start free" CTA button linking to "/" (root will eventually redirect to /map.html when login gate is removed in T3)
- Example lead card (Legacy Arapaho building in Richardson, TX)
- Design matching screenshot: blueprint blue background, grid pattern, white cards, amber buttons
- Responsive for mobile
- Copy saved to site/landing.html for dev server
- Test suite created in business/tools/test_landing.py (validates headline, CTAs, no RealPage text, branding)
- All tests pass; check-no-realpage-target.sh still exits 0
- Commit: 94e17bd

## T3 ✅
Removed the sign-in check (forward_auth) from site/Caddyfile, so Map, Early Leads, building pages, Under the Hood, landing.html and their data load signed out. "/" still opens the Map, so the landing page's "Start free" link lands there with no login.
- Tests: test_e1_signin.py now runs the real Caddyfile and checks every page returns 200 signed out with content and no RealPage text; test_t4_not_found.py updated. 203 tests pass; check-no-realpage-target.sh exits 0.
- Commit: 6bb3343
- Open: the chat still asks for an account inside its panel (T4 reshapes that). Nothing pushed; the live site keeps its gate until this is deployed.
