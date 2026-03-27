"""EN: Tests for server-side Telegram Mini App initData validation.
RU: Тесты серверной проверки Telegram Mini App initData.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from urllib.parse import urlencode

import pytest

from server.security.telegram_miniapp import TelegramMiniAppValidationError, validate_telegram_miniapp_init_data


def _signed_init_data(bot_token: str, *, user_id: int = 77, start_param: str = "opaque-start", auth_date: int | None = None) -> str:
    """EN: Build minimal signed Telegram Mini App initData fixture.
    RU: Собрать минимальный подписанный fixture Telegram Mini App initData.
    """

    auth_value = int(auth_date or int(datetime.now(timezone.utc).timestamp()))
    payload = {
        "auth_date": str(auth_value),
        "query_id": "AAEAAAE",
        "start_param": start_param,
        "user": json.dumps({"id": int(user_id), "username": "demo_user"}, separators=(",", ":")),
    }
    data_check_string = "\n".join(f"{key}={payload[key]}" for key in sorted(payload))
    secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    payload["hash"] = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    return urlencode(payload)


def test_validate_telegram_miniapp_init_data_accepts_valid_payload() -> None:
    """EN: Valid signed initData must return normalized Telegram payload.
    RU: Валидный подписанный initData должен возвращать нормализованный Telegram payload.
    """

    raw = _signed_init_data("123456:TEST_PAY_BOT_TOKEN")
    result = validate_telegram_miniapp_init_data(raw, "123456:TEST_PAY_BOT_TOKEN", max_age_sec=300)

    assert result.user["id"] == 77
    assert result.user["username"] == "demo_user"
    assert result.start_param == "opaque-start"


def test_validate_telegram_miniapp_init_data_rejects_expired_auth_date() -> None:
    """EN: Expired Telegram auth_date must be rejected.
    RU: Истекший Telegram auth_date должен отклоняться.
    """

    expired_auth_date = int(datetime.now(timezone.utc).timestamp()) - 3600
    raw = _signed_init_data("123456:TEST_PAY_BOT_TOKEN", auth_date=expired_auth_date)

    with pytest.raises(TelegramMiniAppValidationError) as exc_info:
        validate_telegram_miniapp_init_data(raw, "123456:TEST_PAY_BOT_TOKEN", max_age_sec=300)

    assert exc_info.value.error_code == "INITDATA_EXPIRED"
