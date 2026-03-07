"""EN: FastAPI entrypoint exposing HTTP endpoints over server services.
RU: Точка входа FastAPI, публикующая HTTP-эндпоинты поверх server-сервисов.
"""

from __future__ import annotations

from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse

from server.api.schemas import (
    DeleteUserRequest,
    LoginRequest,
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
    clear_profile_game_fields,
    clear_profile_user_fields,
    update_profile_game,
    update_profile_user,
)
from server.services.rating_service import get_top_ratings
from server.services.db_schema_guard import get_db_schema_status


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
