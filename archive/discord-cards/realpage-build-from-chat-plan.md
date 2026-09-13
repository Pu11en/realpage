# Building the site from the chat (Eve-style), plus a new useful section

## 🎯 What you asked for
- **1. A new dashboard section that RealPage would actually want**, and the chat AI can read that section's data too.
- **2. Build the site from the online chat.** You type a change, the AI edits the site, pushes it to GitHub, and Railway puts it live right away, with **no testing step**. That's how Eve works.

## 📍 Where things stand right now
- **Railway is running an old version.** Your computer has **34 saved changes that aren't on GitHub yet**, plus today's work: the fixed chat panel and the AI's web research.
- The new chat app (the one with Google sign-in) runs **only on your computer** so far. It isn't on Railway yet.
- ⚠️ **So step one is putting today's version on GitHub and Railway.** Otherwise the online chat would be building on top of the old site.

## 🛠️ How "build from chat" would work (safe version)
- **Two AI modes in the chat:**
  - **Assistant** (everyone): answers questions, researches leads. It can't change anything. Same as today.
  - **Builder** (only you, checked by your Google email): can edit the site's files, save them to GitHub, and Railway puts it live in about 2–3 minutes.
- **Builder can't read web pages.** A sneaky web page could otherwise trick it into changing your site. Research stays in Assistant mode.
- **An "undo last change" command.** Since nothing gets tested first, a bad change is one sentence to roll back ("undo that").
- **Builder only touches the website and dashboard files**, never passwords or keys, and never the data-finding code unless you ask.
- It needs a **GitHub key saved in Railway**, the same way Eve has one.

## 💡 The new section: my pick
- **"At Risk": RealPage buildings that just sold.** New owners often switch software, so these are customers RealPage could lose.
- Today that's **4 buildings (1,071 units)**: Creekside At Legacy (380), The Ludlow (326), Woodlands Of Plano (232), Alta Vista (133).
- Each shows: when it sold, the new owner, its proof link, and a "prep a save call" button that opens the chat.
- The chat can answer "which of our buildings are at risk?" because it reads the same data.
- It's a good **first job for Builder mode**, so you'd see the whole flow work on something real.

## 🧩 Order of work (small steps)
- ⬜ 1. Put today's version on GitHub and Railway, after your OK.
- ⬜ 2. Put the chat app with Google sign-in on Railway.
- ⬜ 3. Add Builder mode: only you, with a GitHub key and an undo command.
- ⬜ 4. From the live chat, ask Builder to add the "At Risk" section. That's the real test.
- ⚠️ Steps 1–3 are several sessions of work, not one.
