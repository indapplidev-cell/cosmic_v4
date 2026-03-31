"""EN: Tests for shared Telegram hub API endpoints and canonical Mini App frontend contract.
RU: Тесты общих API endpoint-ов Telegram hub и канонического контракта Mini App frontend.
"""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from server.api.main import app
from server.security.jwt import create_access_token


def _auth_headers(user_id: int) -> dict[str, str]:
    """EN: Build Authorization header for a given test user id.
    RU: Сформировать Authorization header для указанного test user id.
    """

    token = create_access_token(user_id=user_id, email=f"user{user_id}@test.com")
    return {"Authorization": f"Bearer {token}"}


def test_hub_session_request_returns_exact_url(monkeypatch) -> None:
    """EN: Hub session request must return exact shared Mini App direct URL.
    RU: Запрос hub session должен возвращать точный direct URL общего Mini App.
    """

    monkeypatch.setattr(
        "server.api.main.request_telegram_hub_session",
        lambda entry_action, auth_user_id=None, requested_user_id=None, email=None: {
            "ok": True,
            "miniapp_url": "https://t.me/escape2mars_bot/escape2mars?startapp=opaque",
            "ttl_sec": 300,
            "short_name": "escape2mars",
        },
    )

    client = TestClient(app)
    response = client.post(
        "/telegram/hub/session/request",
        json={"entry_action": "payout", "user_id": 7},
        headers=_auth_headers(7),
    )

    assert response.status_code == 200
    assert response.json()["miniapp_url"] == "https://t.me/escape2mars_bot/escape2mars?startapp=opaque"


def test_hub_init_passes_through_service(monkeypatch) -> None:
    """EN: Hub init endpoint must expose trusted hub context from service.
    RU: Endpoint hub init должен отдавать доверенный hub context из сервиса.
    """

    monkeypatch.setattr(
        "server.api.main.init_telegram_hub",
        lambda init_data, start_param: {
            "ok": True,
            "hub_token": "hub-token",
            "available_actions": {"verify": True, "reset": True, "payout": True},
            "payout": {"balance": 3.5, "network": "USDT", "linked_wallet": "TWallet123", "limits": {"min_amount": 0.001}},
        },
    )

    client = TestClient(app)
    response = client.post(
        "/telegram/hub/init",
        json={"init_data": "signed-payload", "start_param": "opaque-start"},
    )

    assert response.status_code == 200
    assert response.json()["hub_token"] == "hub-token"
    assert response.json()["payout"]["network"] == "USDT"


def test_hub_init_blocks_direct_bypass(monkeypatch) -> None:
    """EN: Direct Mini App bypass without issued hub session must be blocked.
    RU: Прямой обход Mini App без выданной hub session должен блокироваться.
    """

    monkeypatch.setattr(
        "server.api.main.init_telegram_hub",
        lambda init_data, start_param: {"ok": False, "error": "SESSION_NOT_FOUND"},
    )

    client = TestClient(app)
    response = client.post(
        "/telegram/hub/init",
        json={"init_data": "signed-payload", "start_param": "direct-open"},
    )

    assert response.status_code == 200
    assert response.json() == {"ok": False, "error": "SESSION_NOT_FOUND"}


def test_hub_verify_reset_and_payout_actions_use_hub_token(monkeypatch) -> None:
    """EN: Hub action endpoints must forward trusted hub token to verify/reset/payout services.
    RU: Endpoint-ы hub action должны передавать доверенный hub token в verify/reset/payout сервисы.
    """

    monkeypatch.setattr("server.api.main.telegram_hub_action_verify", lambda hub_token: {"ok": True, "hub_token": hub_token, "telegram_verified": True})
    monkeypatch.setattr("server.api.main.telegram_hub_action_reset", lambda hub_token, new_password: {"ok": True, "hub_token": hub_token, "status": "password_reset"})
    monkeypatch.setattr("server.api.main.telegram_hub_action_payout_context", lambda hub_token: {"ok": True, "hub_token": hub_token, "balance": 4.0, "network": "USDT", "linked_wallet": "TWallet123", "limits": {"min_amount": 0.001}})
    monkeypatch.setattr(
        "server.api.main.telegram_hub_action_payout_confirm",
        lambda hub_token, amount, wallet_address, network: {
            "ok": True,
            "hub_token": hub_token,
            "payout_request_id": 15,
            "network": network,
            "amount": amount,
            "wallet_address": wallet_address,
        },
    )

    client = TestClient(app)

    verify_response = client.post("/telegram/hub/action/verify", json={"hub_token": "hub-token"})
    reset_response = client.post("/telegram/hub/action/reset", json={"hub_token": "hub-token", "new_password": "Qwerty12345!"})
    context_response = client.post("/telegram/hub/action/payout/context", json={"hub_token": "hub-token"})
    confirm_response = client.post(
        "/telegram/hub/action/payout/confirm",
        json={"hub_token": "hub-token", "amount": 1.5, "wallet_address": "TWallet123", "network": "USDT"},
    )

    assert verify_response.json()["hub_token"] == "hub-token"
    assert reset_response.json()["status"] == "password_reset"
    assert context_response.json()["network"] == "USDT"
    assert confirm_response.json()["payout_request_id"] == 15


def test_hub_frontend_uses_hub_routes_and_menu() -> None:
    """EN: Shared Mini App frontend must use hub init/action routes and expose verify/reset/payout menu.
    RU: Общий Mini App frontend должен использовать hub init/action routes и показывать меню verify/reset/payout.
    """

    html = Path("server/static/paybot_miniapp/index.html").read_text(encoding="utf-8")

    assert 'POST /telegram/hub/init' not in html
    assert '/telegram/hub/init' in html
    assert '/telegram/hub/action/verify' in html
    assert '/telegram/hub/action/reset' in html
    assert '/telegram/hub/action/payout/context' in html
    assert '/telegram/hub/action/payout/confirm' in html
    assert "Подтвердить аккаунт телеграм" in html
    assert "Сбросить пароль" in html
    assert "Выплата" in html
    assert "/telegram/payout/miniapp/init" not in html
    assert "/telegram/payout/miniapp/confirm" not in html
