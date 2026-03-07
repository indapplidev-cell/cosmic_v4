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

### Вариант B (fallback): Cloudflare Tunnel (без проброса портов)

- В `.env` задайте `CLOUDFLARE_TUNNEL_TOKEN`.
- Запустите профиль tunnel:

```bash
docker compose -f server/infra/docker-compose.yml --env-file server/.env --profile tunnel up -d
```

- Токен берётся в Cloudflare Zero Trust (Tunnel token).
- Этот режим позволяет внешний доступ без публичного IP и без port-forwarding.

## D) Проверка API

```bash
curl https://<PUBLIC_DOMAIN>/healthz
curl -X POST https://<PUBLIC_DOMAIN>/auth/register -H "Content-Type: application/json" -d '{"email":"demo@example.com","psw":"123456"}'
curl -X POST https://<PUBLIC_DOMAIN>/auth/login -H "Content-Type: application/json" -d '{"email":"demo@example.com","psw":"123456"}'
```

## Безопасность (минимум)

- Postgres (`5432`) не публикуется наружу в compose.
- Для публичного доступа используйте только:
  - `443` через Caddy (вариант A), или
  - Cloudflare Tunnel без открытых портов (вариант B).
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
