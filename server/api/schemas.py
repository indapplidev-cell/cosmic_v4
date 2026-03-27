"""EN: Pydantic request schemas with strict validation for API input payloads.
RU: Pydantic-схемы запросов со строгой валидацией входных payload API.
"""

from __future__ import annotations

from typing import Annotated, Literal

from annotated_types import MaxLen, MinLen
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

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
    channel: Literal["telegram"] = "telegram"


class PasswordResetConfirm(StrictBaseModel):
    """EN: Password reset confirmation payload with code and new password.
    RU: Payload подтверждения восстановления с кодом и новым паролем.
    """

    email: EmailStr
    confirm_code: Annotated[str, MinLen(6), MaxLen(6)]
    new_password: Annotated[str, MinLen(8), MaxLen(72)]

    @field_validator("confirm_code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        """EN: Accept only 6-digit numeric reset code.
        RU: Принимать только 6-значный цифровой reset-код.
        """

        if not value.isdigit():
            raise ValueError("FORMAT")
        return value

    @field_validator("new_password")
    @classmethod
    def validate_new_psw(cls, value: str) -> str:
        """EN: Reject control characters in new password input.
        RU: Запретить управляющие символы во входном новом пароле.
        """

        return reject_control_chars(value)


class TelegramLinkConfirmRequest(StrictBaseModel):
    """EN: App-side confirmation payload with user_id and one-time confirm_code from bot.
    RU: Payload подтверждения со стороны приложения с user_id и одноразовым confirm_code из бота.
    """

    user_id: int = Field(gt=0)
    confirm_code: str | None = None
    code: str | None = None
    telegram_user_id: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def normalize_code_alias(self):
        """EN: Normalize legacy `code` alias into canonical `confirm_code`.
        RU: Нормализовать legacy-алиас `code` в каноническое поле `confirm_code`.
        """

        confirm_value = str((self.confirm_code or "").strip())
        legacy_value = str((self.code or "").strip())
        normalized = confirm_value or legacy_value
        self.confirm_code = normalized
        return self

    @field_validator("confirm_code")
    @classmethod
    def validate_confirm_code(cls, value: str | None) -> str:
        """EN: Accept only 6-digit numeric confirm code.
        RU: Принимать только 6-значный цифровой confirm-код.
        """

        value = str((value or "").strip())
        if not value.isdigit():
            raise ValueError("FORMAT")
        if len(value) != 6:
            raise ValueError("FORMAT")
        return value


class TelegramLinkRequest(StrictBaseModel):
    """EN: Telegram deep-link request payload with authenticated user id.
    RU: Payload запроса deep-link для Telegram с идентификатором авторизованного пользователя.
    """

    user_id: int = Field(gt=0)


class PayoutLinkRequest(StrictBaseModel):
    """EN: Authenticated payout link request payload.
    RU: Payload авторизованного запроса payout link-кода.
    """

    user_id: int = Field(gt=0)


class PayoutMiniAppSessionRequest(StrictBaseModel):
    """EN: Authenticated request payload for issuing one-time payout Mini App verification session.
    RU: Payload авторизованного запроса на выдачу одноразовой payout Mini App verification-session.
    """

    user_id: int = Field(gt=0)


class TelegramLinkStatusRequest(StrictBaseModel):
    """EN: Authenticated status request for latest Telegram deep-link code.
    RU: Авторизованный запрос статуса последнего Telegram deep-link кода.
    """

    user_id: int = Field(gt=0)


class PayoutLinkStatusRequest(StrictBaseModel):
    """EN: Authenticated status request for latest payout deep-link code.
    RU: Авторизованный запрос статуса последнего payout deep-link кода.
    """

    user_id: int = Field(gt=0)


class PayoutMiniAppSessionStatusRequest(StrictBaseModel):
    """EN: Authenticated request payload for polling current payout Mini App session status.
    RU: Payload авторизованного запроса для polling текущего статуса payout Mini App session.
    """

    user_id: int = Field(gt=0)


class PayoutLinkAckRequest(StrictBaseModel):
    """EN: Paybot acknowledgement payload for one-time payout link code.
    RU: Payload подтверждения paybot для одноразового payout link-кода.
    """

    code: Annotated[str, MinLen(1), MaxLen(128)]
    telegram_user_id: int = Field(gt=0)
    telegram_username: Annotated[str, MaxLen(64)] | None = None


class PayoutMiniAppSessionConfirmRequest(StrictBaseModel):
    """EN: Mini App payload with raw initData and opaque start_param for server-side verification.
    RU: Payload Mini App с raw initData и непрозрачным start_param для серверной проверки.
    """

    init_data_raw: Annotated[str, MinLen(1), MaxLen(8192)]
    start_param: Annotated[str, MinLen(1), MaxLen(128)]


class TelegramLinkConfirmByCodeRequest(StrictBaseModel):
    """EN: Bot payload to convert pending link_code into one-time confirm_code.
    RU: Payload бота для преобразования pending link_code в одноразовый confirm_code.
    """

    telegram_user_id: int = Field(gt=0)
    link_code: Annotated[str, MinLen(1), MaxLen(128)]
    tg_username: Annotated[str, MaxLen(64)] | None = None


class TelegramLinkConfirmLatestRequest(StrictBaseModel):
    """EN: Bot payload for latest pending link confirmation by Telegram identity.
    RU: Payload бота для подтверждения последнего pending link по Telegram-идентичности.
    """

    telegram_user_id: int = Field(gt=0)
    tg_username: Annotated[str, MinLen(1), MaxLen(64)]


class BotResetIssueRequest(StrictBaseModel):
    """EN: Bot payload for issuing 6-digit reset confirm code from reset_link_code.
    RU: Payload бота для выдачи 6-значного reset confirm-кода на основе reset_link_code.
    """

    telegram_user_id: int = Field(gt=0)
    reset_link_code: Annotated[str, MinLen(1), MaxLen(128)]
    tg_username: Annotated[str, MaxLen(64)] | None = None


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


class LevelScoreRecordUpsertRequest(StrictBaseModel):
    """EN: Authenticated payload for one finished run that should update the per-level score record table.
    RU: ??????????????????? payload ?????? ???????????? run, ??????? ?????? ???????? ??????? ???????? ?? ???????.
    """

    level_number: int = Field(ge=1)
    score: int = Field(ge=0)
    elapsed_ms: int = Field(ge=0)
    result: Literal["completed", "lives_fail", "timeout"]
    attempts_used: int | None = Field(default=None, ge=0)
    reward_used: bool


class AdsConfigRequest(StrictBaseModel):
    """EN: Client ads-config request payload describing runtime platform and locale context.
    RU: Payload запроса ads-config от клиента с описанием runtime-платформы и locale-контекста.
    """

    user_id: int = Field(gt=0)
    platform: Annotated[str, MinLen(2), MaxLen(32)]
    app_version: Annotated[str, MaxLen(32)] | None = None
    locale_country: Annotated[str, MinLen(2), MaxLen(8)]
    tz_offset: Annotated[str, MaxLen(8)] | None = None
    device: Annotated[str, MaxLen(128)] | None = None
    screen: Annotated[str, MaxLen(32)] | None = None


class AdsPlacementConfig(StrictBaseModel):
    """EN: Placement-level ads config returned by backend for banner or rewarded slots.
    RU: Конфиг ads на уровне плейсмента, возвращаемый backend для banner или rewarded-слотов.
    """

    enabled: bool
    unit_id: Annotated[str, MinLen(1), MaxLen(256)]
    refresh_sec: int | None = Field(default=None, ge=0)
    cooldown_sec: int | None = Field(default=None, ge=0)
    reward_type: Literal["life"] | None = None
    reward_amount: int | None = Field(default=None, ge=1)


class AdsConfigResponse(StrictBaseModel):
    """EN: Server-side ads mediation response with resolved region, provider, and placements map.
    RU: Ответ серверной ads-медиации с определенными region, provider и картой плейсментов.
    """

    ok: bool
    provider: Literal["admob_mediation", "dummy"]
    region: Literal["CIS", "WORLD"]
    configured: bool
    banner_enabled: bool
    rewarded_enabled: bool
    banner_ad_unit_id: Annotated[str, MaxLen(256)] | None = None
    rewarded_ad_unit_id: Annotated[str, MaxLen(256)] | None = None
    admob_app_id: Annotated[str, MaxLen(256)] | None = None
    refresh_sec: int = Field(ge=0, default=30)
    min_banner_sec: int = Field(ge=0, default=5)
    debug: bool = False
    error: Annotated[str, MaxLen(64)] | None = None


class AdsEventRequest(StrictBaseModel):
    """EN: Authenticated client ads-event payload collected for diagnostics and analytics.
    RU: Authenticated payload ads-события клиента, собираемый для диагностики и аналитики.
    """

    user_id: int = Field(gt=0)
    screen: Annotated[str, MaxLen(32)] | None = None
    placement: Literal["topbar_banner", "rewarded_gameover"]
    event: Literal[
        "banner_attach",
        "banner_detach",
        "rewarded_click",
        "rewarded_request",
        "rewarded_show",
        "rewarded_result",
    ]
    provider: Annotated[str, MinLen(1), MaxLen(32)]
    flow_id: Annotated[str, MaxLen(32)] | None = None
    ok: bool | None = None
    detail: Annotated[str, MaxLen(512)] | None = None
    ts_client: float | None = Field(default=None, ge=0)
    meta: dict[str, object] = Field(default_factory=dict)
    ts: int | None = Field(default=None, ge=0)
    extra: dict[str, object] = Field(default_factory=dict)
