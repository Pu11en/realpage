# Front door: serves the site and forwards everything else to the chat app (see Caddyfile).
FROM caddy:2-alpine
COPY Caddyfile /etc/caddy/Caddyfile
COPY . /srv
RUN addgroup -S -g 10001 caddy && \
    adduser -S -D -H -u 10001 -G caddy caddy && \
    rm -f /srv/Caddyfile /srv/Dockerfile && \
    chown -R caddy:caddy /config /data

# Caddy only needs to read the baked site/configuration and write its own
# runtime state under /config and /data.  The configured port defaults to
# 8080, so it does not need root to bind the listener.
USER caddy

CMD ["caddy", "run", "--config", "/etc/caddy/Caddyfile", "--adapter", "caddyfile"]
