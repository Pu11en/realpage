# Case-study service

This is a separate, read-only proposal service. It accepts assignment JSONL at
`POST /case-study/api/run`, serves the workbench at `/case-study`, and exposes
`GET /health` for the service health check. It exports proposed messages and
actions; it never sends a message or writes to a CRM.

## Local container

From the repository root:

```bash
docker build -f casestudy/Dockerfile -t cranesignal-case-study .
docker run --rm -p 18091:8080 -e CASESTUDY_OFFLINE=true cranesignal-case-study
```

Open `http://localhost:18091/case-study`. The signed-in CraneSignal preview also
routes `/case-study*` to this service through its existing authentication gate.

## Railway service

Create a separate Railway service named `propertystack-case-study` from this
repository. Set its Dockerfile path to `casestudy/Dockerfile`; the image command
is already `python -m casestudy.web --host 0.0.0.0`, so a Railway Start Command
override is not needed. If Railway requires an explicit Start Command, use that
same command.

Set `DEEPSEEK_API_KEY`, `DEEPSEEK_MODEL`, and optionally `DEEPSEEK_BASE_URL` on
the case-study service only. Without the key or model, requests automatically
use the validated offline templates. Optional limits are
`CASESTUDY_MAX_REQUEST_BYTES` (default 2 MiB) and `CASESTUDY_MAX_BATCH_SIZE`
(default 100). Set the front-door site's `CASESTUDY_UPSTREAM` to
`http://propertystack-case-study.railway.internal:8080`, and configure Railway's
health check path as `/health`.
