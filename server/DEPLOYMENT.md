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
PAY_BOT_TOKEN=123456:...
PAYOUT_MINIAPP_SECRET=...
PAYOUT_MINIAPP_BOT_USERNAME=payprotect_bot
PAYOUT_MINIAPP_SHORT_NAME=verify
# Optional, default 300
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
- Caddy production proxy uses `API_DOMAIN=api.example.com`

## Telegram Mini App binding
- `PAYOUT_MINIAPP_SHORT_NAME` must match the Mini App short name configured in BotFather for `PAYOUT_MINIAPP_BOT_USERNAME`.
- The BotFather Mini App URL for that short name must point to the public backend route:
  - `https://<API_DOMAIN>/paybot/miniapp`
- The backend route `/paybot/miniapp` serves the static verification frontend used by the payout Mini App flow.
- If these values diverge, the app may fail with `CONFIG_INVALID` or the Mini App may open the wrong frontend.
