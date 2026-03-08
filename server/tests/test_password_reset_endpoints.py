"""EN: API tests for forgot-password request/confirm endpoints.
RU: API-тесты endpoint'ов запроса/подтверждения восстановления пароля.
"""

from __future__ import annotations

import os

from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/game_galaxy")

from server.api.main import app


def test_password_reset_request_always_ok(monkeypatch) -> None:
    """EN: Request endpoint must return generic success payload.
    RU: Endpoint запроса должен возвращать обобщённый успешный payload.
    """

    def _fake_request(email: str, request_ip: str | None, user_agent: str | None) -> dict:
        assert email == "u@test.com"
        return {"ok": True}

    monkeypatch.setattr("server.api.main.request_password_reset", _fake_request)
    client = TestClient(app)
    response = client.post("/auth/password/reset/request", json={"email": "u@test.com"})
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_password_reset_confirm_invalid_code(monkeypatch) -> None:
    """EN: Confirm endpoint must pass through INVALID_CODE business error.
    RU: Endpoint подтверждения должен возвращать бизнес-ошибку INVALID_CODE.
    """

    def _fake_confirm(email: str, code: str, new_password: str, request_ip: str | None, user_agent: str | None) -> dict:
        assert email == "u@test.com"
        assert code == "123456"
        assert new_password == "Qwerty12345!"
        return {"ok": False, "error": "INVALID_CODE"}

    monkeypatch.setattr("server.api.main.confirm_password_reset", _fake_confirm)
    client = TestClient(app)
    response = client.post(
        "/auth/password/reset/confirm",
        json={"email": "u@test.com", "code": "123456", "new_psw": "Qwerty12345!"},
    )
    assert response.status_code == 200
    assert response.json() == {"ok": False, "error": "INVALID_CODE"}


def test_password_reset_confirm_validation_422() -> None:
    """EN: Confirm endpoint must reject non-digit 6-char code with 422.
    RU: Endpoint подтверждения должен отклонять нецифровой 6-значный код с 422.
    """

    client = TestClient(app)
    response = client.post(
        "/auth/password/reset/confirm",
        json={"email": "u@test.com", "code": "12ab56", "new_psw": "Qwerty12345!"},
    )
    assert response.status_code == 422
