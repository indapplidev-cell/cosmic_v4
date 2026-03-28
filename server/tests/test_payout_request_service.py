"""EN: Service tests for internal payout request creation with reserve-only flow.
RU: Service-тесты создания внутреннего payout request с reserve-only flow.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass

from server.models.payout_request import PayoutRequest
from server.models.profile_game import ProfileGame
from server.services import payout_request_service


@dataclass
class _State:
    """EN: Mutable in-memory state for payout request service tests.
    RU: Изменяемое in-memory состояние для тестов payout request service.
    """

    profile_game: ProfileGame | None
    user_exists: bool = True
    requests: list[PayoutRequest] | None = None

    def __post_init__(self) -> None:
        if self.requests is None:
            self.requests = []


class _FakeSession:
    """EN: Minimal fake session used to test reserve contract without real DB.
    RU: Минимальная fake session для проверки reserve-контракта без реальной БД.
    """

    def __init__(self, state: _State) -> None:
        self._state = state

    def get(self, _model, _pk: int):
        return object() if self._state.user_exists else None

    def add(self, obj) -> None:
        if isinstance(obj, PayoutRequest):
            obj.id = len(self._state.requests or []) + 1
            self._state.requests.append(obj)
        elif isinstance(obj, ProfileGame):
            self._state.profile_game = obj

    def flush(self) -> None:
        return None


def _fake_get_session(state: _State):
    """EN: Provide fake transactional context manager for payout request service tests.
    RU: Вернуть fake транзакционный context manager для тестов payout request service.
    """

    @contextmanager
    def _ctx():
        yield _FakeSession(state)

    return _ctx


def test_create_payout_request_happy_path_consumes_session_and_reserves_balance(monkeypatch) -> None:
    """EN: Happy path must consume verified session, reserve balance, and persist one payout request.
    RU: Happy path должен consume verified session, зарезервировать баланс и сохранить один payout request.
    """

    state = _State(profile_game=ProfileGame(user_id=7, balance=10, reserved_balance=1))
    consume_calls: list[int] = []
    monkeypatch.setattr(payout_request_service, "get_session", _fake_get_session(state))
    monkeypatch.setattr(payout_request_service, "_ensure_profile_game_locked", lambda session, user_id: state.profile_game)
    monkeypatch.setattr(
        payout_request_service,
        "consume_verified_payout_miniapp_session_in_session",
        lambda session, user_id: consume_calls.append(int(user_id)) or {
            "ok": True,
            "miniapp_session_id": 44,
            "telegram_user_id": 555,
        },
    )

    result = payout_request_service.create_payout_request(7, 2.5, "TWallet123")

    assert result["ok"] is True
    assert result["status"] == "reserved"
    assert result["available_balance"] == 7.5
    assert result["reserved_balance"] == 3.5
    assert consume_calls == [7]
    assert len(state.requests) == 1
    assert state.requests[0].telegram_user_id == 555
    assert float(state.requests[0].amount) == 2.5
    assert state.requests[0].status == "reserved"
    assert state.requests[0].miniapp_session_id == 44


def test_create_payout_request_rejects_insufficient_balance_without_mutation(monkeypatch) -> None:
    """EN: Insufficient balance must reject before consume and leave balance/request state unchanged.
    RU: Недостаточный баланс должен отклоняться до consume и не менять balance/request state.
    """

    state = _State(profile_game=ProfileGame(user_id=7, balance=1, reserved_balance=0))
    consume_calls: list[int] = []
    monkeypatch.setattr(payout_request_service, "get_session", _fake_get_session(state))
    monkeypatch.setattr(payout_request_service, "_ensure_profile_game_locked", lambda session, user_id: state.profile_game)
    monkeypatch.setattr(
        payout_request_service,
        "consume_verified_payout_miniapp_session_in_session",
        lambda session, user_id: consume_calls.append(int(user_id)) or {"ok": True},
    )

    result = payout_request_service.create_payout_request(7, 2.5, "TWallet123")

    assert result == {"ok": False, "error": "BALANCE_INSUFFICIENT"}
    assert consume_calls == []
    assert float(state.profile_game.balance) == 1.0
    assert float(state.profile_game.reserved_balance or 0) == 0.0
    assert state.requests == []


def test_create_payout_request_second_call_fails_after_session_consume(monkeypatch) -> None:
    """EN: Reusing the same verification state must not create a second reserved payout request.
    RU: Повторное использование того же verification state не должно создавать второй reserved payout request.
    """

    state = _State(profile_game=ProfileGame(user_id=7, balance=10, reserved_balance=0))
    consume_results = [
        {"ok": True, "miniapp_session_id": 44, "telegram_user_id": 555},
        {"ok": False, "error": "SESSION_CONSUMED"},
    ]
    monkeypatch.setattr(payout_request_service, "get_session", _fake_get_session(state))
    monkeypatch.setattr(payout_request_service, "_ensure_profile_game_locked", lambda session, user_id: state.profile_game)
    monkeypatch.setattr(
        payout_request_service,
        "consume_verified_payout_miniapp_session_in_session",
        lambda session, user_id: consume_results.pop(0),
    )

    first = payout_request_service.create_payout_request(7, 2, "TWallet123")
    second = payout_request_service.create_payout_request(7, 2, "TWallet123")

    assert first["ok"] is True
    assert second == {"ok": False, "error": "SESSION_CONSUMED"}
    assert len(state.requests) == 1
    assert float(state.profile_game.balance) == 8.0
    assert float(state.profile_game.reserved_balance) == 2.0


def test_create_payout_request_rejects_invalid_wallet_without_mutation(monkeypatch) -> None:
    """EN: Invalid wallet must reject without consume, reserve, or payout request creation.
    RU: Невалидный wallet должен отклоняться без consume, reserve и создания payout request.
    """

    state = _State(profile_game=ProfileGame(user_id=7, balance=10, reserved_balance=0))
    consume_calls: list[int] = []
    monkeypatch.setattr(payout_request_service, "get_session", _fake_get_session(state))
    monkeypatch.setattr(
        payout_request_service,
        "consume_verified_payout_miniapp_session_in_session",
        lambda session, user_id: consume_calls.append(int(user_id)) or {"ok": True},
    )

    result = payout_request_service.create_payout_request(7, 2, "bad wallet with spaces")

    assert result == {"ok": False, "error": "PAYOUT_WALLET_ADDRESS_INVALID"}
    assert consume_calls == []
    assert state.requests == []


def test_create_payout_request_rejects_invalid_amount_without_mutation(monkeypatch) -> None:
    """EN: Invalid payout amount must reject before consume and reserve.
    RU: Невалидная payout amount должна отклоняться до consume и reserve.
    """

    state = _State(profile_game=ProfileGame(user_id=7, balance=10, reserved_balance=0))
    consume_calls: list[int] = []
    monkeypatch.setattr(payout_request_service, "get_session", _fake_get_session(state))
    monkeypatch.setattr(
        payout_request_service,
        "consume_verified_payout_miniapp_session_in_session",
        lambda session, user_id: consume_calls.append(int(user_id)) or {"ok": True},
    )

    result = payout_request_service.create_payout_request(7, 0, "TWallet123")

    assert result == {"ok": False, "error": "PAYOUT_AMOUNT_INVALID"}
    assert consume_calls == []
    assert state.requests == []
