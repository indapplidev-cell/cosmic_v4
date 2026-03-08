"""EN: Pure profile math for record/rating/balance formulas from docx.
RU: Чистая математика профиля (рекорд/рейтинг/баланс) по формулам из docx.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import exp, floor, log1p


@dataclass(frozen=True)
class ProfileMathConfig:
    """EN: Configuration constants for profile formulas.
    RU: Конфигурационные константы для формул профиля.
    """

    BANNER_COIN: float = 0.10
    REWARDED_COIN: float = 0.30
    BANNER_IMP_SEC: int = 5
    PER_1000: int = 1000

    V_MAX: float = 4.6533
    V_MIN: float = 0.4723
    V_MID: float = 2.5628
    CHEAT_MIN_SCORE: int = 20
    EPS_FAST: float = 0.02
    EPS_SLOW: float = 0.02
    EPS_T: float = 1e-9
    ATTEMPTS_BASE: int = 3

    # EN: Case weights from docx example, preserving required order W1 > W3 > W2 > W4.
    # RU: Веса случаев из примера docx с сохранением порядка W1 > W3 > W2 > W4.
    W1: float = 1.00
    W2: float = 0.70
    W3: float = 0.85
    W4: float = 0.55

    REC_REF: float = 120.0
    LIFE_REF: float = 120.0
    GAME_REF: float = 300.0

    # EN: Core weights (must sum to 1).
    # RU: Веса core (сумма должна быть 1).
    a_speed: float = 0.30
    a_rec: float = 0.25
    a_life: float = 0.20
    a_game: float = 0.15
    a_rel: float = 0.10

    # EN: Quality weights for payout k_quality (must sum to 1).
    # RU: Веса качества для payout k_quality (сумма должна быть 1).
    b_rating: float = 0.30
    b_rec: float = 0.25
    b_life: float = 0.20
    b_game: float = 0.15
    b_rel: float = 0.10

    k_attempts: float = 0.35
    POLICY_RATING_MAX: bool = True


DEFAULT_CFG = ProfileMathConfig()


def clamp01(x: float) -> float:
    """EN: Clamp numeric value to [0..1].
    RU: Ограничить числовое значение диапазоном [0..1].
    """

    return max(0.0, min(1.0, float(x)))


def norm_log(x: float, x_ref: float) -> float:
    """EN: Log-normalize value by reference into [0..1].
    RU: Лог-нормализация значения по референсу в диапазон [0..1].
    """

    if x_ref <= 0:
        return 0.0
    return clamp01(log1p(max(0.0, float(x))) / log1p(float(x_ref)))


def f3_attempts(attempts: int, k_attempts: float) -> float:
    """EN: Saturating reliability factor from attempts.
    RU: Насыщающийся фактор надёжности по числу попыток.
    """

    return clamp01(1.0 - exp(-float(k_attempts) * max(0, int(attempts) - 1)))


def triangular_speed_weight(v: float, v_min: float, v_mid: float, v_max: float) -> float:
    """EN: Triangular speed weight from docx, max at v_mid.
    RU: Треугольный вес скорости из docx, максимум в v_mid.
    """

    v = float(v)
    if v <= float(v_min) or v >= float(v_max):
        return 0.0
    if v <= float(v_mid):
        return clamp01(1.0 - ((float(v_mid) - v) / max(float(v_mid) - float(v_min), 1e-12)))
    return clamp01(1.0 - ((v - float(v_mid)) / max(float(v_max) - float(v_mid), 1e-12)))


def calc_v_chis(record_pure: int, chis_sec: float, cfg: ProfileMathConfig = DEFAULT_CFG) -> float:
    """EN: Compute CHIS speed v_chis.
    RU: Вычислить скорость ЧИС v_chis.
    """

    return float(record_pure) / max(float(chis_sec), float(cfg.EPS_T))


def cheat_speed(record_pure: int, chis_sec: float, cfg: ProfileMathConfig = DEFAULT_CFG) -> bool:
    """EN: Two-sided anti-cheat check by CHIS speed from docx.
    RU: Двусторонняя античит-проверка по скорости ЧИС из docx.
    """

    v_chis = calc_v_chis(record_pure, chis_sec, cfg)
    if int(record_pure) < int(cfg.CHEAT_MIN_SCORE):
        return False
    too_fast = v_chis >= float(cfg.V_MAX) * (1.0 + float(cfg.EPS_FAST))
    too_slow = v_chis <= float(cfg.V_MIN) * (1.0 - float(cfg.EPS_SLOW))
    return bool(too_fast or too_slow)


def resolve_w_case(
    *,
    hit_record: bool,
    has_reward: bool,
    cfg: ProfileMathConfig = DEFAULT_CFG,
) -> float:
    """EN: Resolve case weight by 4-case table from docx.
    RU: Выбрать вес случая по таблице из 4 вариантов docx.
    """

    if hit_record and (not has_reward):
        return float(cfg.W1)
    if hit_record and has_reward:
        return float(cfg.W2)
    if (not hit_record) and (not has_reward):
        return float(cfg.W3)
    return float(cfg.W4)


def calc_rating(
    *,
    record_prev: int,
    record_sis: int,
    record_pure: int,
    chis_sec: float,
    attempts: int,
    reward_clicks: int,
    best_life_score: int,
    best_game_score: int,
    valid_starts: int = 0,
    cfg: ProfileMathConfig = DEFAULT_CFG,
) -> tuple[int, dict]:
    """EN: Calculate rating (0..1000) by docx formula.
    RU: Рассчитать рейтинг (0..1000) по формуле docx.
    """

    _ = valid_starts
    v_chis = calc_v_chis(record_pure, chis_sec, cfg)
    f_speed = norm_log(v_chis, cfg.V_MAX)
    f_rec = norm_log(float(record_pure), cfg.REC_REF)
    f1 = norm_log(float(best_life_score), cfg.LIFE_REF)
    f2 = norm_log(float(best_game_score), cfg.GAME_REF)
    f3 = f3_attempts(int(attempts), cfg.k_attempts)

    hit_record = int(record_sis) >= int(record_prev)
    has_reward = (int(attempts) > int(cfg.ATTEMPTS_BASE)) or (int(reward_clicks) > 0)
    w_case = resolve_w_case(hit_record=hit_record, has_reward=has_reward, cfg=cfg)
    w_spd = triangular_speed_weight(v_chis, cfg.V_MIN, cfg.V_MID, cfg.V_MAX)

    core = (
        float(cfg.a_speed) * f_speed
        + float(cfg.a_rec) * f_rec
        + float(cfg.a_life) * f1
        + float(cfg.a_game) * f2
        + float(cfg.a_rel) * f3
    )
    rating_01 = clamp01(w_case * w_spd * core)
    rating = int(round(1000.0 * rating_01))
    return rating, {
        "v_chis": v_chis,
        "f_speed": f_speed,
        "f_rec": f_rec,
        "f1": f1,
        "f2": f2,
        "f3": f3,
        "w_case": w_case,
        "w_spd": w_spd,
        "core": core,
        "rating_01": rating_01,
        "rating": rating,
    }


def calc_pay_raw(sis_sec: float, reward_clicks: int, cfg: ProfileMathConfig = DEFAULT_CFG) -> tuple[float, dict]:
    """EN: Calculate raw payout from banners+reward only.
    RU: Рассчитать чистую выплату (баннеры+reward) без коэффициентов.
    """

    banner_impr = int(floor(max(0.0, float(sis_sec)) / float(cfg.BANNER_IMP_SEC)))
    banner_pay = float(cfg.BANNER_COIN) * (float(banner_impr) / float(cfg.PER_1000))
    reward_pay = float(cfg.REWARDED_COIN) * (float(max(0, int(reward_clicks))) / float(cfg.PER_1000))
    pay_raw = banner_pay + reward_pay
    return pay_raw, {
        "banner_impr": banner_impr,
        "banner_pay": banner_pay,
        "reward_pay": reward_pay,
        "pay_raw": pay_raw,
    }


def calc_balance_delta(
    *,
    pay_raw: float,
    rating: int,
    f_rec: float,
    f1: float,
    f2: float,
    f3: float,
    w_case: float,
    cfg: ProfileMathConfig = DEFAULT_CFG,
) -> tuple[float, dict]:
    """EN: Calculate balance delta with guaranteed bound balance_delta <= pay_raw.
    RU: Рассчитать дельту баланса с гарантией balance_delta <= pay_raw.
    """

    r_norm = clamp01(float(rating) / 1000.0)
    k_quality = clamp01(
        float(cfg.b_rating) * r_norm
        + float(cfg.b_rec) * clamp01(f_rec)
        + float(cfg.b_life) * clamp01(f1)
        + float(cfg.b_game) * clamp01(f2)
        + float(cfg.b_rel) * clamp01(f3)
    )
    k = clamp01(float(w_case) * k_quality)
    balance_delta = max(0.0, float(pay_raw)) * k
    return balance_delta, {"r_norm": r_norm, "k_quality": k_quality, "k": k, "balance_delta": balance_delta}
