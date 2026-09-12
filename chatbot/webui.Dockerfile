# PropertyStack chat app on Railway: Open WebUI + our branding (same files the
# local compose mounts). Build context = repo root. Data lives on a volume at
# /app/backend/data (users, chats).
FROM ghcr.io/open-webui/open-webui:main
COPY chatbot/branding/favicon.png /app/build/favicon.png
COPY chatbot/branding/favicon.png /app/build/static/favicon.png
COPY chatbot/branding/favicon-96x96.png /app/build/static/favicon-96x96.png
COPY chatbot/branding/favicon.svg /app/build/static/favicon.svg
COPY chatbot/branding/logo.png /app/build/static/logo.png
COPY chatbot/branding/logo-transparent.png /app/build/static/splash.png
COPY chatbot/branding/custom.css /app/build/static/custom.css
