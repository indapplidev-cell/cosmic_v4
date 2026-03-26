"""EN: Tests ensuring Telegram link flow is the only active account-linking runtime path.
RU: Тесты, подтверждающие, что Telegram link-flow является единственным активным runtime-путём привязки аккаунта.
"""

from __future__ import annotations

from server.api.main import app
import manager.auth_backend as auth_backend


def test_api_routes_exclude_telegram_verify_runtime_endpoints() -> None:
    """EN: Runtime API must not expose duplicate `/telegram/verify/*` endpoints.
    RU: Runtime API не должен публиковать дублирующие `/telegram/verify/*` endpoints.
    """

    route_paths = {getattr(route, "path", "") for route in app.routes}
    assert "/telegram/link/request" in route_paths
    assert "/telegram/link/confirm" in route_paths
    assert "/telegram/link/confirm_latest" in route_paths
    assert "/telegram/verify/request" not in route_paths
    assert "/telegram/verify/send" not in route_paths
    assert "/telegram/verify/confirm" not in route_paths


def test_auth_backend_excludes_legacy_telegram_verify_bridge() -> None:
    """EN: Client bridge must keep only telegram_link_* helpers for Telegram account linking.
    RU: Клиентский bridge должен оставлять только telegram_link_* helper-ы для привязки Telegram.
    """

    assert hasattr(auth_backend, "telegram_link_request")
    assert hasattr(auth_backend, "telegram_link_confirm")
    assert not hasattr(auth_backend, "telegram_verify_request")
    assert not hasattr(auth_backend, "telegram_verify_confirm")
