#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

bash tools/vps.sh sync-dir server /opt/cosmic_api/server

bash tools/vps.sh cmd "sudo bash -lc '
set -euo pipefail
ENV=/opt/cosmic_api/server/.env
test -f \"\$ENV\"
chmod 600 \"\$ENV\"

if grep -q \"^PAY_BOT_TOKEN=\" \"\$ENV\"; then
  sed -i \"s#^PAY_BOT_TOKEN=.*#PAY_BOT_TOKEN=8700926222:AAHtyLRqVYf1oTPtQK0B23QyJkDr7pmJhcU#\" \"\$ENV\"
else
  printf \"%s\n\" \"PAY_BOT_TOKEN=8700926222:AAHtyLRqVYf1oTPtQK0B23QyJkDr7pmJhcU\" >> \"\$ENV\"
fi

PAY_SECRET=\$(awk -F= \"/^PAY_BOT_SHARED_SECRET=/{print \\\$2}\" \"\$ENV\" | tail -n 1)
if [ -z \"\${PAY_SECRET:-}\" ]; then
  PAY_SECRET=\$(python3 -c \"import secrets; print(secrets.token_urlsafe(48))\")
  sed -i \"/^PAY_BOT_SHARED_SECRET=/d\" \"\$ENV\"
  printf \"%s\n\" \"PAY_BOT_SHARED_SECRET=\$PAY_SECRET\" >> \"\$ENV\"
fi

if grep -q \"^PAY_BOT_API_BASE_URL=\" \"\$ENV\"; then
  sed -i \"s#^PAY_BOT_API_BASE_URL=.*#PAY_BOT_API_BASE_URL=http://api:8000#\" \"\$ENV\"
else
  printf \"%s\n\" \"PAY_BOT_API_BASE_URL=http://api:8000\" >> \"\$ENV\"
fi

awk -F= \"/^PAY_BOT_TOKEN=/{print \\\"PAY_BOT_TOKEN_LEN=\\\", length(\\\$2)} /^PAY_BOT_SHARED_SECRET=/{print \\\"PAY_BOT_SHARED_SECRET_LEN=\\\", length(\\\$2)} /^PAY_BOT_API_BASE_URL=/{print \\\"PAY_BOT_API_BASE_URL_LEN=\\\", length(\\\$2)}\" \"\$ENV\"
'"

bash tools/vps.sh cmd "cd /opt/cosmic_api && sudo docker compose -f server/infra/docker-compose.yml --env-file server/.env exec -T api python -m alembic -c server/alembic.ini upgrade head"

bash tools/vps.sh cmd "cd /opt/cosmic_api && sudo docker compose -f server/infra/docker-compose.yml --env-file server/.env up -d --build api paybot"

bash tools/vps.sh cmd "cd /opt/cosmic_api && sudo docker compose -f server/infra/docker-compose.yml --env-file server/.env ps"

bash tools/vps.sh cmd "python3 - <<'PY'
import json, time, urllib.request, urllib.error
base='http://127.0.0.1:8000'
email=f'payout_smoke_{int(time.time())}@test.com'
psw='Bog3891dan!'
def post(path, data, headers=None):
    body=json.dumps(data).encode('utf-8')
    req=urllib.request.Request(base+path, data=body, method='POST')
    req.add_header('Content-Type','application/json')
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.getcode(), json.loads(r.read().decode('utf-8','replace'))
    except urllib.error.HTTPError as e:
        raw=e.read().decode('utf-8','replace')
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {'raw': raw}
s1,p1=post('/auth/register', {'email': email, 'psw': psw})
print('register_status=', s1, 'ok=', bool(isinstance(p1, dict) and p1.get('ok')))
uid=int((p1 or {}).get('user_id') or 0)
access=str((p1 or {}).get('access_token') or '')
headers={'Authorization': f'Bearer {access}'} if access else {}
s2,p2=post('/payout/link/request', {'user_id': uid}, headers=headers)
print('payout_link_status=', s2, 'ok=', bool(isinstance(p2, dict) and p2.get('ok')), 'has_code=', bool((p2 or {}).get('code')))
PY"

bash tools/vps.sh cmd "cd /opt/cosmic_api && sudo docker compose -f server/infra/docker-compose.yml --env-file server/.env logs --tail 120 api paybot"
