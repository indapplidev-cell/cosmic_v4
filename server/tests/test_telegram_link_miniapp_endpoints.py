"""EN: Endpoint tests for telegram_link Mini App verification routes and auth boundaries.
RU: Тесты endpoint-ов telegram_link Mini App verification и их auth-границ.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from server.api.main import app
from server.security.jwt import create_access_token


def _auth_headers(user_id: int) -> dict[str, str]:
    """EN: Build Authorization header for a given test user id.
    RU: Сформировать Authorization header для указанного test user id.
    """

    token = create_access_token(user_id=user_id, email=f"user{user_id}@test.com")
    return {"Authorization": f"Bearer {token}"}


def _error_code(body: dict) -> str | None:
    """EN: Extract stable business error code from plain or FastAPI exception response.
    RU: Извлечь стабильный business error code из обычного ответа или FastAPI exception response.
    """

    if isinstance(body.get("detail"), dict):
        return str(body["detail"].get("error") or "")
    return str(body.get("error") or "")


def test_telegram_link_miniapp_request_forbids_foreign_user(monkeypatch) -> None:
    """EN: telegram_link Mini App session request must reject user_id spoofing for another account.
    RU: Запрос telegram_link Mini App session должен отклонять spoofing user_id другого аккаунта.
    """

    called = {"value": False}

    def _fake_request(user_id: int) -> dict:
        called["value"] = True
        return {"ok": True, "miniapp_url": "https://t.me/payprotect_bot/verify?startapp=test", "ttl_sec": 300, "purpose": "telegram_link"}

    monkeypatch.setattr("server.api.main.request_telegram_link_miniapp_session", _fake_request)

    client = TestClient(app)
    response = client.post(
        "/telegram/link/miniapp/session/request",
        json={"user_id": 2},
        headers=_auth_headers(1),
    )
    assert response.status_code == 403
    assert _error_code(response.json()) == "FORBIDDEN"
    assert called["value"] is False


def test_telegram_link_miniapp_confirm_passes_through_service_result(monkeypatch) -> None:
    """EN: Shared Mini App confirm endpoint must pass through telegram_link service result.
    RU: Общий Mini App confirm endpoint должен пропускать результат telegram_link service.
    """

    def _fake_confirm(init_data_raw: str, start_param: str) -> dict:
        assert init_data_raw == "signed-payload"
        assert start_param == "opaque-start"
        return {"ok": True, "user_id": 7, "purpose": "telegram_link", "telegram_user_id": 99}

    monkeypatch.setattr("server.api.main.confirm_telegram_miniapp_session", _fake_confirm)

    client = TestClient(app)
    response = client.post(
        "/telegram/miniapp/session/confirm",
        json={"init_data_raw": "signed-payload", "start_param": "opaque-start"},
    )
    assert response.status_code == 200
    assert response.json() == {"ok": True, "user_id": 7, "purpose": "telegram_link", "telegram_user_id": 99}


def test_telegram_link_miniapp_status_allows_own_user(monkeypatch) -> None:
    """EN: telegram_link Mini App status endpoint must return service payload for the authenticated user.
    RU: Endpoint статуса telegram_link Mini App должен возвращать payload сервиса для авторизованного пользователя.
    """

    def _fake_status(user_id: int) -> dict:
        assert int(user_id) == 3
        return {"ok": True, "verified": True, "status": "verified", "ttl_sec": 120, "expired": False, "purpose": "telegram_link", "telegram_user_id": 555}

    monkeypatch.setattr("server.api.main.get_telegram_link_miniapp_session_status", _fake_status)

    client = TestClient(app)
    response = client.post(
        "/telegram/link/miniapp/session/status",
        json={"user_id": 3},
        headers=_auth_headers(3),
    )
    assert response.status_code == 200
    assert response.json()["verified"] is True
    assert response.json()["purpose"] == "telegram_link"
