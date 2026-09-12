# Open-source options to "fix everything" in the chat — research note

Context: the chat panel in `site/master-table.html` + `site/js/app.js` is hand-rolled
vanilla JS. PLAN-v3.md lists fixes: persistence notice, error retry, age-out,
copy button, suggested follow-ups, chat on every page. Off-the-shelf open-source
components already ship most of these.

## Option A — Deep Chat (recommended)

- Repo: https://github.com/OvidijusParsiunas/deep-chat — MIT, framework-agnostic **web component** (`<deep-chat>`), docs: https://deepchat.dev
- Covers out of the box: error handling + retry on failed messages, suggested
  messages (intro + follow-up), speech-to-text, file upload, streaming, full
  theming via CSS variables, works with any backend via a `connect` handler
  (our chatbot API drops straight in).
- Persistence: not automatic, but `getMessages()` + submit events make a
  localStorage save/restore ~15 lines (we already have that logic; it ports).
- Weight: single bundled web component (~100 kB); no framework needed.
- Tradeoff: restyle to match the site theme; abandon our custom markup.

## Option B — @nlxai/chat-widget

- Open source (Apache-2.0), very lightweight, conversation history handling
  built in, designed for embeddable "chat with us" widgets.
- Tradeoff: fewer AI-chat features (no suggested follow-up chips, less active
  community than Deep Chat).

## Option C — Typebot / Botpress (self-hosted builders)

- Full visual chatbot builders, self-hostable, open source.
- Tradeoff: heavy — a server + builder UI for what is currently one static
  page + small API. Overkill here.

## Option D — keep hand-rolled, port features manually

- PLAN-v3 as written. Zero new deps, but we re-implement what Deep Chat ships.

## Recommendation

Swap the chat UI for **Deep Chat** (Option A): one script tag + a `connect`
handler to the existing chatbot backend. It kills PLAN-v3 items 2.2 (error
recovery), 3.1 (copy), 3.2 (suggested follow-ups) and makes 4.1 (chat on every
page) trivial — the same component mounts on all pages, sharing localStorage.
Keep our existing persistence code (2.1/2.3) feeding its message API.
