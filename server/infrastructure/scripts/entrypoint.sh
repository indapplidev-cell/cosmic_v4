#!/usr/bin/env bash
set -euo pipefail

jwt_secret="${JWT_SECRET:-}"
reset_secret="${RESET_SECRET:-}"
jwt_len="${#jwt_secret}"
reset_len="${#reset_secret}"
echo "[BOOT] JWT_SECRET_LEN=${jwt_len}"
echo "[BOOT] RESET_SECRET_LEN=${reset_len}"
if [[ "$jwt_len" -le 0 || "$reset_len" -le 0 ]]; then
  echo "ERROR: JWT_SECRET/RESET_SECRET must be non-empty" >&2
  exit 1
fi

echo "Waiting for PostgreSQL (max 30 attempts)..."
python - <<'PY'
import os
import time
from urllib.parse import urlsplit, urlunsplit

from sqlalchemy import create_engine, text

database_url = os.environ.get("DATABASE_URL", "").strip()
if not database_url:
    raise SystemExit("DATABASE_URL is not set")

def mask_url(url: str) -> str:
    parts = urlsplit(url)
    if "@" not in parts.netloc:
        return url
    userinfo, hostinfo = parts.netloc.rsplit("@", 1)
    if ":" in userinfo:
        user = userinfo.split(":", 1)[0]
        userinfo_masked = f"{user}:****"
    else:
        userinfo_masked = userinfo
    return urlunsplit((parts.scheme, f"{userinfo_masked}@{hostinfo}", parts.path, parts.query, parts.fragment))

def classify_error(exc: Exception) -> str:
    message = str(exc).lower()
    if "password authentication failed" in message or "authentication failed" in message:
        return "auth"
    if "could not translate host name" in message or "name or service not known" in message:
        return "host"
    if "timeout" in message or "timed out" in message:
        return "timeout"
    if "connection refused" in message:
        return "connection_refused"
    return "other"

engine = create_engine(database_url, pool_pre_ping=True, future=True)
masked = mask_url(database_url)

last_error = None
for attempt in range(1, 31):
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print(f"PostgreSQL is ready via {masked}")
        break
    except Exception as exc:  # noqa: BLE001
        last_error = exc
        err_type = classify_error(exc)
        print(f"Attempt {attempt}/30 failed ({err_type}): {type(exc).__name__}")
        time.sleep(2)
else:
    print(f"ERROR: cannot connect to PostgreSQL (check DATABASE_URL / POSTGRES_PASSWORD / existing volume). URL={masked}")
    raise SystemExit(1)
PY

python -m alembic -c server/db/migrations/alembic.ini upgrade head

exec uvicorn server.app.api.main:app --host "${API_HOST:-0.0.0.0}" --port "${API_PORT:-8000}"
