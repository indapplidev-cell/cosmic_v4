"""EN: FastAPI entrypoint exposing HTTP endpoints over server services.
RU: Точка входа FastAPI, публикующая HTTP-эндпоинты поверх server-сервисов.
"""

from __future__ import annotations

import os
import logging

from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from server.api.schemas import (
    AdsConfigRequest,
    AdsConfigResponse,
    AdsEventRequest,
    PayoutLinkAckRequest,
    PayoutLinkRequest,
    PayoutLinkStatusRequest,
    BotResetIssueRequest,
    DeleteUserRequest,
    GameSessionFinishRequest,
    LoginRequest,
    LogoutRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshRequest,
    TelegramLinkRequest,
    TelegramLinkConfirmByCodeRequest,
    TelegramLinkConfirmLatestRequest,
    TelegramLinkConfirmRequest,
    TelegramLinkStatusRequest,
    ProfileGameClearRequest,
    ProfileGameUpdateRequest,
    ProfileUserClearRequest,
    ProfileUserUpdateRequest,
    RegisterRequest,
)
from server.services.ads_service import get_ads_config, log_ads_event
from server.services.payout_service import ack_payout_link_code, get_last_payout_link_status, request_payout_link_code
from server.services.auth_service import (
    delete_user,
    get_user_snapshot,
    get_user_snapshot_by_email,
    login_user,
    logout_user,
    refresh_auth,
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
    confirm_link_by_code,
    confirm_link,
    confirm_link_latest,
    get_last_link_status,
    confirm_password_reset as confirm_password_reset_telegram,
    issue_reset_confirm_code,
    request_link_code,
    request_password_reset as request_password_reset_telegram,
)
from server.services.rating_service import get_top_ratings
from server.services.db_schema_guard import get_db_schema_status
from server.services.docs_service import get_doc_content
from server.config import get_jwt_secret, get_reset_secret
from server.db import get_session


app = FastAPI(title="Cosmic API")
_LOG = logging.getLogger("cosmic.api")
_BOOT_CONFIG_OK = False


def _mask_code(code: str) -> str:
    """EN: Mask one-time code for logs without exposing full value.
    RU: Маскировать одноразовый код в логах без раскрытия полного значения.
    """

    value = str((code or "").strip())
    if not value:
        return "-"
    if len(value) <= 8:
        return f"{value[:1]}...{value[-1:]}(len={len(value)})"
    return f"{value[:4]}...{value[-4:]}(len={len(value)})"


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


def _config_secret_lengths() -> tuple[int, int]:
    """EN: Return lengths of JWT/RESET secrets without exposing values.
    RU: Вернуть длины JWT/RESET секретов без раскрытия самих значений.
    """

    jwt_len = len(os.getenv("JWT_SECRET", "").strip())
    reset_len = len(os.getenv("RESET_SECRET", "").strip())
    return int(jwt_len), int(reset_len)


def _validate_runtime_config() -> None:
    """EN: Validate required runtime secrets and raise on invalid config.
    RU: Проверить обязательные runtime-секреты и поднять ошибку при невалидной конфигурации.
    """

    jwt_secret = get_jwt_secret()
    reset_secret = get_reset_secret()
    _LOG.info("[BOOT] JWT_SECRET_LEN=%s", len(jwt_secret))
    _LOG.info("[BOOT] RESET_SECRET_LEN=%s", len(reset_secret))


@app.on_event("startup")
def on_startup_validate_config() -> None:
    """EN: Fail-fast startup hook: refuse to run API with missing secrets.
    RU: Fail-fast хук старта: запретить запуск API при отсутствии секретов.
    """

    global _BOOT_CONFIG_OK
    _validate_runtime_config()
    _BOOT_CONFIG_OK = True


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
def healthz() -> JSONResponse:
    """EN: Liveness endpoint for local deployment checks.
    RU: Эндпоинт проверки живости для локального развёртывания.
    """

    if not _BOOT_CONFIG_OK:
        return JSONResponse(status_code=503, content={"ok": False, "error": "CONFIG_INVALID"})

    jwt_len, reset_len = _config_secret_lengths()
    if jwt_len <= 0 or reset_len <= 0:
        return JSONResponse(status_code=503, content={"ok": False, "error": "CONFIG_INVALID"})

    try:
        with get_session() as session:
            session.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(status_code=503, content={"ok": False, "error": "DB_UNAVAILABLE"})

    schema_status = get_db_schema_status(force_refresh=True)
    if not schema_status.get("ok") or not schema_status.get("is_current"):
        return JSONResponse(status_code=503, content={"ok": False, "error": "DB_SCHEMA_OUTDATED"})

    return JSONResponse(status_code=200, content={"ok": True})


@app.get("/meta/compat")
def meta_compat() -> dict:
    """EN: Return runtime DB schema compatibility status for client-side readiness checks.
    RU: Вернуть runtime-статус совместимости схемы БД для клиентской проверки готовности.
    """

    status = get_db_schema_status(force_refresh=True)
    return {"ok": bool(status.get("ok")), "db": status}


@app.post("/ads/config")
def ads_config(payload: AdsConfigRequest, request: Request) -> dict:
    """EN: Return authenticated ads mediation config resolved from locale region and placement rules.
    RU: Вернуть authenticated ads-конфиг медиации, определенный по locale-региону и правилам плейсментов.
    """

    auth_user_id = _resolve_user_id_from_bearer(request)
    if auth_user_id is None or auth_user_id <= 0:
        return {"ok": False, "error": "UNAUTHORIZED"}
    if int(auth_user_id) != int(payload.user_id):
        return {"ok": False, "error": "UNAUTHORIZED"}
    result = get_ads_config(auth_user_id, payload)
    result.pop("user_id", None)
    result.pop("screen", None)
    result.pop("platform", None)
    result.pop("locale_country", None)
    result.pop("ts", None)
    return AdsConfigResponse(**result).model_dump()


@app.post("/ads/event")
def ads_event(payload: AdsEventRequest, request: Request) -> dict:
    """EN: Collect authenticated ads event and log it to stdout for current server stub stage.
    RU: Собрать authenticated ads-событие и залогировать его в stdout на текущем stub-этапе сервера.
    """

    auth_user_id = _resolve_user_id_from_bearer(request)
    if auth_user_id is None or auth_user_id <= 0:
        return {"ok": False, "error": "UNAUTHORIZED"}
    if int(auth_user_id) != int(payload.user_id):
        return {"ok": False, "error": "UNAUTHORIZED"}
    meta_payload = dict(payload.meta or {})
    if payload.extra:
        meta_payload.setdefault("extra", dict(payload.extra))
    return log_ads_event(
        user_id=payload.user_id,
        screen=str(payload.screen or "Unknown"),
        placement=payload.placement,
        event=payload.event,
        provider=payload.provider,
        flow_id=payload.flow_id,
        ok=payload.ok,
        detail=payload.detail,
        ts_client=payload.ts_client if payload.ts_client is not None else float(payload.ts or 0),
        meta=meta_payload,
    )


@app.post("/auth/register")
def auth_register(payload: RegisterRequest, request: Request) -> dict:
    """EN: Register user using existing auth service.
    RU: Зарегистрировать пользователя через существующий auth-сервис.
    """

    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    result = register_user(payload.email, payload.psw, user_agent=user_agent, ip=client_ip)
    return _service_result_to_response(result)


@app.post("/auth/login")
def auth_login(payload: LoginRequest, request: Request) -> dict:
    """EN: Login user using existing auth service.
    RU: Выполнить вход через существующий auth-сервис.
    """

    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    result = login_user(payload.email, payload.psw, user_agent=user_agent, ip=client_ip)
    return _service_result_to_response(result)


@app.post("/auth/refresh")
def auth_refresh(payload: RefreshRequest, request: Request) -> JSONResponse:
    """EN: Rotate refresh token and issue fresh access/refresh pair.
    RU: Ротировать refresh-токен и выдать свежую пару access/refresh.
    """

    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    result = refresh_auth(payload.refresh_token, user_agent=user_agent, ip=client_ip)
    if result.get("ok"):
        return JSONResponse(status_code=200, content=result)
    return JSONResponse(status_code=401, content={"ok": False, "error": "UNAUTHORIZED"})


@app.post("/auth/logout")
def auth_logout(payload: LogoutRequest) -> JSONResponse:
    """EN: Revoke provided refresh token.
    RU: Отозвать переданный refresh-токен.
    """

    result = logout_user(payload.refresh_token)
    if result.get("ok"):
        return JSONResponse(status_code=200, content={"ok": True})
    return JSONResponse(status_code=401, content={"ok": False, "error": "UNAUTHORIZED"})


@app.post("/auth/password/reset/request")
def auth_password_reset_request(payload: PasswordResetRequest, request: Request) -> dict:
    """EN: Request one-time password reset code by email with non-enumerating response.
    RU: Запросить одноразовый код восстановления по email с ответом без раскрытия существования аккаунта.
    """

    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    result = request_password_reset_telegram(payload.email, payload.channel, client_ip, user_agent)
    return result if isinstance(result, dict) else {"ok": True, "reset_link_code": None, "ttl_sec": 0}


@app.post("/auth/password/reset/confirm")
def auth_password_reset_confirm(payload: PasswordResetConfirm, request: Request) -> dict:
    """EN: Confirm one-time reset code and set new password hash.
    RU: Подтвердить одноразовый код и установить новый хеш пароля.
    """

    del request
    result = confirm_password_reset_telegram(
        payload.email,
        payload.confirm_code,
        payload.new_password,
    )
    return _service_result_to_response(result)


@app.post("/telegram/reset/issue_by_code")
def telegram_reset_issue_by_code(payload: BotResetIssueRequest, request: Request) -> dict:
    """EN: Bot-only endpoint issuing one-time 6-digit reset confirm code from reset_link_code.
    RU: Bot-only эндпоинт, выдающий одноразовый 6-значный reset confirm-код из reset_link_code.
    """

    expected_secret = str((os.getenv("BOT_SHARED_SECRET", "") or "").strip())
    provided_secret = str((request.headers.get("X-Bot-Secret", "") or "").strip())
    if not expected_secret or provided_secret != expected_secret:
        return {"ok": False, "error": "FORBIDDEN"}
    result = issue_reset_confirm_code(
        telegram_user_id=int(payload.telegram_user_id),
        reset_link_code=str(payload.reset_link_code),
        tg_username=payload.tg_username,
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


@app.post("/telegram/link/status")
def telegram_link_status(payload: TelegramLinkStatusRequest, request: Request) -> dict:
    """EN: Return status of latest Telegram deep-link code for authenticated user.
    RU: Вернуть статус последнего Telegram deep-link кода для авторизованного пользователя.
    """

    auth_user_id = _resolve_user_id_from_bearer(request)
    if auth_user_id is None or auth_user_id <= 0:
        return {"ok": False, "error": "UNAUTHORIZED"}
    if int(auth_user_id) != int(payload.user_id):
        return {"ok": False, "error": "FORBIDDEN"}
    result = get_last_link_status(int(payload.user_id))
    return _service_result_to_response(result)


@app.post("/payout/link/request")
def payout_link_request(payload: PayoutLinkRequest, request: Request) -> dict:
    """EN: Issue one-time payout deep-link code for authenticated user.
    RU: Выдать одноразовый payout deep-link-код для авторизованного пользователя.
    """

    auth_user_id = _resolve_user_id_from_bearer(request)
    if auth_user_id is None or auth_user_id <= 0:
        return {"ok": False, "error": "UNAUTHORIZED"}
    if int(auth_user_id) != int(payload.user_id):
        return {"ok": False, "error": "FORBIDDEN"}
    result = request_payout_link_code(int(payload.user_id))
    return _service_result_to_response(result)


@app.post("/payout/link/status")
def payout_link_status(payload: PayoutLinkStatusRequest, request: Request) -> dict:
    """EN: Return status of latest payout deep-link code for authenticated user.
    RU: Вернуть статус последнего payout deep-link кода для авторизованного пользователя.
    """

    auth_user_id = _resolve_user_id_from_bearer(request)
    if auth_user_id is None or auth_user_id <= 0:
        return {"ok": False, "error": "UNAUTHORIZED"}
    if int(auth_user_id) != int(payload.user_id):
        return {"ok": False, "error": "FORBIDDEN"}
    result = get_last_payout_link_status(int(payload.user_id))
    return _service_result_to_response(result)


@app.post("/payout/link/ack")
def payout_link_ack(payload: PayoutLinkAckRequest, request: Request) -> dict:
    """EN: Bot-only acknowledgement proving payout bot was opened from the app.
    RU: Bot-only подтверждение, доказывающее открытие payout bot из приложения.
    """

    expected_secret = str((os.getenv("PAY_BOT_SHARED_SECRET", "") or "").strip())
    provided_secret = str((request.headers.get("X-Bot-Secret", "") or "").strip())
    if not expected_secret or provided_secret != expected_secret:
        return {"ok": False, "error": "FORBIDDEN"}
    result = ack_payout_link_code(
        code=str(payload.code),
        telegram_user_id=int(payload.telegram_user_id),
        telegram_username=payload.telegram_username,
    )
    return _service_result_to_response(result)


@app.post("/telegram/link/confirm")
def telegram_link_confirm(payload: TelegramLinkConfirmRequest, request: Request) -> dict:
    """EN: Confirm bot-issued 6-digit code from app and finalize Telegram binding for current user.
    RU: Подтвердить 6-значный код из бота со стороны приложения и завершить привязку Telegram для текущего пользователя.
    """

    auth_user_id = _resolve_user_id_from_bearer(request)
    if auth_user_id is None or auth_user_id <= 0:
        return {"ok": False, "error": "UNAUTHORIZED"}
    if int(auth_user_id) != int(payload.user_id):
        return {"ok": False, "error": "UNAUTHORIZED"}
    result = confirm_link(payload.user_id, payload.confirm_code)
    return _service_result_to_response(result)


@app.post("/telegram/link/confirm_by_code")
def telegram_link_confirm_by_code(payload: TelegramLinkConfirmByCodeRequest, request: Request) -> dict:
    """EN: Convert pending link_code into a separate one-time confirm_code and return debug info for bot chat.
    RU: Преобразовать pending link_code в отдельный одноразовый confirm_code и вернуть debug-данные для чата бота.
    """

    client_ip = request.client.host if request.client else "-"
    user_agent = str(request.headers.get("user-agent") or "-")
    _LOG.info(
        "event=TG_CONFIRM_BY_CODE_IN ip=%s ua=%s tg_uid=%s tg_username=%s link_code=%s",
        client_ip,
        user_agent,
        int(payload.telegram_user_id),
        str(payload.tg_username or "-"),
        _mask_code(payload.link_code),
    )
    result = confirm_link_by_code(
        telegram_user_id=payload.telegram_user_id,
        link_code=payload.link_code,
        tg_username=payload.tg_username,
    )
    _LOG.info(
        "event=TG_CONFIRM_BY_CODE_API_RETURN ok=%s error=%s tg_uid=%s tg_username=%s link_code=%s",
        str(bool(result.get("ok"))).lower(),
        str(result.get("error") or "-"),
        int(payload.telegram_user_id),
        str(payload.tg_username or "-"),
        _mask_code(payload.link_code),
    )
    return _service_result_to_response(result)


@app.post("/telegram/link/confirm_latest")
def telegram_link_confirm_latest(payload: TelegramLinkConfirmLatestRequest, request: Request) -> dict:
    """EN: Confirm latest pending Telegram link by runtime Telegram identity (no link_code from bot state required).
    RU: Подтвердить последний pending Telegram link по текущей Telegram-идентичности (без link_code из состояния бота).
    """

    client_ip = request.client.host if request.client else "-"
    user_agent = str(request.headers.get("user-agent") or "-")
    _LOG.info(
        "event=TG_CONFIRM_LATEST_IN ip=%s ua=%s tg_uid=%s tg_username=%s",
        client_ip,
        user_agent,
        int(payload.telegram_user_id),
        str(payload.tg_username or "-"),
    )
    result = confirm_link_latest(
        telegram_user_id=payload.telegram_user_id,
        tg_username=payload.tg_username,
    )
    _LOG.info(
        "event=TG_CONFIRM_LATEST_OUT ok=%s error=%s tg_uid=%s tg_username=%s confirm_code_present=%s",
        str(bool(result.get("ok"))).lower(),
        str(result.get("error") or "-"),
        int(payload.telegram_user_id),
        str(payload.tg_username or "-"),
        str(bool(result.get("confirm_code"))).lower(),
    )
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
