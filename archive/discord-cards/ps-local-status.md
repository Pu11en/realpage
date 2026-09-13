# Where PropertyStack is right now — and why the AI isn't answering

## ✅ The good news: the AI brain works

- I called the chat service directly on your machine and asked "Which vendor runs the most buildings?"
- It answered correctly in about 4 seconds: **Yardi, 66 of the 204 buildings**, with a citation.
- The chat app (Open WebUI) also answers correctly when I call it directly with a valid login.
- So the model, the data, and the answer quality are fine. Nothing is broken in the bot itself.

## ⏳ What's actually broken: the panel can't hold a login

- Your site runs on **localhost:8765** and the chat app runs on **localhost:3000** — two different addresses.
- Open WebUI keeps your login token in browser storage tied to **localhost:3000**.
- The panel is a **window from one address showing a page from another address**. Modern browsers deliberately isolate that window, so it never sees the login.
- Result: inside the panel the chat app keeps showing its own sign-in page, so the panel looks dead even though the AI works.
- I proved this by loading the panel in a real browser: the framed chat app redirects to its sign-in page, and the page can't reach into it to fix it (the browser blocks it outright).

## ✅ What IS working locally today (v6)

- A slide-out chat panel exists on all 5 dashboard pages, docked beside the data.
- The panel decides for itself whether you're signed in and shows a real "Sign in with Google" card.
- The model picker is gone, and the panel no longer covers the dashboard — your three fixes are in.
- All of this is committed on the v6 branch and the site is being served at **localhost:8765** from that branch.

## ⚠️ The one real decision left

- The panel-inside-a-window design only works if the site and the chat app share **one address**.
- That is exactly the choice your own plan already flagged for the live site (C2): one address with the chat under it, or one address with a proxy in front.
- Doing it now fixes the panel both locally and live, in one move — and it is the only way the framed panel can ever keep you signed in.

## ⬜ What I have not done yet

- I have not changed any code, restarted anything, or pushed anything.
- I have not re-entered Google keys (the keys file `chatbot/.env.local` was said to be missing; it now has values, but I did not verify they are the real ones).
- I have not yet written your acceptance test as a runnable check.

## ⬜ Your test, as it stands today

- The closest thing to "your test" that exists is a saved answer sheet: **10 questions with answers you already approved on Sep 10**.
- It is not yet wired up as a one-command pass/fail check — right now it is a document, not a test.
- Turning it into a check that runs locally and prints PASS/FAIL for all 10 answers is a small, well-defined piece of work.
