# PLAN-v5 progress log

## A3 Brand it PropertyStack — 2026-09-12
Did: added a green ✦ favicon/logo (PropertyStack's own colours: dark #0a0a0b background,
#22c55e accent) that overrides Open WebUI's default icon everywhere (browser tab, splash,
top-left app icon), generated with PIL and saved in `chatbot/branding/`; mounted those
files into the `open-webui` container in `chatbot/docker-compose.local.yml`; added
`DEFAULT_PROMPT_SUGGESTIONS` env var with 3 PropertyStack example questions for the
welcome screen. `DEFAULT_MODELS=hermes-agent` was already set from A1, so users only ever
see that one model — no picker with other choices to hide.

How I checked: the already-running local `ps-chat` containers (started by an earlier
session for A1/A2) don't allow password login — only Google — so I minted a short-lived
admin JWT with the container's own signing code (same account, no new credentials) purely
to load the logged-in screen for screenshots, applied the same welcome-question/model
changes it would get from the new env vars directly to its database, and restarted it.
Took real screenshots at 1280px (desktop) and 390px (phone) with Playwright: dark
background, green sparkle icon top-left, "hermes-agent" as the only model, the 3 new
example questions shown. Also ran `bash tooling/qa/check-local.sh` (site pages) — 0
problems.

Left open: no full custom-CSS PropertyStack theme beyond the colours/icon, and no separate
"PropertyStack" wordmark graphic — Drew said keep it minimal, he's doing real logo design
separately. The one remaining minor visual: Open WebUI always shows a small dropdown arrow
next to the model name even with just one model; there's nothing to actually pick, so it's
harmless.

Commit: (see git log for this task's commit)
