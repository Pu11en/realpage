# How to test the new chat (step by step)

**Good news: it's already running on your computer right now.** You only need a web browser.

## Step 1 ⏳ Open the site
- On this computer, open Chrome (or any browser).
- Type **localhost:8765** in the address bar and press Enter.
- You'll see the PropertyStack site. **No sign-in needed.**
- Click the **Ask** button. A chat opens in a panel on the right side.

## Step 2 ⏳ Check the panel (10 seconds)
- ✅ The chat stays inside the side panel.
- ✅ There is **no** "Open in full page" link anywhere.
- Click the green **Past chats** button: a list of your old chats covers the panel.
- Click **Back to chat** (top right): you're back in the chat.
- ⚠️ If any of these is wrong, tell me what you saw.

## Step 3 ⏳ Ask one question (20 seconds)
- Type: **Which buildings sold recently?** and press Enter.
- ✅ The answer is short (about 40 words, a few lines).
- ✅ It has **3 bullets** with bold bits (names, numbers, dates).
- ✅ It ends with a bold **Next:** line and a **Sources:** line.
- ✅ No weird codes (like "SWDNL") and no file names (like ".csv").

## Step 4 ⏳ Try the deep dive memory (30 seconds)
- Close the panel and scroll to the **Early Leads** list on the site.
- Click **Deep dive** on any row. Wait for the answer (can take up to a minute).
- Click **Deep dive** on the **same row** again.
- ✅ This time it's instant and says **"Saved deep dive from <date>. Press ↻ to redo it."**
- Press the **↻** button under the answer, then pick **Try Again**.
- ✅ It researches again from scratch (slow again) and saves the new version.

## If the page won't open
- If **localhost:8765** shows "can't reach this page", the site stopped.
- Open the Ubuntu terminal and paste this, then press Enter:
  **cd ~/.local/state/ccdb/gowork/local-test-plan-chat-finish-20260913-185338 && bash tooling/dev.sh**
- Wait until it stops printing (about 1–2 minutes), then go back to Step 1.
- Or just tell me "it won't open" and I'll start it for you.

## When you're done
- All good? Say **"it's good"** and I'll ask if you want it put on GitHub.
- Something off? Just describe it in your own words, e.g. "no Past chats button".
