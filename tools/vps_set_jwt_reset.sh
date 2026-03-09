#!/usr/bin/env bash
set -euo pipefail

ENV=/opt/cosmic_api/server/.env
test -f "$ENV"
chmod 600 "$ENV"

gen() {
python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(64))
PY
}

JWT="$(gen)"
RESET="$(gen)"

sed -i '/^JWT_SECRET=/d;/^RESET_SECRET=/d' "$ENV"
printf '%s\n' "JWT_SECRET=$JWT" >> "$ENV"
printf '%s\n' "RESET_SECRET=$RESET" >> "$ENV"
