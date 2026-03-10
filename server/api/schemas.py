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


class RefreshRequest(StrictBaseModel):
    """EN: Refresh endpoint payload with one refresh token string.
    RU: Payload эндпоинта refresh с одной строкой refresh-токена.
    """

    refresh_token: Annotated[str, MinLen(16), MaxLen(4096)]


class LogoutRequest(StrictBaseModel):
    """EN: Logout payload with refresh token to revoke.
    RU: Payload logout с refresh-токеном для отзыва.
    """

    refresh_token: Annotated[str, MinLen(16), MaxLen(4096)]


class PasswordResetRequest(StrictBaseModel):
    """EN: Password reset request payload with email only.
    RU: Payload запроса восстановления пароля только с email.
    """

    email: EmailStr
    channel: Literal["telegram", "email"] = "telegram"


class PasswordResetConfirm(StrictBaseModel):
    """EN: Password reset confirmation payload with code and new password.
    RU: Payload подтверждения восстановления с кодом и новым паролем.
    """

    email: EmailStr
    code: Annotated[str, MinLen(6), MaxLen(6)]
    new_psw: Annotated[str, MinLen(8), MaxLen(72)]

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        """EN: Accept only 6-digit numeric reset code.
        RU: Принимать только 6-значный цифровой reset-код.
        """

        if not value.isdigit():
            raise ValueError("FORMAT")
        return value

    @field_validator("new_psw")
    @classmethod
    def validate_new_psw(cls, value: str) -> str:
        """EN: Reject control characters in new password input.
        RU: Запретить управляющие символы во входном новом пароле.
        """

        return reject_control_chars(value)


class TelegramLinkConfirmRequest(StrictBaseModel):
    """EN: Telegram bot confirmation payload with one-time link code and telegram user id.
    RU: Payload подтверждения от Telegram-бота с одноразовым кодом привязки и telegram user id.
    """

    code: Annotated[str, MinLen(6), MaxLen(6)]
    telegram_user_id: int = Field(gt=0)

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        """EN: Accept only 6-digit numeric link code.
        RU: Принимать только 6-значный цифровой код привязки.
        """

        if not value.isdigit():
            raise ValueError("FORMAT")
        return value


class TelegramLinkRequest(StrictBaseModel):
    """EN: Telegram deep-link request payload with authenticated user id.
    RU: Payload запроса deep-link для Telegram с идентификатором авторизованного пользователя.
    """

    user_id: int = Field(gt=0)


class TelegramLinkConfirmByCodeRequest(StrictBaseModel):
    """EN: Bot payload to convert pending link_code into one-time confirm_code.
    RU: Payload бота для преобразования pending link_code в одноразовый confirm_code.
    """

    telegram_user_id: int = Field(gt=0)
    link_code: Annotated[str, MinLen(1), MaxLen(128)]
    tg_username: Annotated[str, MaxLen(64)] | None = None


class TelegramVerifyRequest(StrictBaseModel):
    """EN: Telegram verification request payload initiated by app user.
    RU: Payload запроса верификации Telegram, инициируемого пользователем приложения.
    """

    user_id: int = Field(gt=0)


class TelegramVerifySend(StrictBaseModel):
    """EN: Bot-to-API payload for issuing one-time verification code to Telegram user.
    RU: Payload бота в API для выдачи одноразового кода верификации Telegram-пользователю.
    """

    request_id: Annotated[str, MinLen(10), MaxLen(32)]
    telegram_user_id: int = Field(gt=0)
    bot_secret: Annotated[str, MinLen(1), MaxLen(256)]


class TelegramVerifyConfirm(StrictBaseModel):
    """EN: Telegram verification confirmation payload with request_id and 6-digit code.
    RU: Payload подтверждения Telegram-верификации с request_id и 6-значным кодом.
    """

    user_id: int = Field(gt=0)
    request_id: Annotated[str, MinLen(10), MaxLen(32)]
    code: Annotated[str, MinLen(6), MaxLen(6)]

    @field_validator("code")
    @classmethod
    def validate_verify_code(cls, value: str) -> str:
        """EN: Accept only numeric 6-digit verification code.
        RU: Принимать только цифровой 6-значный код верификации.
        """

        if not value.isdigit():
            raise ValueError("FORMAT")
        return value


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


class AntiCheatWindow(StrictBaseModel):
    """EN: One score/time window item used for server-side fast anti-cheat checks.
    RU: Один элемент окна score/time для серверной проверки быстрого античита.
    """

    delta_score: int = Field(ge=0)
    delta_sec: float = Field(gt=0)


class GameSessionFinishRequest(StrictBaseModel):
    """EN: Raw gameplay metrics payload submitted at SIS finish.
    RU: Payload сырых игровых метрик, отправляемый при завершении СИС.
    """

    user_id: int = Field(gt=0)
    record_sis: int = Field(ge=0)
    record_pure: int = Field(ge=0)
    sis_sec: float = Field(gt=0)
    chis_sec: float = Field(gt=0)
    attempts: int = Field(ge=3)
    reward_clicks: int = Field(ge=0)
    best_life_score: int | None = Field(default=None, ge=0)
    best_game_score: int | None = Field(default=None, ge=0)
    anti_cheat_windows: list[AntiCheatWindow] = Field(default_factory=list, max_length=100)

    @field_validator("record_pure")
    @classmethod
    def validate_record_pure(cls, value: int, info) -> int:
        """EN: Ensure pure record does not exceed SIS record.
        RU: Убедиться, что чистый рекорд не превышает SIS-рекорд.
        """

        record_sis = info.data.get("record_sis")
        if record_sis is not None and int(value) > int(record_sis):
            raise ValueError("FORMAT")
        return int(value)
