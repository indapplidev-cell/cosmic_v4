#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PY'
import re
p = "/opt/cosmic_api/server/.env"
s = open(p, encoding="utf-8").read()

def ln(k: str) -> int:
    m = re.search(rf"^{k}=(.*)$", s, re.M)
    return len(m.group(1)) if m else 0

print("JWT_SECRET_LEN=", ln("JWT_SECRET"))
print("RESET_SECRET_LEN=", ln("RESET_SECRET"))
PY
