#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
import re
p='/opt/cosmic_api/server/.env'
s=open(p,encoding='utf-8').read()
m=re.search(r'^RESET_SECRET=(.*)$', s, re.M)
print('RESET_SECRET=****' if m else 'RESET_SECRET=missing')
print('RESET_SECRET_LEN=', len(m.group(1)) if m else 0)
PY
