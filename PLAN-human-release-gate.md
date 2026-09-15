# CraneSignal: human release gate before GitHub

Written 2026-09-15 after the chat data loop and recruiter evidence loop finished. This is a
preparation loop followed by a real test by Drew. Automated checks can find obvious breakage, but
they cannot mark the product ready to push.

Check: `bash tooling/qa/check-fixes.sh`

Try: `bash tooling/human-test.sh`

Open: http://localhost:8765

## Why it is not ready to push yet

- ✅ The main product checks, chat data work, and recruiter evidence packet are complete in their
  own saved local branches.
- ⚠️ Those pieces are not yet one clean build candidate, so nobody has tested the exact version we
  would publish.
- ⚠️ The usual local preview turns sign in off. It does not prove that a first time person can make
  an account, return to the product, sign out, and sign back in.
- ⚠️ The answer evidence is historical. Seven of twenty saved off topic answers and two of sixty
  saved factual answers did not pass their rubrics.
- ⚠️ Two verified medium severity container hardening findings remain open.
- ⛔ Therefore the current push decision is **no**. This plan creates the real candidate and earns a
  human test. Drew's test, not the loop, makes the final push decision.

## Rules for every task

- Localhost only. Never push, deploy, open a pull request, or change Railway.
- Use existing data and saved evidence. Do not scrape, call a paid model, or run a paid contest.
- User facing language says **CraneSignal**. Do not expose internal product, agent, file, or table
  names.
- Keep the existing site and its visual direction. Make small fixes instead of a redesign.
- Never weaken a check, hide a real failure, or turn a missing measurement into a passing number.
- Add one focused offline regression check for each code change.
- A browser dry run is preparation, not human testing. Never label it as a human pass.
- The release candidate must be reproducible from one local branch with no dependency on deleted
  worktrees or absolute paths.
- AI for the preparation loop: **GPT 5.6 Terra only, with no fallback**.

Run with: `Do the next unticked task in PLAN-human-release-gate.md, then tick it and stop.`

## Preparation tasks

- [x] **H1 Make one clean release candidate.** Bring the completed product and chat data branch
  together with the Under the Hood work in one new local candidate. Preserve unrelated changes in
  other worktrees. Resolve conflicts by keeping the newest tested behavior, then run the Check.
  Commit.

- [x] **H2 Make Under the Hood completely defensible.** Replace weak or stale headline claims with
  the dated recruiter scorecard measurements. Show sample size, method, historical status, and open
  limitations in plain words. Remove absolute machine paths and any dependency on an old worktree.
  Keep the live agent as the primary action and the deeper proof closed by default. Test every shown
  number against the saved evidence. Commit.

- [ ] **H3 Make off topic behavior predictable.** Use the seven saved failures to define the simple
  rule a normal person should see: briefly say the question is outside CraneSignal, then offer a
  useful sales research question. Add offline regression fixtures covering normal small talk,
  unrelated factual questions, and attempts to redirect the agent. Do not call a model. Commit.

- [ ] **H4 Never present an unsupported factual answer as proven.** Use the two saved grounding
  failures to add a deterministic final check: a factual result needs a readable approved source,
  or the answer must plainly say it could not verify the claim. Preserve valid unknown answers and
  add offline regression fixtures. Do not invent citations or call a model. Commit.

- [ ] **H5 Close the two container findings.** Run the chatbot and site containers as an unprivileged
  user while preserving only the file access they need. Re-run the same local security check and
  record the new result. If either finding cannot be safely closed, keep it visible and keep the
  push gate closed. Commit.

- [ ] **H6 Build a safe first time user preview.** Add one command that starts the exact combined
  candidate with sign in enabled, fresh isolated local account storage, clear startup status, and a
  matching stop command. It must not overwrite Drew's existing local chat history or reuse a stale
  account. Add an offline check for the command and its isolation. Commit.

- [ ] **H7 Do a novice browser dry run and fix blockers.** In a fresh browser profile, walk through
  account creation, first use, navigation, chat loading, sources, errors, sign out, and return. Use
  ordinary wording and deliberately take one wrong turn. Record every confusing or broken moment,
  fix release blocking problems, and rerun the Check. Clearly label this as an automated dry run,
  not human testing. Commit.

- [ ] **H8 Hand Drew the real human test.** Leave the combined preview running and produce a short
  observation sheet that asks Drew to use his own words, not copy scripted prompts. Include the
  address, a stop command, the exact push rules below, and a place to record confusion. Do not call
  the candidate ready and do not push. Commit.

## Drew's real test

Use a private browser window with a brand new local account. Act naturally and do not try to help
the product pass.

1. Open the address and, within ten seconds, say what you think CraneSignal does and what you would
   click first.
2. Create an account, enter the product, and find a promising Texas building without instructions.
3. Ask three useful questions in your own wording: which leads deserve attention, what people are
   saying about RealPage, and what RealPage should improve in AI search visibility.
4. Open at least one source, move between the map, leads, a building, AI Visibility, and Under the
   Hood, then recover from one intentional wrong turn.
5. Ask one unrelated question, request private information, and ask the agent to change data. Its
   boundaries should be calm, clear, and useful.
6. Sign out, sign back in, and confirm the product still makes sense on a narrow phone sized window.
7. Record anything that felt slow, unclear, surprising, untrustworthy, or broken, even if you found a
   workaround.

## When I will say it is ready to push

- ✅ Drew can explain the product's purpose in ten seconds without help.
- ✅ A brand new account can sign up, enter, sign out, and return without a dead end.
- ✅ Drew independently completes the core lead, Reddit, and AI Visibility tasks.
- ✅ All three representative answers are useful and every factual claim has a readable source or a
  clear statement that it could not be verified.
- ✅ Off topic, private data, and write requests are handled safely and helpfully.
- ✅ Navigation, loading, empty, and error states tell a normal person what to do next on desktop and
  a phone sized window.
- ✅ Every automated check passes on the exact branch Drew tested, the two container findings are
  closed, and the working tree is clean.
- ✅ Anything Drew reports as confusing or broken is fixed and the affected part is tested again.
- Small purely cosmetic notes may be recorded for later only if they do not confuse, block, or reduce
  trust. Any dead end, wrong answer, unsupported claim, broken sign in, or unclear core action keeps
  the gate closed.

Only after every item above passes will Codex say **ready to push** and ask Drew whether to put that
exact tested commit on GitHub.

## How to try it in 30 seconds after preparation

1. Open the private browser link printed by `bash tooling/human-test.sh` and create a new local account.
2. Use your own words to find one Texas sales lead and ask why it matters. Open one cited source.
3. Sign out and back in. If any step needs an explanation from Codex, the human gate did not pass.
