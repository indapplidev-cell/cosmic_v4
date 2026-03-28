"""EN: Endpoint tests for internal payout request creation auth and payload passthrough.
RU: Endpoint-тесты авторизации и passthrough payload для создания внутреннего payout request.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from server.api.main import app
from server.security.jwt import create_access_token


def _auth_headers(user_id: int) -> dict[str, str]:
    """EN: Build Authorization header for protected payout request endpoint tests.
    RU: Сформировать Authorization header для тестов защищённого payout request endpoint.
    """

    token = create_access_token(user_id=user_id, email=f"user{user_id}@test.com")
    return {"Authorization": f"Bearer {token}"}


def _error_code(body: dict) -> str | None:
    """EN: Extract stable business error code from normal or FastAPI error payloads.
    RU: Извлечь стабильный business error code из обычного или FastAPI error-payload.
    """

    if isinstance(body.get("detail"), dict):
        return str(body["detail"].get("error") or "")
    return str(body.get("error") or "")


def test_payout_request_create_forbids_foreign_user(monkeypatch) -> None:
    """EN: Protected payout request endpoint must reject user_id spoofing for another account.
    RU: Защищённый payout request endpoint должен отклонять spoofing user_id другого аккаунта.
    """

    called = {"value": False}

    def _fake_create_payout_request(user_id: int, amount: float, wallet_address: str) -> dict:
        called["value"] = True
        return {"ok": True}

    monkeypatch.setattr("server.api.main.create_payout_request", _fake_create_payout_request)

    client = TestClient(app)
    response = client.post(
        "/payout/request/create",
        json={"user_id": 2, "amount": 1.5, "wallet_address": "TWallet123"},
        headers=_auth_headers(1),
    )

    assert response.status_code == 403
    assert _error_code(response.json()) == "FORBIDDEN"
    assert called["value"] is False


def test_payout_request_create_passes_through_service_result(monkeypatch) -> None:
    """EN: Protected payout request endpoint must return the service payload for the authenticated user.
    RU: Защищённый payout request endpoint должен возвращать payload сервиса для авторизованного пользователя.
    """

    def _fake_create_payout_request(user_id: int, amount: float, wallet_address: str) -> dict:
        assert int(user_id) == 7
        assert float(amount) == 2.5
        assert wallet_address == "TWallet123"
        return {
            "ok": True,
            "payout_request_id": 44,
            "status": "reserved",
            "amount": 2.5,
            "asset_code": "USDT",
            "available_balance": 7.5,
            "reserved_balance": 3.5,
        }

    monkeypatch.setattr("server.api.main.create_payout_request", _fake_create_payout_request)

    client = TestClient(app)
    response = client.post(
        "/payout/request/create",
        json={"user_id": 7, "amount": 2.5, "wallet_address": "TWallet123"},
        headers=_auth_headers(7),
    )

    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert response.json()["payout_request_id"] == 44
    assert response.json()["status"] == "reserved"


def test_payout_request_create_invalid_amount_returns_domain_error_not_422(monkeypatch) -> None:
    """EN: Invalid payout amount must reach the service contract and return PAYOUT_AMOUNT_INVALID instead of schema 422.
    RU: Невалидная payout amount должна доходить до сервисного контракта и возвращать PAYOUT_AMOUNT_INVALID вместо schema 422.
    """

    calls: list[tuple[int, object, str]] = []

    def _fake_create_payout_request(user_id: int, amount: object, wallet_address: str) -> dict:
        calls.append((int(user_id), amount, wallet_address))
        return {"ok": False, "error": "PAYOUT_AMOUNT_INVALID"}

    monkeypatch.setattr("server.api.main.create_payout_request", _fake_create_payout_request)

    client = TestClient(app)
    response = client.post(
        "/payout/request/create",
        json={"user_id": 7, "amount": "oops", "wallet_address": "TWallet123"},
        headers=_auth_headers(7),
    )

    assert response.status_code == 200
    assert response.json() == {"ok": False, "error": "PAYOUT_AMOUNT_INVALID"}
    assert calls == [(7, "oops", "TWallet123")]
