# Findings & Decisions

## Requirements

- Complete only C13: local live-style HTTP rehearsal, exact export parsing, offline and malformed recovery, README, and one-page interview card.
- Run the complete rehearsal twice, then the full case-study test suite.
- Make no live model calls, pushes, deployments, new-key use, or other project work.

## Research Findings

- The service exposes `GET /health`, `POST /case-study/api/run`, and the workbench at `/case-study`.
- The API returns canonical `submission_jsonl`, per-record `submission_line`, separate diagnostics, and a mode label.
- The browser already saves all exported rows as `case-study-submission.jsonl` and uses the server-provided bytes.
- The two supplied goldens are in `archive/realpage/casestudy/data/sample.jsonl`; 20 focused practice records are in `archive/realpage/casestudy/data/practice.jsonl`.
- No 12-record hold-out file exists in the repository, so a 12-record practice slice is appropriate for rehearsal while the interview card explains how to paste the live 12.

## Technical Decisions
| Decision | Rationale |
|----------|-----------|
| Add a small standard-library rehearsal client | Gives one repeatable command that checks health, counts, exact public shape, byte consistency, ordering, and malformed-record containment. |
| Exercise configured and explicit offline request modes | Configured mode proves missing-key fallback; offline mode proves the deliberate recovery switch. |
| Keep output artifacts under a caller-selected temporary/output directory | Avoids polluting the repository while still proving saved exports parse. |

## Issues Encountered
| Issue | Resolution |
|-------|------------|
| Planning skill resolver lacked execute permission | Used `bash` explicitly and recorded the issue. |

## Resources

- `archive/realpage/casestudy/PLAN-casestudy-bot.md` task C13
- `archive/realpage/casestudy/web.py`
- `archive/realpage/casestudy/tests/test_web.py`
- `archive/realpage/casestudy/README.md`
