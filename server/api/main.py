"""EN: FastAPI entrypoint exposing HTTP endpoints over server services.
RU: Точка входа FastAPI, публикующая HTTP-эндпоинты поверх server-сервисов.
"""

from __future__ import annotations

import os

from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse

from server.api.schemas import (
    DeleteUserRequest,
    GameSessionFinishRequest,
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    TelegramLinkRequest,
    TelegramLinkConfirmRequest,
    TelegramVerifyConfirm,
    TelegramVerifyRequest,
    TelegramVerifySend,
    ProfileGameClearRequest,
    ProfileGameUpdateRequest,
    ProfileUserClearRequest,
    ProfileUserUpdateRequest,
    RegisterRequest,
)
from server.services.auth_service import (
    delete_user,
    get_user_snapshot,
    get_user_snapshot_by_email,
    login_user,
    register_user,
)
from server.services.profile_service import (
    apply_finished_session,
    clear_profile_game_fields,
    clear_profile_user_fields,
    update_profile_game,
    update_profile_user,
)
from server.security.jwt import decode_access_token, extract_bearer_token
from server.services.telegram_service import (
    confirm_link_code,
    confirm_password_reset as confirm_password_reset_telegram,
    request_link_code,
    request_password_reset as request_password_reset_telegram,
)
from server.services.telegram_verify_service import bot_send_code, confirm_verify, request_verify
from server.services.rating_service import get_top_ratings
from server.services.db_schema_guard import get_db_schema_status
from server.services.docs_service import get_doc_content


app = FastAPI(title="Cosmic API")


@app.middleware("http")
async def ensure_db_schema_is_current(request: Request, call_next):
    """EN: Block non-diagnostic requests when DB schema is behind Alembic head.
    RU: Блокировать недиагностические запросы, если схема БД отстаёт от Alembic head.
    """

    path = request.url.path
    if path in {"/healthz", "/meta/compat"}:
        return await call_next(request)

    status = get_db_schema_status()
    if not status.get("ok"):
        return JSONResponse(
            status_code=503,
            content={
                "ok": False,
                "error": "DB_SCHEMA_CHECK_FAILED",
                "details": {
                    "current_revision": status.get("current_revision"),
                    "head_revision": status.get("head_revision"),
                },
            },
        )

    if not status.get("is_current"):
        return JSONResponse(
            status_code=503,
            content={
                "ok": False,
                "error": "DB_SCHEMA_OUTDATED",
                "details": {
                    "current_revision": status.get("current_revision"),
                    "head_revision": status.get("head_revision"),
                },
            },
        )

    return await call_next(request)


def _service_result_to_response(result: dict) -> dict:
    """EN: Return service result as business payload with stable HTTP 200 style.
    RU: Вернуть результат сервиса как business-payload со стабильным стилем HTTP 200.
    """

    if result.get("ok"):
        return result
    return {"ok": False, "error": str(result.get("error", "DB_ERROR"))}


def _resolve_user_id_from_bearer(request: Request) -> int | None:
    """EN: Resolve user_id from Authorization Bearer token payload.
    RU: Извлечь user_id из payload токена Authorization Bearer.
    """

    token = extract_bearer_token(request.headers.get("authorization"))
    if not token:
        return None
    payload = decode_access_token(token)
    if not isinstance(payload, dict):
        return None
    raw_sub = payload.get("sub")
    try:
        return int(raw_sub)
    except Exception:
        return None


@app.get("/healthz")
def healthz() -> dict:
    """EN: Liveness endpoint for local deployment checks.
    RU: Эндпоинт проверки живости для локального развёртывания.
    """

    return {"ok": True}


@app.get("/meta/compat")
def meta_compat() -> dict:
    """EN: Return runtime DB schema compatibility status for client-side readiness checks.
    RU: Вернуть runtime-статус совместимости схемы БД для клиентской проверки готовности.
    """

    status = get_db_schema_status(force_refresh=True)
    return {"ok": bool(status.get("ok")), "db": status}


@app.post("/auth/register")
def auth_register(payload: RegisterRequest) -> dict:
    """EN: Register user using existing auth service.
    RU: Зарегистрировать пользователя через существующий auth-сервис.
    """

    result = register_user(payload.email, payload.psw)
    return _service_result_to_response(result)


@app.post("/auth/login")
def auth_login(payload: LoginRequest) -> dict:
    """EN: Login user using existing auth service.
    RU: Выполнить вход через существующий auth-сервис.
    """

    result = login_user(payload.email, payload.psw)
    return _service_result_to_response(result)


@app.post("/auth/password/reset/request")
def auth_password_reset_request(payload: PasswordResetRequest, request: Request) -> dict:
    """EN: Request one-time password reset code by email with non-enumerating response.
    RU: Запросить одноразовый код восстановления по email с ответом без раскрытия существования аккаунта.
    """

    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    result = request_password_reset_telegram(payload.email, payload.channel, client_ip, user_agent)
    return _service_result_to_response(result)


@app.post("/auth/password/reset/confirm")
def auth_password_reset_confirm(payload: PasswordResetConfirm, request: Request) -> dict:
    """EN: Confirm one-time reset code and set new password hash.
    RU: Подтвердить одноразовый код и установить новый хеш пароля.
    """

    del request
    result = confirm_password_reset_telegram(
        payload.email,
        payload.code,
        payload.new_psw,
    )
    return _service_result_to_response(result)


@app.post("/telegram/link/request")
def telegram_link_request(payload: TelegramLinkRequest, request: Request) -> dict:
    """EN: Create one-time Telegram deep-link start token for authenticated user.
    RU: Создать одноразовый Telegram deep-link start token для авторизованного пользователя.
    """

    auth_user_id = _resolve_user_id_from_bearer(request)
    if auth_user_id is None or auth_user_id <= 0:
        return {"ok": False, "error": "UNAUTHORIZED"}
    if int(auth_user_id) != int(payload.user_id):
        return {"ok": False, "error": "FORBIDDEN"}
    result = request_link_code(payload.user_id)
    return _service_result_to_response(result)


@app.post("/telegram/link/confirm")
def telegram_link_confirm(payload: TelegramLinkConfirmRequest) -> dict:
    """EN: Confirm Telegram link code from bot and bind telegram_user_id to app user.
    RU: Подтвердить Telegram-код от бота и привязать telegram_user_id к пользователю приложения.
    """

    result = confirm_link_code(payload.code, payload.telegram_user_id)
    return _service_result_to_response(result)


@app.post("/telegram/verify/request")
def telegram_verify_request(payload: TelegramVerifyRequest, request: Request) -> dict:
    """EN: Create Telegram verification challenge for provided user_id and return request_id.
    RU: Создать challenge верификации Telegram для переданного user_id и вернуть request_id.
    """

    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    result = request_verify(
        user_id=payload.user_id,
        user_agent=user_agent,
        request_ip=client_ip,
    )
    return _service_result_to_response(result)


@app.post("/telegram/verify/send")
def telegram_verify_send(payload: TelegramVerifySend) -> dict:
    """EN: Accept bot request and send 6-digit code for verification challenge.
    RU: Принять запрос от бота и отправить 6-значный код для challenge верификации.
    """

    expected_secret = os.getenv("BOT_SHARED_SECRET", "").strip()
    provided_secret = str(payload.bot_secret or "").strip()
    if not expected_secret or provided_secret != expected_secret:
        return JSONResponse(status_code=403, content={"ok": False, "error": "FORBIDDEN"})
    result = bot_send_code(
        request_id=payload.request_id,
        telegram_user_id=payload.telegram_user_id,
    )
    return _service_result_to_response(result)


@app.post("/telegram/verify/confirm")
def telegram_verify_confirm(payload: TelegramVerifyConfirm, request: Request) -> dict:
    """EN: Confirm Telegram verification challenge code for provided user_id.
    RU: Подтвердить код challenge верификации Telegram для переданного user_id.
    """

    del request
    result = confirm_verify(user_id=payload.user_id, request_id=payload.request_id, code=payload.code)
    return _service_result_to_response(result)


@app.get("/auth/me")
def auth_me(user_id: int = Query(gt=0)) -> dict:
    """EN: Return current user snapshot by user_id for cache validation/synchronization.
    RU: Вернуть snapshot текущего пользователя по user_id для проверки/синхронизации кэша.
    """

    return _service_result_to_response(get_user_snapshot(user_id))


@app.get("/auth/exists")
def auth_exists(email: str = Query(min_length=3)) -> dict:
    """EN: Resolve user existence by email and return user snapshot when found.
    RU: Проверить существование пользователя по email и вернуть snapshot при наличии.
    """

    return _service_result_to_response(get_user_snapshot_by_email(email))


@app.post("/auth/delete")
def auth_delete(payload: DeleteUserRequest) -> dict:
    """EN: Delete user by id via auth service.
    RU: Удалить пользователя по id через auth-сервис.
    """

    result = delete_user(payload.user_id)
    return _service_result_to_response(result)


@app.post("/profile/user/update")
def profile_user_update(payload: ProfileUserUpdateRequest) -> dict:
    """EN: Update profile_users fields for selected user.
    RU: Обновить поля profile_users для выбранного пользователя.
    """

    result = update_profile_user(
        payload.user_id,
        login=payload.login,
        phone=payload.phone,
        telegram=payload.telegram,
    )
    return _service_result_to_response(result)


@app.post("/profile/user/clear")
def profile_user_clear(payload: ProfileUserClearRequest) -> dict:
    """EN: Reset selected profile_users fields to defaults.
    RU: Сбросить выбранные поля profile_users к значениям по умолчанию.
    """

    result = clear_profile_user_fields(payload.user_id, payload.fields)
    return _service_result_to_response(result)


@app.post("/profile/game/update")
def profile_game_update(payload: ProfileGameUpdateRequest) -> dict:
    """EN: Update profile_games numeric fields for selected user.
    RU: Обновить числовые поля profile_games для выбранного пользователя.
    """

    result = update_profile_game(
        payload.user_id,
        record=payload.record,
        rating=payload.rating,
        balance=payload.balance,
    )
    return _service_result_to_response(result)


@app.post("/profile/game/clear")
def profile_game_clear(payload: ProfileGameClearRequest) -> dict:
    """EN: Reset selected profile_games fields to defaults.
    RU: Сбросить выбранные поля profile_games к значениям по умолчанию.
    """

    result = clear_profile_game_fields(payload.user_id, payload.fields)
    return _service_result_to_response(result)


@app.get("/rating/top")
def rating_top(limit: int = Query(default=100, ge=1, le=100)) -> dict:
    """EN: Return top rating rows via existing rating service.
    RU: Вернуть топ строк рейтинга через существующий rating-сервис.
    """

    items = get_top_ratings(limit=limit)
    return {"ok": True, "items": items}


@app.post("/game/session/finish")
def game_session_finish(payload: GameSessionFinishRequest) -> dict:
    """EN: Accept raw SIS metrics, calculate profile updates on server, and persist results.
    RU: Принять сырые метрики СИС, рассчитать обновления профиля на сервере и сохранить результат.
    """

    result = apply_finished_session(
        payload.user_id,
        {
            "record_sis": payload.record_sis,
            "record_pure": payload.record_pure,
            "sis_sec": payload.sis_sec,
            "chis_sec": payload.chis_sec,
            "attempts": payload.attempts,
            "reward_clicks": payload.reward_clicks,
            "best_life_score": payload.best_life_score,
            "best_game_score": payload.best_game_score,
            "anti_cheat_windows": [item.model_dump() for item in payload.anti_cheat_windows],
        },
    )
    return _service_result_to_response(result)


@app.get("/docs/{doc_key}")
def docs_get(doc_key: str, lang: str = Query(default="ru", min_length=2, max_length=2)) -> dict:
    """EN: Return localized markdown document content from server storage.
    RU: Вернуть локализованное содержимое markdown-документа из серверного хранилища.
    """

    return get_doc_content(doc_key=doc_key, lang=lang)
