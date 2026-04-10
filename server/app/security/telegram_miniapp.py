"""EN: Server-side Telegram Mini App initData validation helpers.
RU: Хелперы серверной проверки Telegram Mini App initData.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import parse_qsl


class TelegramMiniAppValidationError(Exception):
    """EN: Domain error raised when Telegram Mini App initData validation fails.
    RU: Доменная ошибка, возникающая при неуспешной проверке Telegram Mini App initData.
    """

    def __init__(self, error_code: str) -> None:
        """EN: Store stable machine-readable error code for validation failure.
        RU: Сохранить стабильный машиночитаемый код ошибки проверки.
        """

        super().__init__(error_code)
        self.error_code = str(error_code)


@dataclass(frozen=True)
class TelegramMiniAppPayload:
    """EN: Normalized validated Telegram Mini App payload.
    RU: Нормализованный проверенный payload Telegram Mini App.
    """

    user: dict
    auth_date: int
    start_param: str


def _build_data_check_string(pairs: list[tuple[str, str]]) -> str:
    """EN: Build canonical Telegram data-check-string without the hash field.
    RU: Построить каноническую Telegram data-check-string без поля hash.
    """

    filtered = [(key, value) for key, value in pairs if key != "hash"]
    filtered.sort(key=lambda item: item[0])
    return "\n".join(f"{key}={value}" for key, value in filtered)


def validate_telegram_miniapp_init_data(
    init_data_raw: str,
    bot_token: str,
    *,
    max_age_sec: int = 300,
) -> TelegramMiniAppPayload:
    """EN: Validate raw Telegram WebApp initData via HMAC and return normalized payload.
    RU: Проверить raw Telegram WebApp initData через HMAC и вернуть нормализованный payload.

    EN: The function validates Telegram HMAC signature, ensures `auth_date` freshness,
    and extracts the canonical Telegram user payload and `start_param`.
    RU: Функция проверяет Telegram HMAC-подпись, контролирует свежесть `auth_date`
    и извлекает канонический Telegram user payload и `start_param`.
    """

    raw_value = str((init_data_raw or "").strip())
    token_value = str((bot_token or "").strip())
    if not raw_value or not token_value:
        raise TelegramMiniAppValidationError("INITDATA_INVALID")

    pairs = parse_qsl(raw_value, keep_blank_values=True)
    payload_map = dict(pairs)
    provided_hash = str(payload_map.get("hash") or "").strip()
    if not provided_hash:
        raise TelegramMiniAppValidationError("INITDATA_HASH_MISSING")

    data_check_string = _build_data_check_string(pairs)
    secret_key = hmac.new(b"WebAppData", token_value.encode("utf-8"), hashlib.sha256).digest()
    expected_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected_hash, provided_hash):
        raise TelegramMiniAppValidationError("INITDATA_INVALID")

    raw_auth_date = str(payload_map.get("auth_date") or "").strip()
    try:
        auth_date = int(raw_auth_date)
    except Exception as exc:
        raise TelegramMiniAppValidationError("INITDATA_AUTH_DATE_INVALID") from exc

    now_ts = int(datetime.now(timezone.utc).timestamp())
    if auth_date <= 0 or auth_date > now_ts + 30 or now_ts - auth_date > int(max_age_sec):
        raise TelegramMiniAppValidationError("INITDATA_EXPIRED")

    user_raw = str(payload_map.get("user") or "").strip()
    if not user_raw:
        raise TelegramMiniAppValidationError("TELEGRAM_USER_MISSING")

    try:
        user_payload = json.loads(user_raw)
    except Exception as exc:
        raise TelegramMiniAppValidationError("TELEGRAM_USER_INVALID") from exc

    if not isinstance(user_payload, dict):
        raise TelegramMiniAppValidationError("TELEGRAM_USER_INVALID")

    raw_user_id = user_payload.get("id")
    try:
        telegram_user_id = int(raw_user_id)
    except Exception as exc:
        raise TelegramMiniAppValidationError("TELEGRAM_USER_ID_MISSING") from exc

    if telegram_user_id <= 0:
        raise TelegramMiniAppValidationError("TELEGRAM_USER_ID_MISSING")
    user_payload["id"] = telegram_user_id

    start_param = str((payload_map.get("start_param") or "").strip())
    if not start_param:
        raise TelegramMiniAppValidationError("START_PARAM_MISSING")

    return TelegramMiniAppPayload(user=user_payload, auth_date=auth_date, start_param=start_param)
