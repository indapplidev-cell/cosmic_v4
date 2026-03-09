#!/usr/bin/env bash
set -euo pipefail
awk -F= '
/^SMTP_HOST=|^SMTP_PORT=|^SMTP_USER=|^SMTP_FROM=|^SMTP_TLS=/{print}
/^SMTP_PASSWORD=/{print "SMTP_PASSWORD=****"}
' /opt/cosmic_api/server/.env || true
python3 - <<'PY'
import re
s=open('/opt/cosmic_api/server/.env', encoding='utf-8').read()
def ln(k):
    m=re.search(rf'^{k}=(.*)$', s, re.M)
    return len(m.group(1)) if m else 0
print('SMTP_HOST_LEN=', ln('SMTP_HOST'))
print('SMTP_PORT_LEN=', ln('SMTP_PORT'))
print('SMTP_USER_LEN=', ln('SMTP_USER'))
print('SMTP_PASSWORD_LEN=', ln('SMTP_PASSWORD'))
print('SMTP_FROM_LEN=', ln('SMTP_FROM'))
print('SMTP_TLS_LEN=', ln('SMTP_TLS'))
PY
