# PropertyStack chatbot -- eve-agent pattern (Hermes + repo-managed profile).
# Build context is the repo root so the data and research folders can be copied.

# Stage 1 gathers the knowledge base (some research folders are empty/absent in git).
# Separate stage so nothing else from the build context lands in the final image.
FROM alpine:3.20 AS kb
COPY . /ctx
RUN mkdir -p /kb/data /kb/research && \
    cp /ctx/propertystack/data/plano-richardson/*.csv /kb/data/ && \
    for d in 01-company 02-products 03-reviews 04-reddit 05-social 06-news 07-competitors 08-voice-of-customer; do \
      mkdir -p /kb/research/$d; if [ -d /ctx/$d ]; then cp -R /ctx/$d/. /kb/research/$d/; fi; \
    done && \
    find /kb/research -type f ! -name '*.md' ! -name '*.txt' ! -name '*.csv' -delete

# Pinned: newer :latest images (s6 main-hermes) start their own gateway and skip our CMD.
FROM nousresearch/hermes-agent:v2026.7.20

USER root
WORKDIR /app

COPY chatbot/hermes-profile /opt/hermes-profile
COPY chatbot/docker/start-hermes.sh /opt/hermes-start/start-hermes.sh
COPY chatbot/proxy.py /opt/chatbot/proxy.py

# Knowledge base, baked in read-only.
COPY --from=kb /kb /opt/propertystack

RUN chmod +x /opt/hermes-start/start-hermes.sh && \
    chmod -R a-w /opt/propertystack && \
    chown -R hermes:hermes /app /opt/hermes-profile /opt/hermes-start /opt/chatbot

# Keep the base image ENTRYPOINT (s6 init, drops root to the hermes user).
CMD ["bash", "/opt/hermes-start/start-hermes.sh"]
