# PropertyStack: where everything stands (Sep 12)

## ✅ Everything is saved and on GitHub
- All of today's work is saved **and pushed to GitHub**. Nothing of mine is left only on your computer.
- The live site runs that same version: **https://propertystack-production.up.railway.app**
- ⚠️ One file has a small unsaved edit that isn't mine (a test script, changed by your other PropertyStack session). I left it alone.

## 🖥️ Your localhost setup: one command, no sign-in
- In the terminal, from the realpage folder, run: **bash tooling/dev.sh**
- Then open **http://localhost:8765** and click **Ask**. **No login, no Google.** The chat opens right inside the dashboard.
- Run the same command again after any change. It rebuilds, and it always serves the **current** code. (Before, an old copy of the site was secretly running on that address, which caused some of the weird local behavior.)
- To stop everything: **bash tooling/dev.sh stop**
- Your local chats in no-login mode are kept separately from the earlier Google-login test chats, which are untouched.
- ✅ Tested: no sign-in box, and the question "How many buildings run Yardi?" gets "66", with a source.

## 🔧 Bugs found and fixed today
- ✅ **The AI printed its lookup steps as gibberish** instead of answering, both locally and live. Two causes: an old AI engine version, and the data tool crashing on start-up on the live server. Both fixed, and **live now answers "66 buildings run Yardi" with a source.**
- ✅ **Google sign-in** works live, and you're the admin.
- ✅ **The sign-in popup now closes by itself** and the chat appears in the panel.
- ✅ Docker got stuck after a crash. It was fixed by restarting Linux, and it's running again.

## 🌐 What's live
- One address for the site, the Ask panel, the chat app and the AI.
- Anyone with a Google account can sign in, capped at $3 a day each. Users and chats are saved permanently.
- The AI can research a building online (web lookups) and write a call-prep sheet.
- There's a privacy page, and Google's sign-in is set to allow everyone.

## ⬜ Still open (nothing started)
- **Builder mode:** change the site and the bot from the chat, and it goes live right away.
- **"At Risk" section:** the 4 buildings running RealPage that just sold (1,071 units).
- **One Railway click from you**, only needed for Builder mode: connect the propertystack-chat service to GitHub (Settings → Source → Pu11en/realpage, branch main).

## 🐞 Your loop from here
- Run **bash tooling/dev.sh**, then click around **http://localhost:8765**. When you find a bug, tell me what you clicked and what you saw.
- I fix it on localhost, you check it, and then I push. Railway then updates by itself in a few minutes.
