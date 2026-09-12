# Google sign-in for the PropertyStack chat — Drew's 6 steps (about 5 minutes)

The chat (Open WebUI) uses "Sign in with Google". Google needs to know about our app once.

1. Open https://console.cloud.google.com/ and sign in with kidquick360@gmail.com.
   Top-left project picker → **New project** → name it `PropertyStack` → Create → select it.
2. Left menu → **APIs & Services → OAuth consent screen** (may be called "Google Auth
   Platform → Branding"). App name `PropertyStack`, support email = your Gmail,
   audience **External**, developer contact = your Gmail. Save. No scopes to add.
   If it offers "Publish app", click it (otherwise only test users can sign in).
3. Left menu → **Credentials → Create credentials → OAuth client ID**.
   Application type **Web application**, name `PropertyStack chat`.
4. Under **Authorized redirect URIs** add both lines (the second is for the live site;
   we'll change it in C2 if the Railway URL differs):
   - `http://localhost:3000/oauth/google/callback`
   - `https://propertystack-chat-production.up.railway.app/oauth/google/callback`
   Click Create.
5. Copy the **Client ID** (ends in `.apps.googleusercontent.com`) and **Client secret**.
6. Put them in a file that is never committed: `chatbot/.env.local` (already ignored):
   ```
   GOOGLE_CLIENT_ID=paste-here
   GOOGLE_CLIENT_SECRET=paste-here
   ```
   Then tell the session "Google keys are in place" and it restarts the chat.

After that: the login page shows only a Google button; anyone with a Google account can
sign in and gets their own private chats. Password login is turned off.
