"""EN: Tests for centralized client auth retry flow on protected snapshot requests.
RU: Тесты централизованного client auth retry-flow для защищённых snapshot-запросов.
"""

from __future__ import annotations

from manager import auth_backend


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
