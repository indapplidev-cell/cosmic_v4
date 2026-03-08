"""EN: API tests for POST /game/session/finish endpoint shape and validation.
RU: API-тесты формы ответа и валидации endpoint POST /game/session/finish.
"""

from __future__ import annotations

import os

from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/game_galaxy")

from server.api.main import app


def _valid_payload() -> dict:
    """EN: Build minimal valid payload for session finish endpoint.
    RU: Сформировать минимальный валидный payload для endpoint завершения сессии.
    """

    return {
        "user_id": 1,
        "record_sis": 30,
        "record_pure": 20,
        "sis_sec": 20.0,
        "chis_sec": 12.0,
        "attempts": 3,
        "reward_clicks": 0,
        "best_life_score": 15,
        "best_game_score": 30,
        "anti_cheat_windows": [{"delta_score": 20, "delta_sec": 2.0}],
    }


def test_finish_endpoint_ok(monkeypatch) -> None:
    """EN: Endpoint must return business payload from service on valid request.
    RU: Endpoint должен вернуть бизнес-payload сервиса при валидном запросе.
    """

    def _fake_apply_finished_session(user_id: int, metrics: dict) -> dict:
        assert user_id == 1
        assert int(metrics["record_sis"]) == 30
        return {"ok": True, "cheat": False, "record": 40, "rating": 500, "balance": 1.234}

    monkeypatch.setattr("server.api.main.apply_finished_session", _fake_apply_finished_session)

    client = TestClient(app)
    response = client.post("/game/session/finish", json=_valid_payload())
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["cheat"] is False
    assert body["record"] == 40


def test_finish_endpoint_validation_422() -> None:
    """EN: Endpoint must reject invalid metrics with 422.
    RU: Endpoint должен отклонять невалидные метрики кодом 422.
    """

    payload = _valid_payload()
    payload["attempts"] = 1
    client = TestClient(app)
    response = client.post("/game/session/finish", json=payload)
    assert response.status_code == 422
