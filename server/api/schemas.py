"""EN: Pydantic request/response schemas for local FastAPI server.
RU: Pydantic-схемы запросов/ответов для локального FastAPI-сервера.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    """EN: Registration payload with email/password.
    RU: Запрос регистрации с email/паролем.
    """

    email: str = Field(min_length=1)
    psw: str = Field(min_length=1)


class LoginRequest(BaseModel):
    """EN: Login payload with email/password.
    RU: Запрос входа с email/паролем.
    """

    email: str = Field(min_length=1)
    psw: str = Field(min_length=1)


class DeleteUserRequest(BaseModel):
    """EN: Account deletion payload by user identifier.
    RU: Запрос удаления аккаунта по идентификатору пользователя.
    """

    user_id: int


class ProfileUserUpdateRequest(BaseModel):
    """EN: Partial update payload for profile_users row.
    RU: Частичный запрос обновления строки profile_users.
    """

    user_id: int
    login: str | None = None
    phone: str | None = None
    telegram: str | None = None


class ProfileUserClearRequest(BaseModel):
    """EN: Request for resetting selected profile_users fields to defaults.
    RU: Запрос сброса выбранных полей profile_users к дефолтным значениям.
    """

    user_id: int
    fields: list[str]


class ProfileGameUpdateRequest(BaseModel):
    """EN: Partial update payload for profile_games row.
    RU: Частичный запрос обновления строки profile_games.
    """

    user_id: int
    record: int | None = None
    rating: int | None = None
    balance: int | None = None


class ProfileGameClearRequest(BaseModel):
    """EN: Request for resetting selected profile_games fields to defaults.
    RU: Запрос сброса выбранных полей profile_games к дефолтным значениям.
    """

    user_id: int
    fields: list[str]
