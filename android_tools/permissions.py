"""EN: Safe wrappers for Android runtime permissions.
RU: Безопасные обёртки для runtime-разрешений Android.
"""

from typing import Callable


def is_android() -> bool:
    """EN: Check whether the app currently runs on Android.
    RU: Проверить, запущено ли приложение на Android.
    """
    try:
        from kivy.utils import platform as kivy_platform

        return kivy_platform == "android"
    except Exception:
        return False


def request_runtime_permissions(perms: list[str], callback: Callable | None = None) -> bool:
    """EN: Request Android runtime permissions with safe fallbacks.
    RU: Запросить runtime-разрешения Android с безопасными запасными путями.

    EN: Returns True only when the request API is available and invoked.
    RU: Возвращает True только если API запроса доступен и был вызван.
    """
    if not is_android() or not perms:
        return False

    try:
        from android.permissions import request_permissions

        request_permissions(perms, callback)
        return True
    except Exception:
        return False


def check_permission_safe(permission: str) -> bool:
    """EN: Safely check a single Android permission state.
    RU: Безопасно проверить состояние одного разрешения Android.

    EN: Returns False on non-Android platforms or when APIs are unavailable.
    RU: Возвращает False на не-Android платформах или при недоступности API.
    """
    if not is_android() or not permission:
        return False

    try:
        from android.permissions import check_permission

        return bool(check_permission(permission))
    except Exception:
        return False
