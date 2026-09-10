# PropertyStack

The software stack behind every apartment property in an area. Outside-in:
public data only.

## Layout
- `skills/<name>/` — one folder per skill: `SKILL.md` (instructions + contract) and `run.py`
- `lib/` — shared helpers: `jina.py` (Reader/Search), `runlog.py` (run logs), `paths.py`
- `data/<area>/` — numbered outputs, one file per skill
- `runs/` — one JSON log per skill run (feeds the Under the Hood page)
- `evals/` — golden sets + eval configs (added after the skills)
- `.claude/skills` → `skills/` (so Claude Code sessions discover them)

## Pipeline (each skill reads only the files before it)
| # | Skill | Reads | Writes |
|---|---|---|---|
| 1 | find-apartments | county API | `1-apartments.csv` |
| 2 | find-website | 1 | `2-websites.csv` |
| 3 | detect-software | 2 | `3-software.csv` |
| 4 | build-table | 1, 2, 3 | `master.csv` (pages 2, 3, 4) |
| 5 | find-sales | 1 + county API | `5-sales.csv` |
| 6 | find-upcoming | public sources | `6-upcoming.csv` |
| 7 | score-leads | master, 5, 6 | `leads.csv` (page 1) |

Run any skill: `python3 skills/<name>/run.py --area plano-richardson`
Keys: `JINA_API_KEY` in a gitignored `.env`. Never commit keys.
