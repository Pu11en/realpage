# Chatbot image (Hermes agent + proxy.py + baked-in data); runs on Railway and in the local compose.
# Build context is the repo root so the data and research folders can be copied.

# Stage 1 gathers the knowledge base (some research folders are empty/absent in git).
# Separate stage so nothing else from the build context lands in the final image.
FROM alpine:3.20 AS kb
COPY . /ctx
RUN mkdir -p /kb/data /kb/research && \
    cp /ctx/propertystack/data/plano-richardson/*.csv /kb/data/ && \
    ( [ -d /ctx/propertystack/data/dallas-parked/kb ] && cp /ctx/propertystack/data/dallas-parked/kb/*.csv /kb/data/ || true ) && \
    ( [ -d /ctx/propertystack/data/map-summary/kb ] && cp /ctx/propertystack/data/map-summary/kb/*.csv /kb/data/ || true ) && \
    ( [ -d /ctx/propertystack/data/software-share/kb ] && cp /ctx/propertystack/data/software-share/kb/*.csv /kb/data/ || true ) && \
    ( [ -d /ctx/propertystack/data/building-extras/kb ] && cp /ctx/propertystack/data/building-extras/kb/*.csv /kb/data/ || true ) && \
    ( [ -d /ctx/propertystack/data/cranesignal-build/kb ] && cp /ctx/propertystack/data/cranesignal-build/kb/*.csv /kb/data/ || true ) && \
    ( [ -d /ctx/propertystack/data/ai-visibility/kb ] && cp /ctx/propertystack/data/ai-visibility/kb/*.csv /kb/data/ || true ) && \
    ( first=1; for f in /ctx/propertystack/data/*/chat-leads.csv; do \
      [ -e "$f" ] || continue; case "$f" in */_*/*) continue;; esac; \
      if [ "$first" = 1 ]; then head -1 "$f" > /kb/data/state-leads.csv; first=0; fi; \
      tail -n +2 "$f" >> /kb/data/state-leads.csv; \
    done ) && \
    ( [ -e /ctx/propertystack/data/street-talk/street_talk.csv ] && \
      cp /ctx/propertystack/data/street-talk/street_talk.csv /kb/data/street-talk.csv || true ) && \
    for d in 01-company 02-products 03-reviews 04-reddit 05-social 06-news 07-competitors 08-voice-of-customer 09-ai-visibility; do \
      mkdir -p /kb/research/$d; if [ -d /ctx/$d ]; then cp -R /ctx/$d/. /kb/research/$d/; fi; \
    done && \
    find /kb/research -type f ! -name '*.md' ! -name '*.txt' ! -name '*.csv' -delete

# Pinned to a tested release (older ones leak DeepSeek tool calls as text).
FROM nousresearch/hermes-agent:v2026.9.11

USER root
WORKDIR /app

COPY chatbot/hermes-profile /opt/hermes-profile
COPY chatbot/docker/start-hermes.sh /opt/hermes-start/start-hermes.sh
COPY chatbot/proxy.py chatbot/autobold.py chatbot/linkfix.py /opt/chatbot/

# Knowledge base, baked in read-only.
COPY --from=kb /kb /opt/propertystack

RUN chmod +x /opt/hermes-start/start-hermes.sh && \
    chmod -R a-w /opt/propertystack && \
    chown -R hermes:hermes /app /opt/hermes-profile /opt/hermes-start /opt/chatbot

# The base entrypoint keeps its tiny, setuid bootstrap for s6, but all of this
# image's application processes now start as the dedicated unprivileged user.
# /opt/data is already owned by hermes in the base image and is the only
# mutable application location; the baked knowledge base stays read-only.
USER hermes

# Keep the base image ENTRYPOINT (s6 init preserves the unprivileged user).
CMD ["bash", "/opt/hermes-start/start-hermes.sh"]
