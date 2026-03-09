"""EN: Compatibility wrapper for password reset service routed to Telegram channel.
RU: Совместимый враппер сервиса восстановления пароля, направляющий поток в Telegram-канал.
"""

from __future__ import annotations

from server.services.telegram_service import (
    confirm_password_reset as _confirm_password_reset_telegram,
    request_password_reset as _request_password_reset_telegram,
)


def request_password_reset(email: str, request_ip: str | None, user_agent: str | None) -> dict:
    """EN: Request password reset code via Telegram with anti-enumeration response.
    RU: Запросить код восстановления пароля через Telegram с anti-enumeration ответом.
    """

    return _request_password_reset_telegram(
        email=email,
        channel="telegram",
        request_ip=request_ip,
        user_agent=user_agent,
    )


def confirm_password_reset(
    email: str,
    code: str,
    new_password: str,
    request_ip: str | None = None,
    user_agent: str | None = None,
) -> dict:
    """EN: Confirm password reset code and update password hash.
    RU: Подтвердить код восстановления пароля и обновить хеш пароля.
    """

    del request_ip, user_agent
    return _confirm_password_reset_telegram(email=email, code=code, new_password=new_password)

