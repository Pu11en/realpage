# PropertyStack chatbot (Task 8)

Hermes agent on Railway, eve-agent pattern (`github.com/Pu11en/eve-agent`):
upstream `nousresearch/hermes-agent` image + a repo-managed `hermes-profile/`
copied into `$HERMES_HOME` on every boot. Model: `deepseek/deepseek-v4-flash`.

## Pieces

| Path | What |
|---|---|
| `Dockerfile` | Build context = repo root. Bakes `propertystack/data/plano-richardson/*.csv` and research folders `01-company` .. `08-voice-of-customer` in read-only. |
| `docker/start-hermes.sh` | Starts the Hermes API server on `127.0.0.1:8642` (internal key, never public) and `proxy.py` on `$PORT`. |
| `proxy.py` | The one public endpoint: `POST /chat {"message": "...", "history": [{"role","content"}, ...last 10]}` -> `{"answer", "citations", "seconds"}`. `GET /health`. CORS for the site, 1000-char cap, 30 req/hour per IP, 3 concurrent, 120s timeout. |
| `hermes-profile/SOUL.md` | Good-answer rules + hard guardrails from PLAN-v1.md "Chatbot spec". |
| `hermes-profile/config.yaml` | API server gets only the `propertystack` toolset (no terminal, files, web, memory). `max_turns: 8` budget. Memory off. |
| `hermes-profile/plugins/propertystack/` | Tools: `ps_schema`, `ps_sql` (single SELECT, read-only SQLite + authorizer), `ps_research_search`, `ps_research_read`. CSVs load into SQLite at startup. |
| `hermes-profile/skills/query-propertystack/SKILL.md` | Table/citation map and steps. |

## Railway

Second service `propertystack-chatbot` (https://propertystack-chatbot-production.up.railway.app) in the `propertystack` project, deploying
from `main` of this repo. Variables: `RAILWAY_DOCKERFILE_PATH=chatbot/Dockerfile`,
`DEEPSEEK_API_KEY` (same key eve-agent uses; set in Railway, never committed).
Optional: `CHAT_ALLOWED_ORIGINS`, `CHAT_RATE_PER_HOUR`, `CHAT_MAX_CONCURRENT`.

## Local test

```bash
docker build -f chatbot/Dockerfile -t ps-chatbot .
docker run --rm -e DEEPSEEK_API_KEY -e PORT=8080 -p 18080:8080 ps-chatbot
curl -s localhost:18080/chat -H 'Content-Type: application/json' -d '{"message":"Top 5 leads?"}'
```

The data is baked into the image, so a data refresh needs a redeploy (push to main).
