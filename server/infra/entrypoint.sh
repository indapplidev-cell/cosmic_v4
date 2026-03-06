#!/usr/bin/env bash
set -euo pipefail

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

python -m alembic -c server/alembic.ini upgrade head

exec uvicorn server.api.main:app --host "${API_HOST:-0.0.0.0}" --port "${API_PORT:-8000}"
