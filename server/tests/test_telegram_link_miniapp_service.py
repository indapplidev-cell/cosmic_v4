"""EN: Focused lifecycle tests for telegram_link Mini App verification service contracts.
RU: Точечные lifecycle-тесты контрактов telegram_link Mini App verification service.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import server.services.payout_miniapp_service as miniapp_service
from server.models.payout_miniapp_session import PayoutMiniAppSession
from server.security.telegram_miniapp import TelegramMiniAppPayload


@dataclass
class _SessionState:
    """EN: Mutable in-memory state for fake telegram_link Mini App service tests.
    RU: Изменяемое in-memory состояние для fake-тестов telegram_link Mini App service.
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
    """EN: Minimal fake SQLAlchemy session for telegram_link Mini App service contract tests.
    RU: Минимальная fake SQLAlchemy session для contract-тестов telegram_link Mini App service.
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
    """EN: Build normalized Telegram Mini App payload for telegram_link service tests.
    RU: Собрать нормализованный Telegram Mini App payload для telegram_link service-тестов.
    """

    return TelegramMiniAppPayload(
        user={"id": int(user_id), "username": username},
        auth_date=int(datetime.now(timezone.utc).timestamp()),
        start_param=start_param,
    )


def _patch_common(monkeypatch, state: _SessionState, *, start_param: str = "opaque-start", payload: TelegramMiniAppPayload | None = None) -> None:
    """EN: Patch common Mini App service dependencies for telegram_link lifecycle tests.
    RU: Замокать общие зависимости Mini App service для lifecycle-тестов telegram_link.
    """

    monkeypatch.setattr(miniapp_service, "get_session", _fake_get_session(state))
    monkeypatch.setattr(miniapp_service, "get_payout_miniapp_session_ttl_sec", lambda: 300)
    monkeypatch.setattr(miniapp_service, "get_payout_miniapp_auth_max_age_sec", lambda: 300)
    monkeypatch.setattr(miniapp_service, "get_pay_bot_token", lambda: "123456:TEST_PAY_BOT_TOKEN")
    monkeypatch.setattr(miniapp_service, "_generate_session_token", lambda: start_param)
    monkeypatch.setattr(
        miniapp_service,
        "_build_miniapp_url",
        lambda token: f"https://t.me/payprotect_bot/verify?startapp={token}",
    )
    monkeypatch.setattr(
        miniapp_service,
        "_load_session_by_token",
        lambda session, token: next((row for row in reversed(state.rows) if row.session_token_hash == miniapp_service._session_token_hash(token)), None),
    )
    monkeypatch.setattr(
        miniapp_service,
        "_load_latest_session_for_user",
        lambda session, user_id, purpose, for_update=False: next(
            (row for row in reversed(state.rows) if int(row.user_id) == int(user_id) and str(row.purpose) == str(purpose)),
            None,
        ),
    )
    monkeypatch.setattr(
        miniapp_service,
        "validate_telegram_miniapp_init_data",
        lambda init_data_raw, bot_token, max_age_sec=300: payload or _miniapp_payload(start_param=start_param),
    )


def test_telegram_link_miniapp_happy_path_request_confirm_status(monkeypatch) -> None:
    """EN: telegram_link Mini App request, confirm and status must complete one verified lifecycle and call Telegram linkage.
    RU: telegram_link Mini App request, confirm и status должны завершать один verified lifecycle и вызывать Telegram linkage.
    """

    state = _SessionState()
    linked_calls: list[dict[str, object]] = []
    _patch_common(monkeypatch, state)
    monkeypatch.setattr(
        miniapp_service,
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

    request_result = miniapp_service.request_telegram_link_miniapp_session(7)
    confirm_result = miniapp_service.confirm_telegram_miniapp_session("signed-init-data", "opaque-start")
    status_result = miniapp_service.get_telegram_link_miniapp_session_status(7)

    assert request_result["ok"] is True
    assert request_result["purpose"] == "telegram_link"
    assert state.rows[0].purpose == "telegram_link"
    assert confirm_result == {"ok": True, "user_id": 7, "purpose": "telegram_link", "telegram_user_id": 555}
    assert status_result["verified"] is True
    assert status_result["status"] == "verified"
    assert status_result["purpose"] == "telegram_link"
    assert len(linked_calls) == 1


def test_telegram_link_miniapp_rejects_mismatched_linked_account(monkeypatch) -> None:
    """EN: telegram_link Mini App verification must reject when validated tg_user_id differs from already linked account.
    RU: telegram_link Mini App verification должна отклоняться, если validated tg_user_id отличается от уже привязанного account.
    """

    row = PayoutMiniAppSession(
        user_id=7,
        purpose="telegram_link",
        session_token_hash=miniapp_service._session_token_hash("opaque-start"),
        status="issued",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
    )
    state = _SessionState(rows=[row], account=_FakeTelegramAccount(telegram_user_id=111))
    _patch_common(
        monkeypatch,
        state,
        payload=_miniapp_payload(start_param="opaque-start", user_id=222, username="other_user"),
    )

    result = miniapp_service.confirm_telegram_miniapp_session("signed-init-data", "opaque-start")

    assert result == {"ok": False, "error": "TELEGRAM_ACCOUNT_MISMATCH"}
    assert row.status == "rejected"


def test_telegram_link_miniapp_reuse_and_expired_protection(monkeypatch) -> None:
    """EN: telegram_link Mini App session must not be reusable after verify and must expire after TTL.
    RU: telegram_link Mini App session не должна переиспользоваться после verify и должна истекать по TTL.
    """

    now_utc = datetime.now(timezone.utc)
    row = PayoutMiniAppSession(
        user_id=7,
        purpose="telegram_link",
        session_token_hash=miniapp_service._session_token_hash("opaque-start"),
        status="verified",
        expires_at=now_utc + timedelta(minutes=5),
        telegram_user_id=555,
        verified_at=now_utc,
    )
    state = _SessionState(rows=[row])
    _patch_common(monkeypatch, state)

    reused = miniapp_service.confirm_telegram_miniapp_session("signed-init-data", "opaque-start")
    assert reused == {"ok": False, "error": "SESSION_ALREADY_VERIFIED"}

    row.status = "issued"
    row.verified_at = None
    row.expires_at = now_utc - timedelta(minutes=1)
    expired = miniapp_service.confirm_telegram_miniapp_session("signed-init-data", "opaque-start")
    assert expired == {"ok": False, "error": "SESSION_EXPIRED"}
