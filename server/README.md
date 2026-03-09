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
- Password reset delivery uses Telegram bot outbox (no SMTP required).
- Required env vars in `server/.env`:
  - `TELEGRAM_BOT_TOKEN`
  - `JWT_SECRET` (>=32 chars)
  - `RESET_SECRET`
  - `RESET_TOKEN_TTL_MIN`, `RESET_THROTTLE_SEC`, `RESET_MAX_ATTEMPTS`
- Start stack with bot:
  - `docker compose -f server/infra/docker-compose.yml --env-file server/.env up -d --build postgres api bot`
- Flow:
  1) Authorized user calls `POST /telegram/verify/request` and gets `request_id`.
  2) User sends `/verify <request_id>` to bot.
  3) Bot sends a 6-digit verification code to Telegram.
  4) App calls `POST /telegram/verify/confirm` with `{request_id, code}`.
  5) After verification, `POST /auth/password/reset/request` with `{email, channel:"telegram"}` can queue reset code.

RU:
- Доставка кода восстановления пароля работает через Telegram-бота и outbox (SMTP не нужен).
- Обязательные переменные в `server/.env`:
  - `TELEGRAM_BOT_TOKEN`
  - `JWT_SECRET` (>=32 символов)
  - `RESET_SECRET`
  - `RESET_TOKEN_TTL_MIN`, `RESET_THROTTLE_SEC`, `RESET_MAX_ATTEMPTS`
- Запуск стека с ботом:
  - `docker compose -f server/infra/docker-compose.yml --env-file server/.env up -d --build postgres api bot`
- Поток работы:
  1) Авторизованный пользователь вызывает `POST /telegram/verify/request` и получает `request_id`.
  2) Пользователь отправляет боту `/verify <request_id>`.
  3) Бот присылает 6-значный код подтверждения в Telegram.
  4) Приложение вызывает `POST /telegram/verify/confirm` с `{request_id, code}`.
  5) После подтверждения `POST /auth/password/reset/request` с `{email, channel:"telegram"}` ставит код восстановления в Telegram outbox.
