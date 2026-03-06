"""EN: FastAPI entrypoint exposing HTTP endpoints over server services.
RU: Точка входа FastAPI, публикующая HTTP-эндпоинты поверх server-сервисов.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Query
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
from server.services.auth_service import delete_user, login_user, register_user
from server.services.profile_service import (
    clear_profile_game_fields,
    clear_profile_user_fields,
    update_profile_game,
    update_profile_user,
)
from server.services.rating_service import get_top_ratings


app = FastAPI(title="Cosmic API")


def _error(error_code: str, status_code: int = 400) -> JSONResponse:
    """EN: Build standard API error payload.
    RU: Сформировать стандартный формат ошибки API.
    """

    return JSONResponse(status_code=status_code, content={"ok": False, "error": error_code})


def _service_result_to_response(result: dict) -> Any:
    """EN: Convert service result dict into HTTP response payload.
    RU: Преобразовать ответ сервиса в HTTP-ответ с корректным кодом.
    """

    if result.get("ok"):
        return result

    error_code = str(result.get("error", "DB_ERROR"))
    if error_code in {"NOT_FOUND"}:
        return _error(error_code, status_code=404)
    return _error(error_code, status_code=400)


@app.get("/healthz")
def healthz() -> dict:
    """EN: Liveness endpoint for local deployment checks.
    RU: Эндпоинт проверки живости для локального развёртывания.
    """

    return {"ok": True}


@app.post("/auth/register", response_model=None)
def auth_register(payload: RegisterRequest) -> Any:
    """EN: Register user using existing auth service.
    RU: Зарегистрировать пользователя через существующий auth-сервис.
    """

    result = register_user(payload.email, payload.psw)
    return _service_result_to_response(result)


@app.post("/auth/login", response_model=None)
def auth_login(payload: LoginRequest) -> Any:
    """EN: Login user using existing auth service.
    RU: Выполнить вход через существующий auth-сервис.
    """

    result = login_user(payload.email, payload.psw)
    return _service_result_to_response(result)


@app.post("/auth/delete", response_model=None)
def auth_delete(payload: DeleteUserRequest) -> Any:
    """EN: Delete user by id via auth service.
    RU: Удалить пользователя по id через auth-сервис.
    """

    result = delete_user(payload.user_id)
    return _service_result_to_response(result)


@app.post("/profile/user/update", response_model=None)
def profile_user_update(payload: ProfileUserUpdateRequest) -> Any:
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


@app.post("/profile/user/clear", response_model=None)
def profile_user_clear(payload: ProfileUserClearRequest) -> Any:
    """EN: Reset selected profile_users fields to defaults.
    RU: Сбросить выбранные поля profile_users к значениям по умолчанию.
    """

    result = clear_profile_user_fields(payload.user_id, payload.fields)
    return _service_result_to_response(result)


@app.post("/profile/game/update", response_model=None)
def profile_game_update(payload: ProfileGameUpdateRequest) -> Any:
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


@app.post("/profile/game/clear", response_model=None)
def profile_game_clear(payload: ProfileGameClearRequest) -> Any:
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
