"""EN: Profile/game DB service for update/clear operations.
RU: Сервис БД профиля/игры для операций обновления и очистки.
"""

from __future__ import annotations

import os

from server.db import get_session
from server.models.profile_game import ProfileGame
from server.models.profile_user import ProfileUser
from server.services.profile_math import (
    DEFAULT_CFG,
    calc_balance_delta,
    calc_pay_raw,
    calc_rating,
    cheat_fast_windows,
    cheat_speed,
)

_PROFILE_USER_FIELDS = {"login", "phone", "telegram"}
_PROFILE_GAME_FIELDS = {"record", "rating", "balance"}


def _ensure_profile_user(session, user_id: int) -> ProfileUser:
    """EN: Get or create one-to-one ProfileUser row.
    RU: Получить или создать строку ProfileUser один-к-одному.
    """
    obj = session.query(ProfileUser).filter(ProfileUser.user_id == user_id).one_or_none()
    if obj is None:
        obj = ProfileUser(user_id=user_id)
        session.add(obj)
        session.flush()
    return obj


def _ensure_profile_game(session, user_id: int) -> ProfileGame:
    """EN: Get or create one-to-one ProfileGame row.
    RU: Получить или создать строку ProfileGame один-к-одному.
    """
    obj = session.query(ProfileGame).filter(ProfileGame.user_id == user_id).one_or_none()
    if obj is None:
        obj = ProfileGame(user_id=user_id)
        session.add(obj)
        session.flush()
    return obj


def update_profile_user(
    user_id: int,
    *,
    login: str | None = None,
    phone: str | None = None,
    telegram: str | None = None,
) -> dict:
    """EN: Update non-empty ProfileUser fields for provided user.
    RU: Обновить непустые поля ProfileUser для указанного пользователя.
    """
    try:
        user_id_value = int(user_id)
    except Exception:
        return {"ok": False, "error": "BAD_USER_ID"}

    try:
        with get_session() as session:
            obj = _ensure_profile_user(session, user_id_value)

            if login is not None and str(login).strip():
                obj.login = str(login).strip()
            if phone is not None and str(phone).strip():
                obj.phone = str(phone).strip()
            if telegram is not None and str(telegram).strip():
                obj.telegram = str(telegram).strip()

            session.flush()
            return {"ok": True}
    except Exception:
        return {"ok": False, "error": "DB_ERROR"}


def clear_profile_user_fields(user_id: int, fields: list[str]) -> dict:
    """EN: Reset selected ProfileUser fields to DB default literal value.
    RU: Сбросить выбранные поля ProfileUser к дефолтному литералу БД.
    """
    try:
        user_id_value = int(user_id)
    except Exception:
        return {"ok": False, "error": "BAD_USER_ID"}

    valid_fields = [f for f in fields if f in _PROFILE_USER_FIELDS]
    if not valid_fields:
        return {"ok": True}

    try:
        with get_session() as session:
            obj = _ensure_profile_user(session, user_id_value)
            for field in valid_fields:
                setattr(obj, field, "no data")
            session.flush()
            return {"ok": True}
    except Exception:
        return {"ok": False, "error": "DB_ERROR"}


def update_profile_game(
    user_id: int,
    *,
    record: int | None = None,
    rating: int | None = None,
    balance: float | None = None,
) -> dict:
    """EN: Update provided ProfileGame numeric fields.
    RU: Обновить переданные числовые поля ProfileGame.
    """
    try:
        user_id_value = int(user_id)
    except Exception:
        return {"ok": False, "error": "BAD_USER_ID"}

    try:
        with get_session() as session:
            obj = _ensure_profile_game(session, user_id_value)

            if record is not None:
                obj.record = int(record)
            if rating is not None:
                obj.rating = int(rating)
            if balance is not None:
                obj.balance = round(float(balance), 3)

            session.flush()
            return {"ok": True}
    except Exception:
        return {"ok": False, "error": "DB_ERROR"}


def clear_profile_game_fields(user_id: int, fields: list[str]) -> dict:
    """EN: Reset selected ProfileGame fields to numeric zero.
    RU: Сбросить выбранные поля ProfileGame в числовой ноль.
    """
    try:
        user_id_value = int(user_id)
    except Exception:
        return {"ok": False, "error": "BAD_USER_ID"}

    valid_fields = [f for f in fields if f in _PROFILE_GAME_FIELDS]
    if not valid_fields:
        return {"ok": True}

    try:
        with get_session() as session:
            obj = _ensure_profile_game(session, user_id_value)
            for field in valid_fields:
                setattr(obj, field, 0)
            session.flush()
            return {"ok": True}
    except Exception:
        return {"ok": False, "error": "DB_ERROR"}


def apply_finished_session(user_id: int, metrics: dict) -> dict:
    """EN: Apply one finished SIS by server formulas and persist resulting profile_game snapshot.
    RU: Применить завершенную СИС по серверным формулам и сохранить итоговый snapshot profile_game.
    """

    try:
        user_id_value = int(user_id)
    except Exception:
        return {"ok": False, "error": "BAD_USER_ID"}

    try:
        record_sis = int(metrics.get("record_sis") or 0)
        record_pure = int(metrics.get("record_pure") or 0)
        sis_sec = float(metrics.get("sis_sec") or 0.0)
        chis_sec = float(metrics.get("chis_sec") or 0.0)
        attempts = int(metrics.get("attempts") or DEFAULT_CFG.ATTEMPTS_BASE)
        reward_clicks = int(metrics.get("reward_clicks") or 0)
        best_life_score = int(metrics.get("best_life_score") or 0)
        best_game_score = int(metrics.get("best_game_score") or 0)
        anti_cheat_windows = list(metrics.get("anti_cheat_windows") or [])
    except Exception:
        return {"ok": False, "error": "FORMAT"}

    try:
        with get_session() as session:
            obj = _ensure_profile_game(session, user_id_value)
            record_prev = int(obj.record or 0)
            rating_prev = int(obj.rating or 0)
            balance_prev = float(obj.balance or 0.0)

            cheat_fast = cheat_fast_windows(anti_cheat_windows=anti_cheat_windows, cfg=DEFAULT_CFG)
            cheat_final = cheat_speed(record_pure=record_pure, chis_sec=chis_sec, cfg=DEFAULT_CFG)
            cheat = bool(cheat_fast or cheat_final)

            debug_payload: dict = {}
            if cheat:
                obj.record = 0
                obj.rating = 0
                obj.balance = 0.0
                session.flush()
                if os.getenv("PROFILE_DEBUG", "0") == "1":
                    debug_payload = {
                        "cheat_fast": cheat_fast,
                        "cheat_final": cheat_final,
                    }
                return {
                    "ok": True,
                    "cheat": True,
                    "record": 0,
                    "rating": 0,
                    "balance": 0.0,
                    "debug": debug_payload,
                }

            pay_raw, pay_dbg = calc_pay_raw(sis_sec=sis_sec, reward_clicks=reward_clicks, cfg=DEFAULT_CFG)
            rating_sis, rating_dbg = calc_rating(
                record_prev=record_prev,
                record_sis=record_sis,
                record_pure=record_pure,
                chis_sec=chis_sec,
                attempts=attempts,
                reward_clicks=reward_clicks,
                best_life_score=best_life_score,
                best_game_score=best_game_score,
                valid_starts=attempts,
                cfg=DEFAULT_CFG,
            )
            balance_delta, bal_dbg = calc_balance_delta(
                pay_raw=pay_raw,
                rating=rating_sis,
                f_rec=float(rating_dbg["f_rec"]),
                f1=float(rating_dbg["f1"]),
                f2=float(rating_dbg["f2"]),
                f3=float(rating_dbg["f3"]),
                w_case=float(rating_dbg["w_case"]),
                cfg=DEFAULT_CFG,
            )

            record_new = max(record_prev, record_sis)
            if DEFAULT_CFG.POLICY_RATING_MAX:
                rating_new = max(rating_prev, rating_sis)
            else:
                rating_new = int(rating_sis)
            balance_new = round(balance_prev + float(balance_delta), 3)

            obj.record = int(record_new)
            obj.rating = int(rating_new)
            obj.balance = float(balance_new)
            session.flush()

            if os.getenv("PROFILE_DEBUG", "0") == "1":
                debug_payload = {
                    "pay_raw": pay_dbg,
                    "rating": rating_dbg,
                    "balance": bal_dbg,
                    "cheat_fast": cheat_fast,
                    "cheat_final": cheat_final,
                }

            return {
                "ok": True,
                "cheat": False,
                "record": int(record_new),
                "rating": int(rating_new),
                "balance": float(balance_new),
                "debug": debug_payload,
            }
    except Exception:
        return {"ok": False, "error": "DB_ERROR"}
