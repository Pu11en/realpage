# PropertyStack chat app on Railway: Open WebUI + our branding (same files the
# local compose mounts). Build context = repo root. Data lives on a volume at
# /app/backend/data (users, chats).
FROM ghcr.io/open-webui/open-webui:main
COPY chatbot/branding/favicon.png /app/build/favicon.png
COPY chatbot/branding/favicon.png /app/build/static/favicon.png
COPY chatbot/branding/favicon-96x96.png /app/build/static/favicon-96x96.png
COPY chatbot/branding/apple-touch-icon.png /app/build/static/apple-touch-icon.png
COPY chatbot/branding/favicon.svg /app/build/static/favicon.svg
COPY chatbot/branding/logo.png /app/build/static/logo.png
COPY chatbot/branding/logo-transparent.png /app/build/static/splash.png
COPY chatbot/branding/custom.css /app/build/static/custom.css
COPY chatbot/branding/fonts/ /app/build/static/fonts/
COPY chatbot/branding/loader.js /app/build/static/loader.js
# Users see just "CraneSignal", not "CraneSignal (Open WebUI)". Allowed by the Open WebUI
# license while we stay at 50 or fewer users in any 30 days; past that, restore it or buy
# their enterprise license. loader.js does the same in the browser for the local compose.
RUN sed -i "s/^    WEBUI_NAME += ' (Open WebUI)'$/    pass/" /app/backend/open_webui/env.py
# New-account alerts for Discord with name, email and their optional pick
# (chatbot/signup_alerts.py), running next to the app.
COPY chatbot/signup_alerts.py /app/signup_alerts.py
CMD ["bash", "-c", "python3 /app/signup_alerts.py & exec bash start.sh"]
