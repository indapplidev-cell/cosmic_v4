from fastapi.testclient import TestClient

from server.api.main import app


client = TestClient(app)


def test_survive_timed_progress_endpoint(monkeypatch):
    monkeypatch.setattr("server.api.main.get_authenticated_user_id", lambda _request: 42)
    monkeypatch.setattr(
        "server.api.main.get_campaign_progress",
        lambda user_id: {
            "ok": True,
            "progress": {
                "user_id": user_id,
                "last_completed_level_number": 3,
                "current_level_number": 4,
                "campaign_completed": False,
            },
        },
    )

    response = client.get("/game/modes/survive-timed/progress")

    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert response.json()["progress"]["current_level_number"] == 4


def test_survive_timed_level_result_endpoint(monkeypatch):
    monkeypatch.setattr("server.api.main.get_authenticated_user_id", lambda _request: 7)
    monkeypatch.setattr(
        "server.api.main.upsert_level_result",
        lambda user_id, level_number, survival_ms, result: {
            "ok": True,
            "result": {
                "user_id": user_id,
                "level_number": level_number,
                "last_survival_ms": survival_ms,
                "last_result": result,
            },
        },
    )

    response = client.post(
        "/game/modes/survive-timed/level-result",
        json={"level_number": 2, "survival_ms": 55000, "result": "fail"},
    )

    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert response.json()["result"]["last_result"] == "fail"


def test_survive_timed_level_success_endpoint(monkeypatch):
    monkeypatch.setattr("server.api.main.get_authenticated_user_id", lambda _request: 9)
    monkeypatch.setattr(
        "server.api.main.record_survive_timed_level_success",
        lambda user_id, level_number, survival_ms: {
            "ok": True,
            "result": {
                "user_id": user_id,
                "level_number": level_number,
                "last_survival_ms": survival_ms,
                "last_result": "success",
            },
            "progress": {
                "user_id": user_id,
                "last_completed_level_number": level_number,
                "current_level_number": level_number + 1,
                "campaign_completed": False,
            },
        },
    )

    response = client.post(
        "/game/modes/survive-timed/level-success",
        json={"level_number": 4, "survival_ms": 240000},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["result"]["last_result"] == "success"
    assert payload["progress"]["current_level_number"] == 5
