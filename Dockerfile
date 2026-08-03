FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && \
    apt-get install -y --no-install-recommends gosu && \
    rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 1000 bot && \
    useradd --uid 1000 --gid bot --no-create-home --shell /usr/sbin/nologin bot && \
    mkdir -p /app/data && chown -R bot:bot /app

COPY bot/ ./bot/
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["python", "-m", "bot.main"]
