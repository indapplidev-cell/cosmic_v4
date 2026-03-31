# Backend Deployment

## Dev
- Copy `server/.env.example` to `server/.env`
- Fill local dev values
- Run dev stack:
```bash
docker compose -f server/infra/docker-compose.yml --env-file server/.env up --build
```

## Production VPS/VDS
- Put production secrets only into `server/.env` on the server
- Set managed PostgreSQL in `DATABASE_URL`, for example:
```env
DATABASE_URL=postgresql+psycopg://user:pass@db.example.com:5432/game_galaxy?sslmode=require
JWT_SECRET=...
RESET_SECRET=...
BOT_SHARED_SECRET=...
PAY_BOT_SHARED_SECRET=...
PAY_BOT_TOKEN=8689634707:AAHNixwuoFTD1nP0My8n57n8_sbMkrMdQqs
PAYOUT_MINIAPP_SECRET=...
PAYOUT_MINIAPP_BOT_USERNAME=escape2mars_bot
ESCAPE2MARS_MINIAPP_SHORT_NAME=escape2mars
ESCAPE2MARS_MINIAPP_URL=https://tg.escape2mars.space/main/miniapp
# Optional, shared Telegram hub session TTL, default 300
PAYOUT_MINIAPP_SESSION_TTL_SEC=300
# Optional, default 300
PAYOUT_MINIAPP_AUTH_MAX_AGE_SEC=300
API_DOMAIN=api.example.com
```
- Run production backend stack without local postgres container:
```bash
docker compose -f server/infra/docker-compose.prod.yml --env-file server/.env up --build -d
```

## Alembic
- Apply migrations against the same `DATABASE_URL`:
```bash
cd server
alembic upgrade head
```

## API domain
- Client production config must receive:
```env
APP_ENV=production
API_BASE_URL=https://api.example.com
```
- Existing repo includes a Caddy example for generic API proxying, but Mini App production deployment for Telegram should be proxied by `nginx` on the dedicated subdomain `tg.escape2mars.space`.
- В репозитории есть пример Caddy для общего API-proxy, но production-деплой Telegram Mini App нужно проксировать через `nginx` на выделенном поддомене `tg.escape2mars.space`.

## Telegram Mini App binding
- Configure BotFather for `@escape2mars_bot` with:
  - `Main App URL = https://tg.escape2mars.space/main/miniapp`
  - `Direct Link short name = escape2mars`
- Expected direct launch link format:
  - `https://t.me/escape2mars_bot/escape2mars?startapp=<opaque_token>`
- Preferred reverse-proxy binding for the Mini App subdomain:
  - `server_name tg.escape2mars.space;`
  - `proxy_pass http://127.0.0.1:8000;`
  - backend continues serving `/main/miniapp`, `/privacy`, `/terms`, `/support`, and `/telegram/hub/*`
- Canonical shared hub flow:
  - app entry: `POST /telegram/hub/session/request`
  - Telegram hub init: `POST /telegram/hub/init`
  - verify action: `POST /telegram/hub/action/verify`
  - reset action: `POST /telegram/hub/action/reset`
  - payout context: `POST /telegram/hub/action/payout/context`
  - payout confirm: `POST /telegram/hub/action/payout/confirm`
- App-to-Telegram transition proof is validated once on hub init, but each sensitive action remains server-checked separately.
- The backend must expose:
  - `/main/miniapp`
  - `/privacy`
  - `/terms`
  - `/support`
- `@pswprotect_bot` remains dedicated to verify/reset flow and should not be repointed to the payout Mini App.
