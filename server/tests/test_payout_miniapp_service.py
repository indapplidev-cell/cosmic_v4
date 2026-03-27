"""EN: Focused lifecycle tests for payout Mini App verification service contracts.
RU: Точечные lifecycle-тесты контрактов payout Mini App verification service.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import server.services.payout_miniapp_service as payout_miniapp_service
from server.models.payout_miniapp_session import PayoutMiniAppSession
from server.security.telegram_miniapp import TelegramMiniAppPayload


@dataclass
class _SessionState:
    """EN: Mutable in-memory state for fake payout Mini App service session tests.
    RU: Изменяемое in-memory состояние для fake-тестов payout Mini App service.
    """

    rows: list[PayoutMiniAppSession] = field(default_factory=list)
    account: object | None = None
    user_exists: bool = True


class _FakeTelegramAccount:
    """EN: Minimal existing Telegram account fixture for mismatch tests.
    RU: Минимальный fixture существующего Telegram account для тестов mismatch.
    """

    def __init__(self, telegram_user_id: int) -> None:
        self.telegram_user_id = int(telegram_user_id)


class _FakeSession:
    """EN: Minimal fake SQLAlchemy session for payout Mini App service contract tests.
    RU: Минимальная fake SQLAlchemy session для contract-тестов payout Mini App service.
    """

    def __init__(self, state: _SessionState) -> None:
        self._state = state

    def get(self, _model, _pk: int):
        return object() if self._state.user_exists else None

    def add(self, obj) -> None:
        if isinstance(obj, PayoutMiniAppSession):
            if obj.created_at is None:
                obj.created_at = datetime.now(timezone.utc)
            self._state.rows.append(obj)

    def flush(self) -> None:
        return None

    def execute(self, _statement) -> None:
        return None

    def scalar(self, _statement):
        return self._state.account


def _fake_get_session(state: _SessionState):
    """EN: Build fake context manager returning the same mutable fake session.
    RU: Собрать fake context manager, возвращающий ту же изменяемую fake session.
    """

    @contextmanager
    def _ctx():
        yield _FakeSession(state)

    return _ctx


def _miniapp_payload(*, start_param: str = "opaque-start", user_id: int = 555, username: str = "demo_user") -> TelegramMiniAppPayload:
    """EN: Build normalized Telegram Mini App payload for service tests.
    RU: Собрать нормализованный Telegram Mini App payload для service-тестов.
    """

    return TelegramMiniAppPayload(
        user={"id": int(user_id), "username": username},
        auth_date=int(datetime.now(timezone.utc).timestamp()),
        start_param=start_param,
    )


def _patch_common(monkeypatch, state: _SessionState, *, start_param: str = "opaque-start", payload: TelegramMiniAppPayload | None = None) -> None:
    """EN: Patch common Mini App service dependencies for lifecycle contract tests.
    RU: Замокать общие зависимости Mini App service для lifecycle contract-тестов.
    """

    monkeypatch.setattr(payout_miniapp_service, "get_session", _fake_get_session(state))
    monkeypatch.setattr(payout_miniapp_service, "get_payout_miniapp_session_ttl_sec", lambda: 300)
    monkeypatch.setattr(payout_miniapp_service, "get_payout_miniapp_auth_max_age_sec", lambda: 300)
    monkeypatch.setattr(payout_miniapp_service, "get_pay_bot_token", lambda: "123456:TEST_PAY_BOT_TOKEN")
    monkeypatch.setattr(payout_miniapp_service, "_generate_session_token", lambda: start_param)
    monkeypatch.setattr(
        payout_miniapp_service,
        "_build_miniapp_url",
        lambda token: f"https://t.me/payprotect_bot/verify?startapp={token}",
    )
    monkeypatch.setattr(
        payout_miniapp_service,
        "_load_session_by_token",
        lambda session, token: next((row for row in reversed(state.rows) if row.session_token_hash == payout_miniapp_service._session_token_hash(token)), None),
    )
    monkeypatch.setattr(
        payout_miniapp_service,
        "_load_latest_session_for_user",
        lambda session, user_id: next((row for row in reversed(state.rows) if int(row.user_id) == int(user_id)), None),
    )
    monkeypatch.setattr(
        payout_miniapp_service,
        "validate_telegram_miniapp_init_data",
        lambda init_data_raw, bot_token, max_age_sec=300: payload or _miniapp_payload(start_param=start_param),
    )


def test_payout_miniapp_happy_path_request_confirm_status_and_link(monkeypatch) -> None:
    """EN: Request, confirm and status must complete one verified Mini App lifecycle and call Telegram linkage.
    RU: Request, confirm и status должны завершать один verified Mini App lifecycle и вызывать Telegram linkage.
    """

    state = _SessionState()
    linked_calls: list[dict[str, object]] = []
    _patch_common(monkeypatch, state)
    monkeypatch.setattr(
        payout_miniapp_service,
        "link_or_update_telegram_account",
        lambda session, user_id, telegram_user_id, telegram_username: (
            linked_calls.append(
                {
                    "user_id": int(user_id),
                    "telegram_user_id": int(telegram_user_id),
                    "telegram_username": telegram_username,
                }
            )
            or True,
            None,
        ),
    )

    request_result = payout_miniapp_service.request_payout_miniapp_session(7)
    confirm_result = payout_miniapp_service.confirm_payout_miniapp_session("signed-init-data", "opaque-start")
    status_result = payout_miniapp_service.get_payout_miniapp_session_status(7)

    assert request_result["ok"] is True
    assert request_result["miniapp_url"].endswith("?startapp=opaque-start")
    assert confirm_result == {"ok": True, "user_id": 7, "telegram_user_id": 555}
    assert status_result["verified"] is True
    assert status_result["status"] == "verified"
    assert status_result["telegram_user_id"] == 555
    assert len(linked_calls) == 1
    assert linked_calls[0] == {"user_id": 7, "telegram_user_id": 555, "telegram_username": "demo_user"}


def test_confirm_payout_miniapp_session_rejects_already_verified(monkeypatch) -> None:
    """EN: Repeated Mini App confirm on an already verified session must fail deterministically.
    RU: Повторный Mini App confirm для уже verified session должен стабильно отклоняться.
    """

    now_utc = datetime.now(timezone.utc)
    row = PayoutMiniAppSession(
        user_id=7,
        session_token_hash=payout_miniapp_service._session_token_hash("opaque-start"),
        status="verified",
        expires_at=now_utc + timedelta(minutes=5),
        telegram_user_id=555,
        verified_at=now_utc,
    )
    state = _SessionState(rows=[row])
    _patch_common(monkeypatch, state)

    result = payout_miniapp_service.confirm_payout_miniapp_session("signed-init-data", "opaque-start")

    assert result == {"ok": False, "error": "SESSION_ALREADY_VERIFIED"}


def test_payout_miniapp_status_expires_issued_and_verified_sessions(monkeypatch) -> None:
    """EN: Issued and verified sessions must be downgraded to expired after TTL passes.
    RU: Issued и verified session должны переводиться в expired после истечения TTL.
    """

    past = datetime.now(timezone.utc) - timedelta(minutes=10)
    issued_row = PayoutMiniAppSession(user_id=7, session_token_hash="issued", status="issued", expires_at=past)
    verified_row = PayoutMiniAppSession(
        user_id=7,
        session_token_hash="verified",
        status="verified",
        expires_at=past,
        telegram_user_id=555,
        verified_at=past - timedelta(minutes=1),
    )

    issued_state = _SessionState(rows=[issued_row])
    _patch_common(monkeypatch, issued_state)
    issued_status = payout_miniapp_service.get_payout_miniapp_session_status(7)
    assert issued_status["verified"] is False
    assert issued_status["status"] == "expired"
    assert issued_status["expired"] is True

    verified_state = _SessionState(rows=[verified_row])
    _patch_common(monkeypatch, verified_state)
    verified_status = payout_miniapp_service.get_payout_miniapp_session_status(7)
    assert verified_status["verified"] is False
    assert verified_status["status"] == "expired"
    assert verified_status["expired"] is True


def test_consume_verified_payout_miniapp_session_is_single_use(monkeypatch) -> None:
    """EN: Verified payout Mini App session must be consumable exactly once and then stop acting as verified.
    RU: Verified payout Mini App session должна потребляться ровно один раз и после этого переставать считаться verified.
    """

    now_utc = datetime.now(timezone.utc)
    row = PayoutMiniAppSession(
        user_id=7,
        session_token_hash="opaque-hash",
        status="verified",
        expires_at=now_utc + timedelta(minutes=5),
        telegram_user_id=555,
        telegram_username="demo_user",
        verified_at=now_utc - timedelta(seconds=5),
        tg_auth_date=now_utc - timedelta(seconds=10),
    )
    state = _SessionState(rows=[row])
    _patch_common(monkeypatch, state)

    first = payout_miniapp_service.consume_verified_payout_miniapp_session(7)
    second = payout_miniapp_service.consume_verified_payout_miniapp_session(7)
    status_after = payout_miniapp_service.get_payout_miniapp_session_status(7)

    assert first["ok"] is True
    assert first["status"] == "consumed"
    assert first["telegram_user_id"] == 555
    assert second == {"ok": False, "error": "SESSION_CONSUMED"}
    assert status_after["verified"] is False
    assert status_after["status"] == "consumed"


def test_consume_verified_payout_miniapp_session_rejects_expired_verified(monkeypatch) -> None:
    """EN: Expired verified payout Mini App session must not be consumable.
    RU: Просроченная verified payout Mini App session не должна потребляться.
    """

    past = datetime.now(timezone.utc) - timedelta(minutes=10)
    row = PayoutMiniAppSession(
        user_id=7,
        session_token_hash="opaque-hash",
        status="verified",
        expires_at=past,
        telegram_user_id=555,
        verified_at=past - timedelta(seconds=5),
    )
    state = _SessionState(rows=[row])
    _patch_common(monkeypatch, state)

    result = payout_miniapp_service.consume_verified_payout_miniapp_session(7)

    assert result == {"ok": False, "error": "SESSION_EXPIRED"}
    assert row.status == "expired"


def test_confirm_payout_miniapp_session_rejects_mismatched_linked_account(monkeypatch) -> None:
    """EN: Mini App verification must reject when validated tg_user_id differs from already linked account.
    RU: Mini App verification должна отклоняться, если validated tg_user_id отличается от уже привязанного account.
    """

    row = PayoutMiniAppSession(
        user_id=7,
        session_token_hash=payout_miniapp_service._session_token_hash("opaque-start"),
        status="issued",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
    )
    state = _SessionState(rows=[row], account=_FakeTelegramAccount(telegram_user_id=111))
    _patch_common(
        monkeypatch,
        state,
        payload=_miniapp_payload(start_param="opaque-start", user_id=222, username="other_user"),
    )

    result = payout_miniapp_service.confirm_payout_miniapp_session("signed-init-data", "opaque-start")

    assert result == {"ok": False, "error": "TELEGRAM_ACCOUNT_MISMATCH"}
    assert row.status == "rejected"
    assert row.fail_reason == "TELEGRAM_ACCOUNT_MISMATCH"
