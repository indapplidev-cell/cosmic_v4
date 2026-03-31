"""EN: FastAPI entrypoint exposing HTTP endpoints over server services.
RU: РўРѕС‡РєР° РІС…РѕРґР° FastAPI, РїСѓР±Р»РёРєСѓСЋС‰Р°СЏ HTTP-СЌРЅРґРїРѕРёРЅС‚С‹ РїРѕРІРµСЂС… server-СЃРµСЂРІРёСЃРѕРІ.
"""

from __future__ import annotations

import os
import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import text

from server.api.schemas import (
    AdsConfigRequest,
    AdsConfigResponse,
    AdsEventRequest,
    PayoutLinkAckRequest,
    PayoutLinkRequest,
    PayoutRequestCreateRequest,
    PayoutMiniAppSessionRequest,
    PayoutMiniAppSessionStatusRequest,
    PayoutMiniAppInitRequest,
    PayoutMiniAppConfirmRequest,
    PayoutLinkStatusRequest,
    TelegramHubInitRequest,
    TelegramHubPayoutConfirmRequest,
    TelegramHubPayoutContextRequest,
    TelegramHubResetActionRequest,
    TelegramHubSessionRequest,
    TelegramHubVerifyActionRequest,
    BotResetIssueRequest,
    DeleteUserRequest,
    GameSessionFinishRequest,
    LevelScoreRecordUpsertRequest,
    LoginRequest,
    LogoutRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshRequest,
    TelegramMiniAppSessionConfirmRequest,
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
from server.services.payout_miniapp_service import (
    confirm_telegram_miniapp_session,
    get_telegram_link_miniapp_session_status,
    confirm_payout_miniapp_session,
    confirm_payout_miniapp,
    get_payout_miniapp_session_status,
    init_payout_miniapp,
    request_telegram_link_miniapp_session,
    request_payout_miniapp_session,
)
from server.services.payout_request_service import create_payout_request
from server.services.telegram_hub_service import (
    init_telegram_hub,
    request_telegram_hub_session,
    telegram_hub_action_payout_confirm,
    telegram_hub_action_payout_context,
    telegram_hub_action_reset,
    telegram_hub_action_verify,
)
from server.services.payout_service import ack_payout_link_code, get_last_payout_link_status, request_payout_link_code
from server.services.auth_service import (
    delete_user,
    get_user_snapshot,
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
from server.api.auth import get_authenticated_user_id, require_same_user
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
from server.services.level_score_record_service import upsert_level_score_record
from server.config import get_jwt_secret, get_reset_secret
from server.db import get_session


app = FastAPI(title="Cosmic API")
_LOG = logging.getLogger("cosmic.api")
_BOOT_CONFIG_OK = False
_PAYBOT_MINIAPP_INDEX = Path(__file__).resolve().parents[1] / "static" / "paybot_miniapp" / "index.html"
_PRIVACY_PAGE = Path(__file__).resolve().parents[1] / "static" / "paybot_miniapp" / "privacy.html"
_TERMS_PAGE = Path(__file__).resolve().parents[1] / "static" / "paybot_miniapp" / "terms.html"
_SUPPORT_PAGE = Path(__file__).resolve().parents[1] / "static" / "paybot_miniapp" / "support.html"


def _mask_code(code: str) -> str:
    """EN: Mask one-time code for logs without exposing full value.
    RU: РњР°СЃРєРёСЂРѕРІР°С‚СЊ РѕРґРЅРѕСЂР°Р·РѕРІС‹Р№ РєРѕРґ РІ Р»РѕРіР°С… Р±РµР· СЂР°СЃРєСЂС‹С‚РёСЏ РїРѕР»РЅРѕРіРѕ Р·РЅР°С‡РµРЅРёСЏ.
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
    RU: Р‘Р»РѕРєРёСЂРѕРІР°С‚СЊ РЅРµРґРёР°РіРЅРѕСЃС‚РёС‡РµСЃРєРёРµ Р·Р°РїСЂРѕСЃС‹, РµСЃР»Рё СЃС…РµРјР° Р‘Р” РѕС‚СЃС‚Р°С‘С‚ РѕС‚ Alembic head.
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
    RU: Р’РµСЂРЅСѓС‚СЊ РґР»РёРЅС‹ JWT/RESET СЃРµРєСЂРµС‚РѕРІ Р±РµР· СЂР°СЃРєСЂС‹С‚РёСЏ СЃР°РјРёС… Р·РЅР°С‡РµРЅРёР№.
    """

    jwt_len = len(os.getenv("JWT_SECRET", "").strip())
    reset_len = len(os.getenv("RESET_SECRET", "").strip())
    return int(jwt_len), int(reset_len)


def _validate_runtime_config() -> None:
    """EN: Validate required runtime secrets and raise on invalid config.
    RU: РџСЂРѕРІРµСЂРёС‚СЊ РѕР±СЏР·Р°С‚РµР»СЊРЅС‹Рµ runtime-СЃРµРєСЂРµС‚С‹ Рё РїРѕРґРЅСЏС‚СЊ РѕС€РёР±РєСѓ РїСЂРё РЅРµРІР°Р»РёРґРЅРѕР№ РєРѕРЅС„РёРіСѓСЂР°С†РёРё.
    """

    jwt_secret = get_jwt_secret()
    reset_secret = get_reset_secret()
    _LOG.info("[BOOT] JWT_SECRET_LEN=%s", len(jwt_secret))
    _LOG.info("[BOOT] RESET_SECRET_LEN=%s", len(reset_secret))


@app.on_event("startup")
def on_startup_validate_config() -> None:
    """EN: Fail-fast startup hook: refuse to run API with missing secrets.
    RU: Fail-fast С…СѓРє СЃС‚Р°СЂС‚Р°: Р·Р°РїСЂРµС‚РёС‚СЊ Р·Р°РїСѓСЃРє API РїСЂРё РѕС‚СЃСѓС‚СЃС‚РІРёРё СЃРµРєСЂРµС‚РѕРІ.
    """

    global _BOOT_CONFIG_OK
    _validate_runtime_config()
    _BOOT_CONFIG_OK = True


def _service_result_to_response(result: dict) -> dict:
    """EN: Return service result as business payload with stable HTTP 200 style.
    RU: Р’РµСЂРЅСѓС‚СЊ СЂРµР·СѓР»СЊС‚Р°С‚ СЃРµСЂРІРёСЃР° РєР°Рє business-payload СЃРѕ СЃС‚Р°Р±РёР»СЊРЅС‹Рј СЃС‚РёР»РµРј HTTP 200.
    """

    if result.get("ok"):
        return result
    return {"ok": False, "error": str(result.get("error", "DB_ERROR"))}


def _get_optional_authenticated_user_id(request: Request) -> int | None:
    """EN: Return authenticated user id when bearer token exists, otherwise `None`.
    RU: Вернуть id авторизованного пользователя при наличии bearer-токена, иначе `None`.
    """

    try:
        return get_authenticated_user_id(request)
    except HTTPException as exc:
        if int(exc.status_code) == 401:
            return None
        raise



@app.get("/healthz")
def healthz() -> JSONResponse:
    """EN: Liveness endpoint for local deployment checks.
    RU: Р­РЅРґРїРѕРёРЅС‚ РїСЂРѕРІРµСЂРєРё Р¶РёРІРѕСЃС‚Рё РґР»СЏ Р»РѕРєР°Р»СЊРЅРѕРіРѕ СЂР°Р·РІС‘СЂС‚С‹РІР°РЅРёСЏ.
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
    RU: Р’РµСЂРЅСѓС‚СЊ runtime-СЃС‚Р°С‚СѓСЃ СЃРѕРІРјРµСЃС‚РёРјРѕСЃС‚Рё СЃС…РµРјС‹ Р‘Р” РґР»СЏ РєР»РёРµРЅС‚СЃРєРѕР№ РїСЂРѕРІРµСЂРєРё РіРѕС‚РѕРІРЅРѕСЃС‚Рё.
    """

    status = get_db_schema_status(force_refresh=True)
    return {"ok": bool(status.get("ok")), "db": status}


@app.post("/ads/config")
def ads_config(payload: AdsConfigRequest, request: Request) -> dict:
    """EN: Return authenticated ads mediation config resolved from locale region and placement rules.
    RU: Р’РµСЂРЅСѓС‚СЊ authenticated ads-РєРѕРЅС„РёРі РјРµРґРёР°С†РёРё, РѕРїСЂРµРґРµР»РµРЅРЅС‹Р№ РїРѕ locale-СЂРµРіРёРѕРЅСѓ Рё РїСЂР°РІРёР»Р°Рј РїР»РµР№СЃРјРµРЅС‚РѕРІ.
    """

    auth_user_id = require_same_user(request, int(payload.user_id))
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
    RU: РЎРѕР±СЂР°С‚СЊ authenticated ads-СЃРѕР±С‹С‚РёРµ Рё Р·Р°Р»РѕРіРёСЂРѕРІР°С‚СЊ РµРіРѕ РІ stdout РЅР° С‚РµРєСѓС‰РµРј stub-СЌС‚Р°РїРµ СЃРµСЂРІРµСЂР°.
    """

    auth_user_id = require_same_user(request, int(payload.user_id))
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
    RU: Р—Р°СЂРµРіРёСЃС‚СЂРёСЂРѕРІР°С‚СЊ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ С‡РµСЂРµР· СЃСѓС‰РµСЃС‚РІСѓСЋС‰РёР№ auth-СЃРµСЂРІРёСЃ.
    """

    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    result = register_user(payload.email, payload.psw, user_agent=user_agent, ip=client_ip)
    return _service_result_to_response(result)


@app.post("/auth/login")
def auth_login(payload: LoginRequest, request: Request) -> dict:
    """EN: Login user using existing auth service.
    RU: Р’С‹РїРѕР»РЅРёС‚СЊ РІС…РѕРґ С‡РµСЂРµР· СЃСѓС‰РµСЃС‚РІСѓСЋС‰РёР№ auth-СЃРµСЂРІРёСЃ.
    """

    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    result = login_user(payload.email, payload.psw, user_agent=user_agent, ip=client_ip)
    return _service_result_to_response(result)


@app.post("/auth/refresh")
def auth_refresh(payload: RefreshRequest, request: Request) -> JSONResponse:
    """EN: Rotate refresh token and issue fresh access/refresh pair.
    RU: Р РѕС‚РёСЂРѕРІР°С‚СЊ refresh-С‚РѕРєРµРЅ Рё РІС‹РґР°С‚СЊ СЃРІРµР¶СѓСЋ РїР°СЂСѓ access/refresh.
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
    RU: РћС‚РѕР·РІР°С‚СЊ РїРµСЂРµРґР°РЅРЅС‹Р№ refresh-С‚РѕРєРµРЅ.
    """

    result = logout_user(payload.refresh_token)
    if result.get("ok"):
        return JSONResponse(status_code=200, content={"ok": True})
    return JSONResponse(status_code=401, content={"ok": False, "error": "UNAUTHORIZED"})


@app.post("/auth/password/reset/request")
def auth_password_reset_request(payload: PasswordResetRequest, request: Request) -> dict:
    """EN: Request one-time password reset code by email with non-enumerating response.
    RU: Р—Р°РїСЂРѕСЃРёС‚СЊ РѕРґРЅРѕСЂР°Р·РѕРІС‹Р№ РєРѕРґ РІРѕСЃСЃС‚Р°РЅРѕРІР»РµРЅРёСЏ РїРѕ email СЃ РѕС‚РІРµС‚РѕРј Р±РµР· СЂР°СЃРєСЂС‹С‚РёСЏ СЃСѓС‰РµСЃС‚РІРѕРІР°РЅРёСЏ Р°РєРєР°СѓРЅС‚Р°.
    """

    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    result = request_password_reset_telegram(payload.email, payload.channel, client_ip, user_agent)
    return result if isinstance(result, dict) else {"ok": True, "reset_link_code": None, "ttl_sec": 0}


@app.post("/auth/password/reset/confirm")
def auth_password_reset_confirm(payload: PasswordResetConfirm, request: Request) -> dict:
    """EN: Confirm one-time reset code and set new password hash.
    RU: РџРѕРґС‚РІРµСЂРґРёС‚СЊ РѕРґРЅРѕСЂР°Р·РѕРІС‹Р№ РєРѕРґ Рё СѓСЃС‚Р°РЅРѕРІРёС‚СЊ РЅРѕРІС‹Р№ С…РµС€ РїР°СЂРѕР»СЏ.
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
    RU: Bot-only СЌРЅРґРїРѕРёРЅС‚, РІС‹РґР°СЋС‰РёР№ РѕРґРЅРѕСЂР°Р·РѕРІС‹Р№ 6-Р·РЅР°С‡РЅС‹Р№ reset confirm-РєРѕРґ РёР· reset_link_code.
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
    """EN: Legacy Telegram deep-link request kept only as fallback UX and not as the main security boundary.
    RU: Legacy-запрос Telegram deep-link, оставленный только как fallback UX и не используемый как основной security boundary.
    """

    require_same_user(request, int(payload.user_id))
    result = request_link_code(payload.user_id)
    return _service_result_to_response(result)


@app.post("/telegram/link/miniapp/session/request")
def telegram_link_miniapp_session_request(payload: TelegramLinkRequest, request: Request) -> dict:
    """EN: Issue one-time telegram_link Mini App verification session for authenticated user.
    RU: Выдать одноразовую telegram_link Mini App verification-session для авторизованного пользователя.
    """

    require_same_user(request, int(payload.user_id))
    result = request_telegram_link_miniapp_session(int(payload.user_id))
    return _service_result_to_response(result)


@app.post("/telegram/link/status")
def telegram_link_status(payload: TelegramLinkStatusRequest, request: Request) -> dict:
    """EN: Legacy Telegram deep-link status kept only as fallback UX and not as the main security boundary.
    RU: Legacy-статус Telegram deep-link, оставленный только как fallback UX и не используемый как основной security boundary.
    """

    require_same_user(request, int(payload.user_id))
    result = get_last_link_status(int(payload.user_id))
    return _service_result_to_response(result)


@app.post("/telegram/link/miniapp/session/status")
def telegram_link_miniapp_session_status(payload: TelegramLinkStatusRequest, request: Request) -> dict:
    """EN: Return current telegram_link Mini App verification status for authenticated user.
    RU: Вернуть текущий статус telegram_link Mini App verification для авторизованного пользователя.
    """

    require_same_user(request, int(payload.user_id))
    result = get_telegram_link_miniapp_session_status(int(payload.user_id))
    return _service_result_to_response(result)


@app.post("/payout/link/request")
def payout_link_request(payload: PayoutLinkRequest, request: Request) -> dict:
    """EN: Legacy payout deep-link request kept only for non-security fallback UX.
    RU: Legacy-запрос payout deep-link, оставленный только для не security-критичного fallback UX.
    """

    require_same_user(request, int(payload.user_id))
    result = request_payout_link_code(int(payload.user_id))
    return _service_result_to_response(result)


@app.post("/payout/link/status")
def payout_link_status(payload: PayoutLinkStatusRequest, request: Request) -> dict:
    """EN: Legacy payout deep-link status kept only for non-security fallback UX.
    RU: Legacy-статус payout deep-link, оставленный только для не security-критичного fallback UX.
    """

    require_same_user(request, int(payload.user_id))
    result = get_last_payout_link_status(int(payload.user_id))
    return _service_result_to_response(result)


@app.post("/payout/link/ack")
def payout_link_ack(payload: PayoutLinkAckRequest, request: Request) -> dict:
    """EN: Legacy paybot ack endpoint kept for fallback UX and not used as payout security boundary.
    RU: Legacy-endpoint paybot ack, оставленный для fallback UX и не используемый как security boundary payout.
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


@app.post("/telegram/payout/miniapp/session/request")
def telegram_payout_miniapp_session_request(payload: PayoutMiniAppSessionRequest, request: Request) -> dict:
    """EN: Canonical payout Mini App session issue endpoint returning exact Telegram direct launch URL.
    RU: Канонический endpoint выдачи payout Mini App session, возвращающий точный Telegram direct launch URL.
    """

    require_same_user(request, int(payload.user_id))
    result = request_payout_miniapp_session(int(payload.user_id))
    return _service_result_to_response(result)


@app.post("/telegram/hub/session/request")
def telegram_hub_session_request(payload: TelegramHubSessionRequest, request: Request) -> dict:
    """EN: Issue one shared Telegram Mini App hub session for verify/reset/payout entry points.
    RU: Выдать одну общую Telegram Mini App hub session для точек входа verify/reset/payout.
    """

    auth_user_id = _get_optional_authenticated_user_id(request)
    requested_user_id = int(payload.user_id or 0) if payload.user_id is not None else None
    if payload.entry_action in {"verify", "payout"}:
        if auth_user_id is None:
            return {"ok": False, "error": "UNAUTHORIZED"}
        if requested_user_id is None or requested_user_id <= 0:
            return {"ok": False, "error": "FORBIDDEN"}
        require_same_user(request, int(requested_user_id))
    result = request_telegram_hub_session(
        entry_action=str(payload.entry_action),
        auth_user_id=auth_user_id,
        requested_user_id=requested_user_id,
        email=payload.email,
    )
    return _service_result_to_response(result)


@app.post("/telegram/miniapp/session/confirm")
def telegram_miniapp_session_confirm(payload: TelegramMiniAppSessionConfirmRequest) -> dict:
    """EN: Validate Telegram Mini App initData and confirm one purpose-aware session.
    RU: Проверить Telegram Mini App initData и подтвердить одну purpose-aware session.
    """

    result = confirm_telegram_miniapp_session(
        init_data_raw=str(payload.init_data_raw),
        start_param=str(payload.start_param),
    )
    return _service_result_to_response(result)


@app.post("/payout/miniapp/session/confirm")
def payout_miniapp_session_confirm(payload: TelegramMiniAppSessionConfirmRequest) -> dict:
    """EN: Validate Telegram Mini App initData and verify payout identity for one session.
    RU: Проверить Telegram Mini App initData и подтвердить payout identity для одной session.
    """

    result = confirm_payout_miniapp_session(
        init_data_raw=str(payload.init_data_raw),
        start_param=str(payload.start_param),
    )
    return _service_result_to_response(result)


@app.post("/telegram/payout/miniapp/init")
def telegram_payout_miniapp_init(payload: PayoutMiniAppInitRequest) -> dict:
    """EN: Initialize payout Mini App server context after validating Telegram initData and startapp token.
    RU: Инициализировать серверный payout Mini App context после проверки Telegram initData и startapp-токена.
    """

    result = init_payout_miniapp(
        init_data_raw=str(payload.init_data),
        start_param=str(payload.start_param),
    )
    return _service_result_to_response(result)


@app.post("/telegram/payout/miniapp/confirm")
def telegram_payout_miniapp_confirm(payload: PayoutMiniAppConfirmRequest) -> dict:
    """EN: Confirm payout from Telegram Mini App with full server-side validation and request creation.
    RU: Подтвердить payout из Telegram Mini App с полной серверной проверкой и созданием request.
    """

    result = confirm_payout_miniapp(
        init_data_raw=str(payload.init_data),
        start_param=str(payload.start_param),
        amount=payload.amount,
        wallet_address=str(payload.wallet_address),
        network=str(payload.network),
    )
    return _service_result_to_response(result)


@app.post("/telegram/hub/init")
def telegram_hub_init(payload: TelegramHubInitRequest) -> dict:
    """EN: Validate Telegram initData once and return trusted shared hub context.
    RU: Один раз проверить Telegram initData и вернуть доверенный общий hub context.
    """

    result = init_telegram_hub(
        init_data=str(payload.init_data),
        start_param=str(payload.start_param),
    )
    return _service_result_to_response(result)


@app.post("/telegram/hub/action/verify")
def telegram_hub_verify_action(payload: TelegramHubVerifyActionRequest) -> dict:
    """EN: Execute Telegram verify/link action through trusted hub session.
    RU: Выполнить действие verify/link Telegram через доверенную hub session.
    """

    result = telegram_hub_action_verify(str(payload.hub_token))
    return _service_result_to_response(result)


@app.post("/telegram/hub/action/reset")
def telegram_hub_reset_action(payload: TelegramHubResetActionRequest) -> dict:
    """EN: Execute password reset action through trusted hub session.
    RU: Выполнить действие сброса пароля через доверенную hub session.
    """

    result = telegram_hub_action_reset(
        str(payload.hub_token),
        str(payload.new_password),
    )
    return _service_result_to_response(result)


@app.post("/telegram/hub/action/payout/context")
def telegram_hub_payout_context_action(payload: TelegramHubPayoutContextRequest) -> dict:
    """EN: Load payout section context through trusted hub session.
    RU: Загрузить context payout-секции через доверенную hub session.
    """

    result = telegram_hub_action_payout_context(str(payload.hub_token))
    return _service_result_to_response(result)


@app.post("/telegram/hub/action/payout/confirm")
def telegram_hub_payout_confirm_action(payload: TelegramHubPayoutConfirmRequest) -> dict:
    """EN: Confirm payout through trusted hub session with repeated server-side checks.
    RU: Подтвердить payout через доверенную hub session с повторными server-side проверками.
    """

    result = telegram_hub_action_payout_confirm(
        str(payload.hub_token),
        amount=payload.amount,
        wallet_address=str(payload.wallet_address),
        network=str(payload.network),
    )
    return _service_result_to_response(result)


@app.post("/payout/miniapp/session/status")
def payout_miniapp_session_status(payload: PayoutMiniAppSessionStatusRequest, request: Request) -> dict:
    """EN: Return current payout Mini App verification status for authenticated user.
    RU: Вернуть текущий статус payout Mini App verification для авторизованного пользователя.
    """

    require_same_user(request, int(payload.user_id))
    result = get_payout_miniapp_session_status(int(payload.user_id))
    return _service_result_to_response(result)


@app.post("/payout/request/create")
def payout_request_create(payload: PayoutRequestCreateRequest, request: Request) -> dict:
    """EN: Create internal payout request after Mini App verification and reserve user balance.
    RU: Создать внутренний payout request после Mini App verification и зарезервировать баланс пользователя.
    """

    require_same_user(request, int(payload.user_id))
    result = create_payout_request(
        user_id=int(payload.user_id),
        amount=payload.amount,
        wallet_address=str(payload.wallet_address),
    )
    return _service_result_to_response(result)


@app.get("/main/miniapp")
def paybot_miniapp_index() -> FileResponse:
    """EN: Serve static Telegram Mini App frontend for shared identity verification purposes.
    RU: Отдать статический Telegram Mini App frontend для общих целей проверки identity.

    EN: BotFather Mini App configuration for `ESCAPE2MARS_MINIAPP_SHORT_NAME` is expected
    to point to this public backend route.
    RU: Ожидается, что конфигурация Mini App в BotFather для `ESCAPE2MARS_MINIAPP_SHORT_NAME`
    будет указывать именно на этот публичный backend-route.
    """

    return FileResponse(_PAYBOT_MINIAPP_INDEX)


@app.get("/privacy")
def privacy_page() -> FileResponse:
    """EN: Serve public privacy policy page required for Telegram Mini App deployment.
    RU: Отдать публичную страницу privacy policy, необходимую для деплоя Telegram Mini App.
    """

    return FileResponse(_PRIVACY_PAGE)


@app.get("/terms")
def terms_page() -> FileResponse:
    """EN: Serve public terms page required for Telegram Mini App deployment.
    RU: Отдать публичную страницу terms, необходимую для деплоя Telegram Mini App.
    """

    return FileResponse(_TERMS_PAGE)


@app.get("/support")
def support_page() -> FileResponse:
    """EN: Serve public support/contact page required for Telegram Mini App deployment.
    RU: Отдать публичную страницу support/contact, необходимую для деплоя Telegram Mini App.
    """

    return FileResponse(_SUPPORT_PAGE)


@app.post("/telegram/link/confirm")
def telegram_link_confirm(payload: TelegramLinkConfirmRequest, request: Request) -> dict:
    """EN: Legacy Telegram code confirmation kept only as fallback UX and not as the main security boundary.
    RU: Legacy-подтверждение Telegram по коду, оставленное только как fallback UX и не используемое как основной security boundary.
    """

    require_same_user(request, int(payload.user_id))
    result = confirm_link(payload.user_id, payload.confirm_code)
    return _service_result_to_response(result)


@app.post("/telegram/link/confirm_by_code")
def telegram_link_confirm_by_code(payload: TelegramLinkConfirmByCodeRequest, request: Request) -> dict:
    """EN: Legacy bot endpoint for fallback Telegram link flow and not a trusted security boundary.
    RU: Legacy bot-endpoint для fallback Telegram link flow и не доверенный security boundary.
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
    """EN: Legacy bot endpoint for fallback latest Telegram link confirmation and not a trusted security boundary.
    RU: Legacy bot-endpoint для fallback-подтверждения последней Telegram link session и не доверенный security boundary.
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
def auth_me(request: Request) -> dict:
    """EN: Return current user snapshot by user_id for cache validation/synchronization.
    RU: Р’РµСЂРЅСѓС‚СЊ snapshot С‚РµРєСѓС‰РµРіРѕ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ РїРѕ user_id РґР»СЏ РїСЂРѕРІРµСЂРєРё/СЃРёРЅС…СЂРѕРЅРёР·Р°С†РёРё РєСЌС€Р°.
    """

    auth_user_id = get_authenticated_user_id(request)
    return _service_result_to_response(get_user_snapshot(auth_user_id))

@app.post("/auth/delete")
def auth_delete(payload: DeleteUserRequest, request: Request) -> dict:
    """EN: Delete user by id via auth service.
    RU: РЈРґР°Р»РёС‚СЊ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ РїРѕ id С‡РµСЂРµР· auth-СЃРµСЂРІРёСЃ.
    """

    require_same_user(request, int(payload.user_id))
    result = delete_user(payload.user_id)
    return _service_result_to_response(result)


@app.post("/profile/user/update")
def profile_user_update(payload: ProfileUserUpdateRequest, request: Request) -> dict:
    """EN: Update profile_users fields for selected user.
    RU: РћР±РЅРѕРІРёС‚СЊ РїРѕР»СЏ profile_users РґР»СЏ РІС‹Р±СЂР°РЅРЅРѕРіРѕ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ.
    """

    require_same_user(request, int(payload.user_id))
    result = update_profile_user(
        payload.user_id,
        login=payload.login,
        phone=payload.phone,
        telegram=payload.telegram,
    )
    return _service_result_to_response(result)


@app.post("/profile/user/clear")
def profile_user_clear(payload: ProfileUserClearRequest, request: Request) -> dict:
    """EN: Reset selected profile_users fields to defaults.
    RU: РЎР±СЂРѕСЃРёС‚СЊ РІС‹Р±СЂР°РЅРЅС‹Рµ РїРѕР»СЏ profile_users Рє Р·РЅР°С‡РµРЅРёСЏРј РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ.
    """

    require_same_user(request, int(payload.user_id))
    result = clear_profile_user_fields(payload.user_id, payload.fields)
    return _service_result_to_response(result)


@app.post("/profile/game/update")
def profile_game_update(payload: ProfileGameUpdateRequest, request: Request) -> dict:
    """EN: Update profile_games numeric fields for selected user.
    RU: РћР±РЅРѕРІРёС‚СЊ С‡РёСЃР»РѕРІС‹Рµ РїРѕР»СЏ profile_games РґР»СЏ РІС‹Р±СЂР°РЅРЅРѕРіРѕ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ.
    """

    require_same_user(request, int(payload.user_id))
    result = update_profile_game(
        payload.user_id,
        record=payload.record,
        rating=payload.rating,
        balance=payload.balance,
    )
    return _service_result_to_response(result)


@app.post("/profile/game/clear")
def profile_game_clear(payload: ProfileGameClearRequest, request: Request) -> dict:
    """EN: Reset selected profile_games fields to defaults.
    RU: РЎР±СЂРѕСЃРёС‚СЊ РІС‹Р±СЂР°РЅРЅС‹Рµ РїРѕР»СЏ profile_games Рє Р·РЅР°С‡РµРЅРёСЏРј РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ.
    """

    require_same_user(request, int(payload.user_id))
    result = clear_profile_game_fields(payload.user_id, payload.fields)
    return _service_result_to_response(result)


@app.get("/rating/top")
def rating_top(limit: int = Query(default=100, ge=1, le=100)) -> dict:
    """EN: Return top rating rows via existing rating service.
    RU: Р’РµСЂРЅСѓС‚СЊ С‚РѕРї СЃС‚СЂРѕРє СЂРµР№С‚РёРЅРіР° С‡РµСЂРµР· СЃСѓС‰РµСЃС‚РІСѓСЋС‰РёР№ rating-СЃРµСЂРІРёСЃ.
    """

    items = get_top_ratings(limit=limit)
    return {"ok": True, "items": items}


@app.post("/game/session/finish")
def game_session_finish(payload: GameSessionFinishRequest, request: Request) -> dict:
    """EN: Accept raw SIS metrics, calculate profile updates on server, and persist results.
    RU: РџСЂРёРЅСЏС‚СЊ СЃС‹СЂС‹Рµ РјРµС‚СЂРёРєРё РЎРРЎ, СЂР°СЃСЃС‡РёС‚Р°С‚СЊ РѕР±РЅРѕРІР»РµРЅРёСЏ РїСЂРѕС„РёР»СЏ РЅР° СЃРµСЂРІРµСЂРµ Рё СЃРѕС…СЂР°РЅРёС‚СЊ СЂРµР·СѓР»СЊС‚Р°С‚.
    """

    require_same_user(request, int(payload.user_id))
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


@app.post("/game/level-score-record")
def game_level_score_record(payload: LevelScoreRecordUpsertRequest, request: Request) -> dict:
    """EN: Accept one authenticated finished-run result and upsert it into the per-level score-record table.
    RU: ??????? ???? ??????????????????? ???? ???????????? run ? ???????? ??? ? ??????? ???????? ?? ???????.
    """

    auth_user_id = get_authenticated_user_id(request)
    result = upsert_level_score_record(
        user_id=int(auth_user_id),
        level_number=int(payload.level_number),
        score=int(payload.score),
        elapsed_ms=int(payload.elapsed_ms),
        result=str(payload.result),
        attempts_used=payload.attempts_used,
        reward_used=bool(payload.reward_used),
    )
    return _service_result_to_response(result)


@app.get("/docs/{doc_key}")
def docs_get(doc_key: str, lang: str = Query(default="ru", min_length=2, max_length=2)) -> dict:
    """EN: Return localized markdown document content from server storage.
    RU: Р’РµСЂРЅСѓС‚СЊ Р»РѕРєР°Р»РёР·РѕРІР°РЅРЅРѕРµ СЃРѕРґРµСЂР¶РёРјРѕРµ markdown-РґРѕРєСѓРјРµРЅС‚Р° РёР· СЃРµСЂРІРµСЂРЅРѕРіРѕ С…СЂР°РЅРёР»РёС‰Р°.
    """

    return get_doc_content(doc_key=doc_key, lang=lang)

