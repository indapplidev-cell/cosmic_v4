"""EN: Tests for centralized client auth retry flow on protected snapshot requests.
RU: Тесты централизованного client auth retry-flow для защищённых snapshot-запросов.
"""

from __future__ import annotations

from manager import auth_backend
from manager.modes.survive_timed.runtime_bridge import SurviveTimedRuntimeBridge

import data.gameplay.modes.survive_timed.local_level_progress_store as progress_store
import data.gameplay.modes.survive_timed.local_level_result_store as result_store


def _bind_survive_timed_storage(monkeypatch, tmp_path):
    class _App:
        def __init__(self, user_data_dir: str) -> None:
            self.user_data_dir = user_data_dir

    app = _App(str(tmp_path))
    monkeypatch.setattr(progress_store.App, "get_running_app", staticmethod(lambda: app))
    monkeypatch.setattr(result_store.App, "get_running_app", staticmethod(lambda: app))
    return app


def test_get_current_user_snapshot_refreshes_and_retries_on_unauthorized(monkeypatch) -> None:
    """EN: Protected /auth/me must refresh expired access token and retry once before failing session restore.
    RU: Защищённый /auth/me должен обновлять истёкший access token и делать один retry до отказа startup-восстановления сессии.
    """

    calls: list[dict] = []

    monkeypatch.setattr(auth_backend, "_ensure_healthcheck_once", lambda: None)
    monkeypatch.setattr(auth_backend, "has_valid_session", lambda cache=None: True)
    monkeypatch.setattr(auth_backend, "ensure_access_token", lambda force_refresh=False: "expired-access")
    monkeypatch.setattr(auth_backend, "get_refresh_token", lambda: "refresh-token")
    monkeypatch.setattr(auth_backend, "get_session_user_id", lambda cache=None: 7)
    monkeypatch.setattr(auth_backend, "refresh_access_token", lambda: True)
    monkeypatch.setattr(auth_backend, "get_access_token", lambda: "fresh-access")
    monkeypatch.setattr(auth_backend, "force_logout", lambda reason="UNKNOWN": None)

    def _fake_request_with_meta(method: str, path: str, **kwargs):
        calls.append({"method": method, "path": path, "headers": dict(kwargs.get("headers") or {})})
        if len(calls) == 1:
            return False, {"ok": False, "error": "UNAUTHORIZED"}, 401
        return True, {"ok": True, "user": {"user_id": 7, "email": "user7@test.com"}}, 200

    monkeypatch.setattr(auth_backend.api_client, "request_with_meta", _fake_request_with_meta)

    ok, payload = auth_backend.get_current_user_snapshot(timeout=5)

    assert ok is True
    assert payload["ok"] is True
    assert payload["user"]["user_id"] == 7
    assert len(calls) == 2
    assert calls[0]["path"] == "/auth/me"
    assert calls[0]["headers"]["Authorization"] == "Bearer expired-access"
    assert calls[1]["headers"]["Authorization"] == "Bearer fresh-access"


def test_get_current_user_snapshot_falls_back_to_legacy_query_user_id(monkeypatch) -> None:
    """EN: Startup snapshot must retry `/auth/me` with cached query `user_id` for legacy backend contracts returning 422.
    RU: Startup-snapshot должен повторять `/auth/me` с query `user_id` из кэша для legacy backend-контрактов, возвращающих 422.
    """

    calls: list[dict] = []

    monkeypatch.setattr(auth_backend, "_ensure_healthcheck_once", lambda: None)
    monkeypatch.setattr(auth_backend, "has_valid_session", lambda cache=None: True)
    monkeypatch.setattr(auth_backend, "ensure_access_token", lambda force_refresh=False: "access-token")
    monkeypatch.setattr(auth_backend, "get_refresh_token", lambda: "refresh-token")
    monkeypatch.setattr(auth_backend, "get_session_user_id", lambda cache=None: 7)

    def _fake_request_with_meta(method: str, path: str, **kwargs):
        calls.append(
            {
                "method": method,
                "path": path,
                "params": dict(kwargs.get("params") or {}),
                "headers": dict(kwargs.get("headers") or {}),
            }
        )
        if len(calls) == 1:
            return False, {"detail": [{"loc": ["query", "user_id"], "msg": "Field required", "type": "missing"}]}, 422
        return True, {"ok": True, "user": {"user_id": 7, "email": "user7@test.com"}}, 200

    monkeypatch.setattr(auth_backend.api_client, "request_with_meta", _fake_request_with_meta)

    ok, payload = auth_backend.get_current_user_snapshot(timeout=5)

    assert ok is True
    assert payload["ok"] is True
    assert payload["user"]["user_id"] == 7
    assert len(calls) == 2
    assert calls[0]["path"] == "/auth/me"
    assert calls[0]["params"] == {}
    assert calls[1]["path"] == "/auth/me"
    assert calls[1]["params"] == {"user_id": 7}


def test_hydrate_survive_timed_progress_overwrites_local_store_from_server(monkeypatch, tmp_path) -> None:
    """EN: Hydrate must replace divergent local survive_timed progress with the backend snapshot.
    RU: Hydrate должен перезаписывать расходящийся локальный survive_timed progress snapshot-ом backend.
    """

    _bind_survive_timed_storage(monkeypatch, tmp_path)
    progress_store.save_campaign_progress(
        {
            "last_completed_level_number": 7,
            "current_level_number": 8,
            "campaign_completed": False,
        }
    )

    monkeypatch.setattr(auth_backend, "has_valid_session", lambda cache=None: True)
    monkeypatch.setattr(
        auth_backend,
        "get_survive_timed_progress",
        lambda timeout=10: (
            True,
            {
                "ok": True,
                "progress": {
                    "last_completed_level_number": 3,
                    "current_level_number": 4,
                    "campaign_completed": False,
                    "updated_at": "2026-04-02T10:00:00Z",
                },
            },
        ),
    )

    ok = auth_backend.hydrate_survive_timed_progress(timeout=5)
    stored = progress_store.load_campaign_progress()

    assert ok is True
    assert stored == {
        "last_completed_level_number": 3,
        "current_level_number": 4,
        "campaign_completed": False,
        "updated_at": "2026-04-02T10:00:00Z",
    }


def test_authorized_success_uses_server_snapshot_before_any_local_progression(monkeypatch, tmp_path) -> None:
    """EN: Authorized success must not mutate local survive_timed state before backend returns authoritative result/progress.
    RU: Авторизованный success не должен менять локальный survive_timed state до server-authoritative ответа backend.
    """

    _bind_survive_timed_storage(monkeypatch, tmp_path)
    progress_store.save_campaign_progress(
        {
            "last_completed_level_number": 7,
            "current_level_number": 8,
            "campaign_completed": False,
        }
    )
    result_store.save_level_results(
        {
            "levels": {
                "2": {
                    "best_survival_sec": 99.0,
                    "last_survival_sec": 99.0,
                    "attempts_count": 9,
                    "completed_count": 9,
                    "last_result": "success",
                }
            }
        }
    )

    bridge = SurviveTimedRuntimeBridge()
    profile = bridge.activate_level(2)
    bridge.begin_run()
    monkeypatch.setattr(bridge, "get_elapsed_sec", lambda: float(profile.target_survival_sec))
    monkeypatch.setattr(auth_backend, "has_valid_session", lambda cache=None: True)

    def _submit_success(payload: dict, timeout: int = 10):
        assert payload["level_number"] == 2
        assert progress_store.load_campaign_progress()["current_level_number"] == 8
        assert result_store.load_level_results()["levels"]["2"]["attempts_count"] == 9
        return True, {
            "ok": True,
            "result": {
                "level_number": 2,
                "best_survival_ms": 60000,
                "last_survival_ms": 60000,
                "attempts_count": 1,
                "completed_count": 1,
                "last_result": "success",
                "updated_at": "2026-04-02T11:00:00Z",
            },
            "progress": {
                "last_completed_level_number": 2,
                "current_level_number": 3,
                "campaign_completed": False,
                "updated_at": "2026-04-02T11:00:01Z",
            },
        }

    monkeypatch.setattr(auth_backend, "submit_survive_timed_level_success", _submit_success)

    response = bridge.record_success()

    assert response["ok"] is True
    assert response["progress"]["current_level_number"] == 3
    assert progress_store.load_campaign_progress() == {
        "last_completed_level_number": 2,
        "current_level_number": 3,
        "campaign_completed": False,
        "updated_at": "2026-04-02T11:00:01Z",
    }
    assert result_store.load_level_results() == {
        "levels": {
            "2": {
                "best_survival_sec": 60.0,
                "last_survival_sec": 60.0,
                "attempts_count": 1,
                "completed_count": 1,
                "last_result": "success",
            }
        },
        "updated_at": "2026-04-02T11:00:00Z",
    }


def test_authorized_fail_uses_server_snapshot_without_local_attempt_increment(monkeypatch, tmp_path) -> None:
    """EN: Authorized fail must not increment attempts locally before backend returns authoritative result.
    RU: Авторизованный fail не должен инкрементить локальные attempts до server-authoritative ответа backend.
    """

    _bind_survive_timed_storage(monkeypatch, tmp_path)
    progress_store.save_campaign_progress(
        {
            "last_completed_level_number": 4,
            "current_level_number": 5,
            "campaign_completed": False,
        }
    )
    result_store.save_level_results(
        {
            "levels": {
                "5": {
                    "best_survival_sec": 45.0,
                    "last_survival_sec": 40.0,
                    "attempts_count": 7,
                    "completed_count": 2,
                    "last_result": "fail",
                }
            }
        }
    )

    bridge = SurviveTimedRuntimeBridge()
    profile = bridge.activate_level(5)
    bridge.begin_run()
    monkeypatch.setattr(bridge, "get_elapsed_sec", lambda: 17.0)
    monkeypatch.setattr(auth_backend, "has_valid_session", lambda cache=None: True)

    def _submit_fail(payload: dict, timeout: int = 10):
        assert payload == {"level_number": 5, "survival_ms": 17000, "result": "fail"}
        assert result_store.load_level_results()["levels"]["5"]["attempts_count"] == 7
        assert progress_store.load_campaign_progress()["current_level_number"] == 5
        return True, {
            "ok": True,
            "result": {
                "level_number": 5,
                "best_survival_ms": 45000,
                "last_survival_ms": 17000,
                "attempts_count": 2,
                "completed_count": 0,
                "last_result": "fail",
                "updated_at": "2026-04-02T12:00:00Z",
            },
        }

    monkeypatch.setattr(auth_backend, "submit_survive_timed_level_result", _submit_fail)

    response = bridge.record_fail()

    assert response["ok"] is True
    assert progress_store.load_campaign_progress()["current_level_number"] == 5
    assert result_store.load_level_results() == {
        "levels": {
            "5": {
                "best_survival_sec": 45.0,
                "last_survival_sec": 17.0,
                "attempts_count": 2,
                "completed_count": 0,
                "last_result": "fail",
            }
        },
        "updated_at": "2026-04-02T12:00:00Z",
    }


def test_guest_flow_keeps_local_fallback_without_backend_calls(monkeypatch, tmp_path) -> None:
    """EN: Guest/offline survive_timed flow must keep local-only fallback when no valid session exists.
    RU: Guest/offline survive_timed flow должен сохранять local-only fallback без валидной сессии.
    """

    _bind_survive_timed_storage(monkeypatch, tmp_path)
    monkeypatch.setattr(auth_backend, "has_valid_session", lambda cache=None: False)
    monkeypatch.setattr(
        auth_backend,
        "submit_survive_timed_level_success",
        lambda payload, timeout=10: (_ for _ in ()).throw(AssertionError("authorized success submit must not be called")),
    )
    monkeypatch.setattr(
        auth_backend,
        "submit_survive_timed_level_result",
        lambda payload, timeout=10: (_ for _ in ()).throw(AssertionError("authorized fail submit must not be called")),
    )

    success_bridge = SurviveTimedRuntimeBridge()
    success_profile = success_bridge.activate_level(1)
    success_bridge.begin_run()
    monkeypatch.setattr(success_bridge, "get_elapsed_sec", lambda: float(success_profile.target_survival_sec))

    success_response = success_bridge.record_success()

    assert success_response["ok"] is True
    assert progress_store.load_campaign_progress()["current_level_number"] == 2
    assert result_store.load_level_results()["levels"]["1"]["completed_count"] == 1

    fail_bridge = SurviveTimedRuntimeBridge()
    fail_bridge.activate_level(2)
    fail_bridge.begin_run()
    monkeypatch.setattr(fail_bridge, "get_elapsed_sec", lambda: 15.0)

    fail_response = fail_bridge.record_fail()

    assert fail_response["ok"] is True
    assert progress_store.load_campaign_progress()["current_level_number"] == 2
    assert result_store.load_level_results()["levels"]["2"] == {
        "best_survival_sec": 15.0,
        "last_survival_sec": 15.0,
        "attempts_count": 1,
        "completed_count": 0,
        "last_result": "fail",
    }
