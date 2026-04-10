"""EN: Internal payout request creation with Mini App consume and balance reservation.
RU: Создание внутреннего payout request с Mini App consume и резервированием баланса.
"""

from __future__ import annotations

import logging
from decimal import Decimal, ROUND_DOWN, InvalidOperation

from sqlalchemy import select

from server.db.sessions.session_factory import get_session
from server.db.models.profile_game import ProfileGame
from server.db.models.payout_request import PayoutRequest
from server.db.models.user import User
from server.app.security.payout_wallet import PayoutWalletValidationError, validate_payout_wallet_address
from server.telegram.services.payout_miniapp_service import consume_verified_payout_miniapp_session_in_session


_PAYOUT_ASSET_CODE = "USDT"
_AMOUNT_QUANT = Decimal("0.001")
_LOG = logging.getLogger("cosmic.payout_request")


def _normalize_amount(amount: object) -> Decimal:
    """EN: Normalize payout amount to a positive Decimal with 3 fractional digits.
    RU: Нормализовать payout amount в положительный Decimal с 3 знаками после запятой.
    """

    try:
        value = Decimal(str(amount)).quantize(_AMOUNT_QUANT, rounding=ROUND_DOWN)
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("PAYOUT_AMOUNT_INVALID") from None
    if value <= Decimal("0"):
        raise ValueError("PAYOUT_AMOUNT_INVALID")
    return value


def _ensure_profile_game_locked(session, user_id: int) -> ProfileGame:
    """EN: Load or create the per-user profile_game row under transaction scope for balance reserve.
    RU: Загрузить или создать строку profile_game пользователя в рамках транзакции для reserve баланса.
    """

    row = session.scalar(
        select(ProfileGame)
        .where(ProfileGame.user_id == int(user_id))
        .with_for_update()
        .limit(1)
    )
    if row is None:
        row = ProfileGame(user_id=int(user_id), balance=0, reserved_balance=0)
        session.add(row)
        session.flush()
    return row


def _decimal_or_zero(value: object) -> Decimal:
    """EN: Convert stored numeric value to Decimal or zero without changing domain precision.
    RU: Преобразовать сохранённое numeric-значение в Decimal или ноль без смены доменной точности.
    """

    if value is None:
        return Decimal("0")
    return Decimal(str(value)).quantize(_AMOUNT_QUANT, rounding=ROUND_DOWN)


def create_payout_request(user_id: int, amount: object, wallet_address: str) -> dict:
    """EN: Atomically consume payout verification, reserve balance, and create internal payout request.
    RU: Атомарно consume payout verification, зарезервировать баланс и создать внутренний payout request.

    EN: This service does not send funds to any external provider. It only prepares the internal
    request and reserve state for the next provider integration step.
    RU: Этот сервис не отправляет средства во внешний provider. Он только подготавливает внутренний
    request и reserve-состояние для следующего шага интеграции с provider.
    """

    try:
        user_id_value = int(user_id)
    except Exception:
        return {"ok": False, "error": "BAD_USER_ID"}

    try:
        amount_value = _normalize_amount(amount)
    except ValueError:
        return {"ok": False, "error": "PAYOUT_AMOUNT_INVALID"}

    try:
        wallet_value = validate_payout_wallet_address(wallet_address)
    except PayoutWalletValidationError as exc:
        return {"ok": False, "error": exc.error_code}

    try:
        with get_session() as session:
            user = session.get(User, user_id_value)
            if user is None:
                _LOG.info("event=PAYOUT_REQUEST_REJECT user_id=%s reason=%s", user_id_value, "NOT_FOUND")
                return {"ok": False, "error": "NOT_FOUND"}

            profile_game = _ensure_profile_game_locked(session, user_id_value)
            available_balance = _decimal_or_zero(profile_game.balance)
            reserved_balance = _decimal_or_zero(profile_game.reserved_balance)
            if available_balance < amount_value:
                _LOG.info(
                    "event=PAYOUT_REQUEST_REJECT user_id=%s reason=%s balance=%s amount=%s",
                    user_id_value,
                    "BALANCE_INSUFFICIENT",
                    str(available_balance),
                    str(amount_value),
                )
                return {"ok": False, "error": "BALANCE_INSUFFICIENT"}

            verification = consume_verified_payout_miniapp_session_in_session(session, user_id_value)
            if not verification.get("ok"):
                _LOG.info(
                    "event=PAYOUT_REQUEST_REJECT user_id=%s reason=%s",
                    user_id_value,
                    str(verification.get("error")),
                )
                return verification

            profile_game.balance = available_balance - amount_value
            profile_game.reserved_balance = reserved_balance + amount_value

            payout_request = PayoutRequest(
                user_id=user_id_value,
                telegram_user_id=int(verification["telegram_user_id"]),
                wallet_address=wallet_value,
                asset_code=_PAYOUT_ASSET_CODE,
                amount=amount_value,
                status="reserved",
                miniapp_session_id=int(verification.get("miniapp_session_id") or 0) or None,
            )
            session.add(payout_request)
            session.flush()
            _LOG.info(
                "event=PAYOUT_REQUEST_CREATED user_id=%s payout_request_id=%s tg_uid=%s amount=%s status=%s",
                user_id_value,
                int(payout_request.id),
                int(verification["telegram_user_id"]),
                str(amount_value),
                "reserved",
            )

            return {
                "ok": True,
                "payout_request_id": int(payout_request.id),
                "status": "reserved",
                "amount": float(amount_value),
                "asset_code": _PAYOUT_ASSET_CODE,
                "available_balance": float(profile_game.balance),
                "reserved_balance": float(profile_game.reserved_balance),
            }
    except Exception:
        _LOG.exception("event=PAYOUT_REQUEST_CREATE_FAIL user_id=%s", user_id_value)
        return {"ok": False, "error": "DB_ERROR"}


def create_hub_payout_request_in_session(
    session,
    *,
    user_id: int,
    telegram_user_id: int,
    amount: object,
    wallet_address: str,
    miniapp_session_id: int | None = None,
) -> dict:
    """EN: Create internal payout request from a trusted hub session within caller transaction scope.
    RU: Создать внутренний payout request из доверенной hub session в рамках транзакции вызывающего кода.

    EN: This helper reuses the same reserve and wallet validation rules as the canonical payout
    request flow, but it does not consume a separate payout Mini App session because hub access
    has already been proven and bound to the caller transaction.
    RU: Этот helper переиспользует те же правила reserve и валидации кошелька, что и канонический
    payout flow, но не consume-ит отдельную payout Mini App session, потому что доступ через hub
    уже доказан и привязан к транзакции вызывающего кода.
    """

    try:
        user_id_value = int(user_id)
        telegram_user_id_value = int(telegram_user_id)
    except Exception:
        return {"ok": False, "error": "BAD_USER_ID"}
    if user_id_value <= 0 or telegram_user_id_value <= 0:
        return {"ok": False, "error": "BAD_USER_ID"}

    try:
        amount_value = _normalize_amount(amount)
    except ValueError:
        return {"ok": False, "error": "PAYOUT_AMOUNT_INVALID"}

    try:
        wallet_value = validate_payout_wallet_address(wallet_address)
    except PayoutWalletValidationError as exc:
        return {"ok": False, "error": exc.error_code}

    user = session.get(User, user_id_value)
    if user is None:
        _LOG.info("event=HUB_PAYOUT_REQUEST_REJECT user_id=%s reason=%s", user_id_value, "NOT_FOUND")
        return {"ok": False, "error": "NOT_FOUND"}

    profile_game = _ensure_profile_game_locked(session, user_id_value)
    available_balance = _decimal_or_zero(profile_game.balance)
    reserved_balance = _decimal_or_zero(profile_game.reserved_balance)
    if available_balance < amount_value:
        _LOG.info(
            "event=HUB_PAYOUT_REQUEST_REJECT user_id=%s reason=%s balance=%s amount=%s",
            user_id_value,
            "BALANCE_INSUFFICIENT",
            str(available_balance),
            str(amount_value),
        )
        return {"ok": False, "error": "BALANCE_INSUFFICIENT"}

    profile_game.balance = available_balance - amount_value
    profile_game.reserved_balance = reserved_balance + amount_value

    payout_request = PayoutRequest(
        user_id=user_id_value,
        telegram_user_id=telegram_user_id_value,
        wallet_address=wallet_value,
        asset_code=_PAYOUT_ASSET_CODE,
        amount=amount_value,
        status="reserved",
        miniapp_session_id=int(miniapp_session_id or 0) or None,
    )
    session.add(payout_request)
    session.flush()
    _LOG.info(
        "event=HUB_PAYOUT_REQUEST_CREATED user_id=%s payout_request_id=%s tg_uid=%s amount=%s status=%s",
        user_id_value,
        int(payout_request.id),
        telegram_user_id_value,
        str(amount_value),
        "reserved",
    )
    return {
        "ok": True,
        "payout_request_id": int(payout_request.id),
        "status": "reserved",
        "amount": float(amount_value),
        "asset_code": _PAYOUT_ASSET_CODE,
        "available_balance": float(profile_game.balance),
        "reserved_balance": float(profile_game.reserved_balance),
    }
