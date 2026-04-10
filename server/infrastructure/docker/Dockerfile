FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY server /app/server
COPY shared /app/shared

RUN pip install --no-cache-dir -r /app/server/requirements.txt
RUN find /app/server/infrastructure/scripts -maxdepth 1 -name "*.sh" -exec sed -i 's/\r$//' {} \; \
    && find /app/server/infrastructure/scripts -maxdepth 1 -name "*.sh" -exec chmod +x {} \;
