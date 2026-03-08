"""EN: Pydantic request schemas with strict validation for API input payloads.
RU: Pydantic-схемы запросов со строгой валидацией входных payload API.
"""

from __future__ import annotations

from typing import Annotated, Literal

from annotated_types import MaxLen, MinLen
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from server.security.validators import (
    reject_control_chars,
    validate_login,
    validate_nonneg_int,
    validate_phone,
    validate_telegram,
)


class StrictBaseModel(BaseModel):
    """EN: Base schema that forbids unknown fields and strips outer whitespace.
    RU: Базовая схема, запрещающая лишние поля и обрезающая внешний пробел.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class RegisterRequest(StrictBaseModel):
    """EN: Registration payload with strict email and password constraints.
    RU: Payload регистрации со строгими ограничениями email и пароля.
    """

    email: EmailStr
    psw: Annotated[str, MinLen(8), MaxLen(72)]

    @field_validator("psw")
    @classmethod
    def validate_psw(cls, value: str) -> str:
        """EN: Reject control characters in plaintext password input.
        RU: Отклонить управляющие символы во входном plaintext-пароле.
        """

        return reject_control_chars(value)


class LoginRequest(StrictBaseModel):
    """EN: Login payload with strict email and password constraints.
    RU: Payload входа со строгими ограничениями email и пароля.
    """

    email: EmailStr
    psw: Annotated[str, MinLen(8), MaxLen(72)]

    @field_validator("psw")
    @classmethod
    def validate_psw(cls, value: str) -> str:
        """EN: Reject control characters in plaintext password input.
        RU: Отклонить управляющие символы во входном plaintext-пароле.
        """

        return reject_control_chars(value)


class DeleteUserRequest(StrictBaseModel):
    """EN: Account deletion payload by positive user identifier.
    RU: Payload удаления аккаунта по положительному идентификатору пользователя.
    """

    user_id: int = Field(gt=0)


class ProfileUserUpdateRequest(StrictBaseModel):
    """EN: Partial update payload for profile_users with strict allowlist validation.
    RU: Payload частичного обновления profile_users со строгой allowlist-валидацией.
    """

    user_id: int = Field(gt=0)
    login: str | None = None
    phone: str | None = None
    telegram: str | None = None

    @field_validator("login")
    @classmethod
    def validate_login_field(cls, value: str | None) -> str | None:
        """EN: Validate optional login input when provided.
        RU: Провалидировать опциональный login при передаче.
        """

        if value is None:
            return None
        return validate_login(value)

    @field_validator("phone")
    @classmethod
    def validate_phone_field(cls, value: str | None) -> str | None:
        """EN: Validate optional phone input when provided.
        RU: Провалидировать опциональный phone при передаче.
        """

        if value is None:
            return None
        return validate_phone(value)

    @field_validator("telegram")
    @classmethod
    def validate_telegram_field(cls, value: str | None) -> str | None:
        """EN: Validate optional Telegram input when provided.
        RU: Провалидировать опциональный Telegram при передаче.
        """

        if value is None:
            return None
        return validate_telegram(value)


class ProfileUserClearRequest(StrictBaseModel):
    """EN: Request for resetting selected profile_users fields to defaults.
    RU: Запрос сброса выбранных полей profile_users к значениям по умолчанию.
    """

    user_id: int = Field(gt=0)
    fields: list[Literal["login", "phone", "telegram"]] = Field(min_length=1, max_length=3)

    @field_validator("fields")
    @classmethod
    def validate_unique_fields(cls, value: list[str]) -> list[str]:
        """EN: Ensure field names list does not contain duplicates.
        RU: Убедиться, что список имён полей не содержит дубликатов.
        """

        if len(set(value)) != len(value):
            raise ValueError("FORMAT")
        return value


class ProfileGameUpdateRequest(StrictBaseModel):
    """EN: Partial update payload for profile_games numeric fields.
    RU: Payload частичного обновления числовых полей profile_games.
    """

    user_id: int = Field(gt=0)
    record: int | None = None
    rating: int | None = None
    balance: float | None = None

    @field_validator("record")
    @classmethod
    def validate_record(cls, value: int | None) -> int | None:
        """EN: Validate optional record value bounds.
        RU: Проверить границы опционального значения record.
        """

        if value is None:
            return None
        return validate_nonneg_int(value)

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, value: int | None) -> int | None:
        """EN: Validate optional rating value bounds.
        RU: Проверить границы опционального значения rating.
        """

        if value is None:
            return None
        return validate_nonneg_int(value)

    @field_validator("balance")
    @classmethod
    def validate_balance(cls, value: float | None) -> float | None:
        """EN: Validate optional balance bounds and normalize to 3 decimals.
        RU: Проверить границы balance и нормализовать до 3 знаков.
        """

        if value is None:
            return None
        value_f = round(float(value), 3)
        if value_f < 0 or value_f > 2_000_000_000:
            raise ValueError("FORMAT")
        return value_f


class ProfileGameClearRequest(StrictBaseModel):
    """EN: Request for resetting selected profile_games fields to defaults.
    RU: Запрос сброса выбранных полей profile_games к значениям по умолчанию.
    """

    user_id: int = Field(gt=0)
    fields: list[Literal["record", "rating", "balance"]] = Field(min_length=1, max_length=3)

    @field_validator("fields")
    @classmethod
    def validate_unique_fields(cls, value: list[str]) -> list[str]:
        """EN: Ensure field names list does not contain duplicates.
        RU: Убедиться, что список имён полей не содержит дубликатов.
        """

        if len(set(value)) != len(value):
            raise ValueError("FORMAT")
        return value
