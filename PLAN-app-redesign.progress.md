# Progress: PLAN-app-redesign

## T1 Fonts + shared colors + app frame — done 2026-09-15
- Self-hosted Inter + Plus Jakarta Sans (fontsource variable latin woff2) in `site/fonts/`.
- `site/css/styles.css`: @font-face for both, landing `:root` tokens (plus `--bad`, `--blue-soft`), old dark names kept as aliases; `--font` Inter, `--font-head` Plus Jakarta Sans on h1-h3/.wordmark; sidebar = paper-2, active tab blue on blue-soft with amber left marker; Ask button amber; score high/mid/low = ok/warn/muted red; sig tags + placeholder banner use soft badges.
- `site/js/app.js`: vendor pill greys readable on white.
- Check: `bash tooling/qa/check-design.sh` passes (quick check 0 problems; design list still empty). Both fonts confirmed loaded in the browser.
- index.html NOT added to design-pages.txt: its inline "New" pill still uses #22c55e — T2 fixes it. Screenshot: `docs/design-screens/T1-index.png`.
- Note: the landing page lives only in the main checkout (`business/` is not in this branch); T9 must handle that.
