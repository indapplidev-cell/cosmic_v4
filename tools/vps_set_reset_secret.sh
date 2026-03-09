#!/usr/bin/env bash
set -euo pipefail
ENV=/opt/cosmic_api/server/.env
touch "$ENV"
if ! grep -q '^RESET_SECRET=.' "$ENV"; then
  val="$(python3 -c "import secrets; print(secrets.token_urlsafe(48))")"
  sed -i '/^RESET_SECRET=/d' "$ENV"
  printf 'RESET_SECRET=%s
' "$val" >> "$ENV"
fi
chmod 600 "$ENV"
