FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 10001 casestudy \
    && useradd --system --uid 10001 --gid casestudy --home-dir /nonexistent --shell /usr/sbin/nologin casestudy

WORKDIR /app
COPY casestudy/requirements.txt /app/casestudy/requirements.txt
RUN pip install --no-cache-dir -r /app/casestudy/requirements.txt
COPY casestudy /app/casestudy
RUN chown -R casestudy:casestudy /app

USER casestudy
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=2)" || exit 1

CMD ["python", "-m", "casestudy.web", "--host", "0.0.0.0"]
