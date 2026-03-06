#!/usr/bin/env bash
set -euo pipefail

compose_cmd=(docker compose -f server/infra/docker-compose.yml --env-file server/.env)

echo "[1/4] Stopping stack and removing volumes..."
"${compose_cmd[@]}" down -v --remove-orphans

echo "[2/4] Rebuilding and starting stack..."
"${compose_cmd[@]}" up -d --build

echo "[3/4] Waiting for API healthz..."
ok=0
for i in $(seq 1 60); do
  if resp="$(curl -sS http://localhost:8000/healthz 2>/dev/null)" && [[ "$resp" == *'"ok":true'* || "$resp" == *'"ok": true'* ]]; then
    echo "API is healthy: $resp"
    ok=1
    break
  fi
  sleep 2
done

if [[ "$ok" -ne 1 ]]; then
  echo "ERROR: API healthcheck failed after reset."
  echo "---- API logs (tail 200) ----"
  "${compose_cmd[@]}" logs --tail 200 api || true
  echo "---- PostgreSQL logs (tail 200) ----"
  "${compose_cmd[@]}" logs --tail 200 postgres || true
  exit 1
fi

echo "[4/4] Done."
