# Letting the chat AI fill in new areas: what Eve does, and what fits here

## 🔍 How Eve does it on Railway
- Eve runs on Railway with **full computer powers**: it can run commands, edit files, and holds a **GitHub key** that lets it push changes.
- When someone asks it to change something, it **edits the files, saves them to GitHub, and Railway rebuilds and restarts it automatically.** It's never allowed to restart itself directly, only through GitHub.
- It keeps a **permanent storage drive** on Railway, so its memory and files survive restarts.
- **Why that was safe for Eve:** only you talk to it (through Telegram). It's your personal assistant.

## ⚠️ Why we shouldn't copy it exactly
- The PropertyStack chat is for **a whole sales team** signing in with Google, not just you.
- If it could push code, **any salesperson could accidentally break the dashboard.**
- Now that it reads web pages, a sneaky page could also try to **trick it into doing things.** Letting it touch code or GitHub makes that dangerous.
- Also, finding a new area costs **Jina lookups (a few hundred per area)**, so not everyone should be able to start one.
- **Good news: new areas are data, not code.** We don't need the AI to change code at all, just to run the skills and save the results.

## 🧰 What's ready today
- ✅ The 7 finder skills work end to end. Plano + Richardson (204 buildings) took **about 6–8 minutes** in total.
- ✅ **Any city in Collin County works right away** with no new code: Frisco (the Collin side), McKinney, Allen, Wylie, Murphy, Prosper and others. You just pick the cities.
- ⚠️ **Other counties need new work per county.** Dallas County has no easy data feed. We got partway using its bulk download files, then paused it.
- ⚠️ **Today the data is locked inside the chat and the website** when they're built. A new area only shows up after a rebuild.
- ⚠️ **The dashboard is hard-wired to "Plano-Richardson"** and has no area picker.

## 🗺️ The plan I'd build (small steps, on your computer first)
- ⬜ **1. Data lives on a storage drive, not baked in.** The chat and the dashboard both read areas from one shared folder, so new areas show up without a rebuild.
- ⬜ **2. Area picker on the dashboard.** A dropdown: "Plano-Richardson", "McKinney-Allen", and so on.
- ⬜ **3. "Add an area" in the chat, for you only.** You type "add McKinney and Allen" and it runs the skills in the background, about 10 minutes. Everyone else gets "ask your admin."
- ⬜ **4. Progress and a finish message.** "Found 180 buildings, 41 leads." Then the new area appears in the picker.
- ⬜ **5. Safety.** Only the finder skills can run (no other commands), one area at a time, a daily limit, and it never pushes to GitHub.
- ⬜ **6. Test it on your computer** by adding one real Collin city. Then you try it, and only after your OK does it go to Railway.

## 🧪 How you'd try it (30 seconds)
- In the chat, type **"add Allen"**. About 10 minutes later, Allen shows up in the dashboard's area dropdown.
- Pick Allen and check the lead list has real buildings with proof links.
- Sign in as a non-admin and type "add Wylie". It should politely refuse.
