FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY server /app/server
COPY engine /app/engine

RUN pip install --no-cache-dir -r /app/server/requirements.txt
RUN chmod +x /app/server/infra/entrypoint.sh
