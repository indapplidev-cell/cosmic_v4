# Local Linux Deploy: PostgreSQL + API + HTTPS Access

## A) Установка на Linux

1. Установите Docker Engine и Docker Compose plugin.
2. Добавьте пользователя в группу `docker`:

```bash
sudo usermod -aG docker $USER
newgrp docker
```

## B) Запуск стека

1. Подготовьте env:

```bash
cp server/.env.example server/.env
```

2. Заполните в `server/.env`:
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- `DATABASE_URL` (должен ссылаться на `postgres:5432` внутри compose)
- `PUBLIC_DOMAIN`, `CADDY_EMAIL` (для Caddy HTTPS)

3. Запуск:

```bash
docker compose -f server/infra/docker-compose.yml --env-file server/.env up -d --build
```

4. Проверка:

```bash
curl https://<PUBLIC_DOMAIN>/healthz
```

## C) Доступ из мобильной сети

### Вариант A (основной): Caddy + публичный HTTPS

- В compose уже включен `caddy` (порты `80` и `443`).
- Нужно:
  - домен, указывающий на внешний IP домашней сети;
  - проброс `443` (и обычно `80` для ACME challenge) на Linux-сервер.
- Наружу открыт только reverse proxy. Postgres наружу не публикуется.

## D) Проверка API

```bash
curl https://<PUBLIC_DOMAIN>/healthz
curl -X POST https://<PUBLIC_DOMAIN>/auth/register -H "Content-Type: application/json" -d '{"email":"demo@example.com","psw":"123456"}'
curl -X POST https://<PUBLIC_DOMAIN>/auth/login -H "Content-Type: application/json" -d '{"email":"demo@example.com","psw":"123456"}'
```

## Безопасность (минимум)

- Postgres (`5432`) не публикуется наружу в compose.
- Для публичного доступа используйте только:
  - `443` через Caddy (вариант A).
- Не коммитьте `server/.env`.
- Обязательно используйте сильный `POSTGRES_PASSWORD`.

## Password Storage (EN/RU)

EN:
- `users` stores only `password_hash` (bcrypt via passlib). Plaintext passwords are never stored.
- Input API contract stays the same: request payload uses `{ "email", "psw" }`.
- `BCRYPT_ROUNDS` controls bcrypt cost (default `12`).
- When `BCRYPT_ROUNDS` is increased, hashes are upgraded automatically on successful login (`rehash on login`).
- Optional `PASSWORD_PEPPER` is supported via environment and is not stored in database.

RU:
- В `users` хранится только `password_hash` (bcrypt через passlib). Plaintext-пароли не сохраняются.
- Входной API-контракт не меняется: payload остаётся `{ "email", "psw" }`.
- `BCRYPT_ROUNDS` управляет cost bcrypt (по умолчанию `12`).
- При увеличении `BCRYPT_ROUNDS` хеш обновляется автоматически при успешном логине (`rehash on login`).
- Опциональный `PASSWORD_PEPPER` задаётся через окружение и не хранится в БД.

## Validation/Safety Checks (EN/RU)

EN:
- Run static SQL interpolation check:
  - `python -m server.scripts.sql_injection_check`
- Run payload validation smoke checks:
  - `python -m server.scripts.validation_smoke`

RU:
- Запустить статическую проверку SQL-интерполяции:
  - `python -m server.scripts.sql_injection_check`
- Запустить smoke-проверки валидации payload:
  - `python -m server.scripts.validation_smoke`
## Session Metrics Endpoint (EN/RU)

EN:
- Main gameplay profile update path is now `POST /game/session/finish`.
- Client sends raw session metrics only (`record_sis`, `record_pure`, `sis_sec`, `chis_sec`, `attempts`, `reward_clicks`, `anti_cheat_windows`, etc.).
- Server calculates `record/rating/balance` using server-side formulas and anti-cheat checks, persists to PostgreSQL, and returns:
  - `ok`
  - `cheat`
  - `record`, `rating`, `balance`
  - optional `debug` when `PROFILE_DEBUG=1`.

RU:
- Основной путь обновления игрового профиля теперь `POST /game/session/finish`.
- Клиент отправляет только сырые метрики сессии (`record_sis`, `record_pure`, `sis_sec`, `chis_sec`, `attempts`, `reward_clicks`, `anti_cheat_windows` и т.д.).
- Сервер рассчитывает `record/rating/balance` по серверным формулам и античиту, сохраняет в PostgreSQL и возвращает:
  - `ok`
  - `cheat`
  - `record`, `rating`, `balance`
  - опционально `debug` при `PROFILE_DEBUG=1`.

## Telegram Password Reset (EN/RU)

EN:
- Telegram account linking/confirmation uses the canonical link flow.
- Required env vars in `server/.env`:
  - `TELEGRAM_BOT_TOKEN`
  - `JWT_SECRET` (>=32 chars)
  - `RESET_SECRET`
- Start stack with bot:
  - `docker compose -f server/infra/docker-compose.yml --env-file server/.env up -d --build postgres api bot`
- Flow:
  1) Authorized user calls `POST /telegram/link/request`.
  2) App opens bot deep-link with one-time start token.
  3) Bot confirms latest link and returns 6-digit confirm code through `POST /telegram/link/confirm_latest`.
  4) App calls `POST /telegram/link/confirm` with `{user_id, confirm_code}`.
  5) After Telegram is linked, password reset stays a separate Telegram reset flow.

RU:
- Привязка и подтверждение Telegram работают через канонический link-flow.
- Обязательные переменные в `server/.env`:
  - `TELEGRAM_BOT_TOKEN`
  - `JWT_SECRET` (>=32 символов)
  - `RESET_SECRET`
- Запуск стека с ботом:
  - `docker compose -f server/infra/docker-compose.yml --env-file server/.env up -d --build postgres api bot`
- Поток работы:
  1) Авторизованный пользователь вызывает `POST /telegram/link/request`.
  2) Приложение открывает deep-link бота с одноразовым start-token.
  3) Бот подтверждает последний link-запрос и возвращает 6-значный confirm-code через `POST /telegram/link/confirm_latest`.
  4) Приложение вызывает `POST /telegram/link/confirm` с `{user_id, confirm_code}`.
  5) После привязки Telegram восстановление пароля остаётся отдельным Telegram reset-flow.

## Payout Mini App Verification (EN/RU)

EN:
- Payout identity verification now uses Telegram Mini App only, not legacy `/start + ack` as a security boundary.
- Required env vars in `server/.env`:
  - `PAY_BOT_TOKEN`
  - `PAYOUT_MINIAPP_SECRET`
  - `PAYOUT_MINIAPP_BOT_USERNAME`
  - `PAYOUT_MINIAPP_SHORT_NAME`
- Optional env vars:
  - `PAYOUT_MINIAPP_SESSION_TTL_SEC` (default `300`)
  - `PAYOUT_MINIAPP_AUTH_MAX_AGE_SEC` (default `300`)
- Runtime/API flow:
  1) App calls `POST /payout/miniapp/session/request`.
  2) Backend returns `miniapp_url` in `https://t.me/<bot>/<short_name>?startapp=<token>` format.
  3) Telegram opens the Mini App registered in BotFather under `PAYOUT_MINIAPP_SHORT_NAME`.
  4) That BotFather Mini App configuration must point to the backend route `GET /paybot/miniapp`, which serves the verification frontend.
  5) Mini App posts raw `initData` and `start_param` to `POST /payout/miniapp/session/confirm`.
  6) App polls `POST /payout/miniapp/session/status` until `verified=true`.
- Legacy `/payout/link/*` and paybot `/start` remain only as fallback UX and are not a security boundary for payout.

RU:
- Проверка payout identity теперь использует только Telegram Mini App, а не legacy `/start + ack` как security boundary.
- Обязательные env-переменные в `server/.env`:
  - `PAY_BOT_TOKEN`
  - `PAYOUT_MINIAPP_SECRET`
  - `PAYOUT_MINIAPP_BOT_USERNAME`
  - `PAYOUT_MINIAPP_SHORT_NAME`
- Optional env-переменные:
  - `PAYOUT_MINIAPP_SESSION_TTL_SEC` (default `300`)
  - `PAYOUT_MINIAPP_AUTH_MAX_AGE_SEC` (default `300`)
- Runtime/API flow:
  1) Приложение вызывает `POST /payout/miniapp/session/request`.
  2) Backend возвращает `miniapp_url` в формате `https://t.me/<bot>/<short_name>?startapp=<token>`.
  3) Telegram открывает Mini App, зарегистрированный в BotFather под `PAYOUT_MINIAPP_SHORT_NAME`.
  4) Эта настройка Mini App в BotFather должна указывать на backend-route `GET /paybot/miniapp`, который отдаёт verification frontend.
  5) Mini App отправляет raw `initData` и `start_param` в `POST /payout/miniapp/session/confirm`.
  6) Приложение poll-ит `POST /payout/miniapp/session/status` до `verified=true`.
- Legacy `/payout/link/*` и paybot `/start` остаются только как fallback UX и не являются security boundary для payout.
