# PropertyStack is live on Railway: one step from you, then test sign-in

## ✅ What's live now
- **One address for everything:** https://propertystack-production.up.railway.app
- The site, the Ask panel, and the chat app with Google sign-in all run from that one address. That's what lets sign-in work inside the panel, including on iPhone.
- The AI behind the chat is live too, **with today's web research ability** (the Jina lookups).
- The chat app **saves users and chats on a permanent drive**, so they survive restarts and updates.
- Everything from your computer is now on GitHub, as you approved.
### Problems I hit and fixed along the way
- The AI's base software changed upstream and started ignoring our start-up steps. Fixed, and pinned to a known-good version so it can't surprise us again.
- A networking setting I added today blocked Railway's health check. Fixed.

## ⚠️ The one thing only you can do (about 1 minute)
- Google only lets sign-in come back to addresses you've approved. Right now it refuses the live address with **"Error 400: redirect_uri_mismatch."**
- Steps:
  - Go to **console.cloud.google.com**, then **APIs & Services**, then **Credentials**.
  - Open the **OAuth client** you made for PropertyStack (the same one the local version uses).
  - Under **Authorized redirect URIs**, add exactly: **https://propertystack-production.up.railway.app/oauth/google/callback**
  - Under **Authorized JavaScript origins**, add: **https://propertystack-production.up.railway.app**
  - Click **Save**. Google says it can take a few minutes to kick in.

## 🧪 Your test (after the Google step)
- ⚠️ **Sign in first, before anyone else.** The first person to sign in becomes the admin.
- Open the site and click the green **Ask** button, then **Continue with Google**.
- Ask **"Which vendor runs the most buildings?"** You should see a cited answer (Yardi, 66).
- Ask **"Prep me to cold call Vantage At Spring Creek"**. It takes about 1.5 minutes and includes web research.
- Reload the page and check your chat is still there. Then try it on your phone.

## 🔍 What I check after you test
- I have a one-command check that looks at the live site and reports:
  - every page loads, and the chat and AI are healthy;
  - whether Google accepts the sign-in address;
  - **every user in the database**: email, role, when they joined, when they were last active, and how many chats;
  - **recent errors in all three services' logs.**
- Right now: pages ✅, chat ✅, AI ✅, **0 users** (nobody has signed in yet), **0 real errors.** The one log warning is a harmless database note from the chat app.

## ⬜ Still to do after your test
- **Builder mode:** you change the site and the bot from the chat, and it goes live right away.
- One Railway click for that: the chat app is connected to GitHub for the site and AI, but I had to upload the chat app itself directly, because Railway only lets you (not me) connect a new service to GitHub. It rarely changes, so this can wait.
- ⚠️ **Right now any Google account can sign in and use the chat**, capped at $3 a day per person. We can switch it to "you approve each new user" whenever you want.
