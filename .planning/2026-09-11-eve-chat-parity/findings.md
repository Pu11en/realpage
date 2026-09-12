# Findings: Eve chat parity

## Eve vs site bot (config files, 2026-09-11)
| Setting | Eve | Site bot |
|---|---|---|
| memory_enabled / user_profile_enabled | true / true | false / false |
| compression | on, 0.5 → 0.2 | off |
| tool_progress / show_cost | true / true | false / false |
| max_turns | 90 | 8 |
| tools | full (terminal, web, files, sub-agents) | read-only `propertystack` plugin |
| where it talks | Telegram (+ BlueBubbles) | website via `chatbot/proxy.py` |
| saved state | persistent Hermes home | wiped each deploy |

## Hermes web API (docs: API server page)
- Chats kept on the server: `X-Hermes-Session-Id` header, or the Responses API
  (`previous_response_id` / `conversation`), or `POST /api/sessions/{id}/chat[/stream]`.
- History: `GET /api/sessions/{id}/messages`.
- Streaming with `hermes.tool.progress` events (the "what it's doing" line).
- Stop a run: Runs API `POST /v1/runs/{id}/stop`.
- `X-Hermes-Session-Key` gives per-user memory scope, **for Honcho memory**.

## Memory catch (docs: memory page)
- Built-in memory (MEMORY.md / USER.md) is **one per profile**: every visitor would
  share it. Not safe on a public site.
- Per-visitor memory needs an external memory provider (Honcho, Mem0, Supermemory, …)
  alongside it. Unverified: which ones need a paid account or API key. Check before A2.

## Deep Chat (deepchat.dev docs)
- Has: `browserStorage` (saved chats), streaming, suggestion buttons, `connect` handler,
  `htmlClassUtilities` for styling our citation chips.
- Missing: copy button, Retry button, "New chat" button, ageing-out.
- Trial page works: `site/chat-trial.html` (tested headless with faked replies).

## Current chat code (site/master-table.html)
- Hand-built, inline in one page. Browser re-sends last 10 messages as history.
- Live proxy CORS already allows `http://localhost:8765`.

## Memory add-ons (Hermes memory-providers docs, summarised by a small model — verify in A2)
| Add-on | Runs where | Needs | Keeps users apart |
|---|---|---|---|
| Honcho | cloud or self-hosted | `HONCHO_API_KEY`, paid | yes (peers) |
| Mem0 | cloud or open-source | `MEM0_API_KEY` or none (OSS) | yes (`user_id`) |
| Hindsight | cloud or local | `HINDSIGHT_API_KEY` or none (local) | yes (`bank_id`) |
| Supermemory | cloud or self-hosted | `SUPERMEMORY_API_KEY` or none (self-hosted) | yes (`{identity}` tag) |
| RetainDB | cloud | $20/month | not stated |
| OpenViking, Holographic, ByteRover | local | none | not stated |
- Enable with `memory.provider: <name>` in config.yaml.
- Unknown: does the visitor ID header reach Mem0/Hindsight/Supermemory (only Honcho is
  documented)? Can built-in memory stay off while an add-on is on?

## Holes (code read, 2026-09-11)
H1–H13 listed in PLAN-v4.md "Holes in today's chat". Proxy errors are raw ("agent error", "agent timed out", "rate limit reached"); browser has no own time limit; history sent = last 10 turns, saved = 20 turns / 40 bubbles.

## Ready-made chat frontends for Hermes (2026-09-11)
Hermes ships no chat UI of its own, but its API server is built for OpenAI-style
frontends; the code special-cases **Open WebUI** (session mapping, tool progress) and the
docs have a full Open WebUI guide. Also listed: LobeChat, LibreChat, AnythingLLM, NextChat,
ChatBox, Jan, HF Chat-UI, big-AGI.
- **Open WebUI** (MIT-ish, Python+Svelte, one Docker image): accounts + per-user chats,
  chat list/search/delete, streaming, stop, regenerate, copy, edit, mobile PWA, admin
  panel, rate limits. Needs a login (sign-up can be open or invite-only). Runs as its
  own Railway service next to the bot; not embedded inside PropertyStack pages.
- **LibreChat** (MIT): same class, heavier setup (Mongo), more multi-model features.
- Embeddable widget kits (assistant-ui, Vercel AI SDK): build-it-yourself, no chat
  list/auth out of the box — closer to what we're doing by hand.
Tradeoff: Open WebUI = solid, everything an agent chat needs, but it's a separate
"app" with login, styled like ChatGPT, not the PropertyStack sidebar.
