# AGENTS.md — CraneSignal project notes

## Workflow

CraneSignal is a general-purpose lead finder for anyone selling to apartment owners.
The system detects which property-management software every building runs,
flags buildings most likely to switch (recent sale, new owner, under construction),
and provides sources for every claim.

Development follows the pattern: local testing and iteration before any merge to main,
and main is deployed to production only after Drew approves.

## Archived work

AI Visibility research and the site library's early vendor-focused phase are archived in
`archive/realpage/`. See the plans there if needed for historical context.
