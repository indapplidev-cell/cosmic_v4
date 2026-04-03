# -*- coding: utf-8 -*-
"""EN: Local per-level result service for survive_timed attempts.
RU: Локальный сервис результатов попыток survive_timed по уровням.
"""

from __future__ import annotations

from data.gameplay.modes.survive_timed.local_level_result_store import (
    load_level_results,
    save_level_result_snapshot,
    save_level_results,
)


def apply_survive_timed_level_result_from_server(result_payload: object) -> dict | None:
    """EN: Apply one server level-result snapshot to local survive_timed storage without merge heuristics.
    RU: Применить один server snapshot результата уровня к локальному survive_timed storage без merge-эвристик.
    """

    if not isinstance(result_payload, dict):
        return None
    try:
        level_number = max(int(result_payload.get("level_number", 0) or 0), 1)
        stored = save_level_result_snapshot(
            level_number,
            {
                "best_survival_sec": max(float(int(result_payload.get("best_survival_ms", 0) or 0)) / 1000.0, 0.0),
                "last_survival_sec": max(float(int(result_payload.get("last_survival_ms", 0) or 0)) / 1000.0, 0.0),
                "attempts_count": max(int(result_payload.get("attempts_count", 0) or 0), 0),
                "completed_count": max(int(result_payload.get("completed_count", 0) or 0), 0),
                "last_result": str(result_payload.get("last_result", "") or ""),
            },
            updated_at=str(result_payload.get("updated_at", "") or ""),
        )
        return dict(stored.get("levels", {}).get(str(level_number), {}))
    except Exception:
        return None


class SurviveTimedLevelResultService:
    """EN: Persist survive_timed per-level attempts and completion metrics locally.
    RU: Локально сохранять метрики попыток и прохождений survive_timed по уровням.
    """

    def get_level_result(self, level_number: int) -> dict:
        """EN: Return local survive_timed result snapshot for one level.
        RU: Вернуть локальный снимок результата survive_timed для одного уровня.
        """

        payload = load_level_results()
        return dict(payload.get("levels", {}).get(str(max(int(level_number), 1)), {}))

    def apply_server_result(self, result_payload: object) -> dict | None:
        """EN: Apply one server-authoritative result snapshot to local storage.
        RU: Применить один server-authoritative snapshot результата к локальному storage.
        """

        return apply_survive_timed_level_result_from_server(result_payload)

    def record_success(self, level_number: int, survival_sec: float) -> dict:
        """EN: Persist successful survive_timed attempt and update best/last counters.
        RU: Сохранить успешную попытку survive_timed и обновить лучшие/последние счётчики.
        """

        return self._record_result(level_number=level_number, survival_sec=survival_sec, result="success")

    def record_fail(self, level_number: int, survival_sec: float) -> dict:
        """EN: Persist failed survive_timed attempt and update last/best counters without completion increment.
        RU: Сохранить неуспешную попытку survive_timed и обновить last/best без увеличения completed_count.
        """

        return self._record_result(level_number=level_number, survival_sec=survival_sec, result="fail")

    def _record_result(self, *, level_number: int, survival_sec: float, result: str) -> dict:
        """EN: Update one level result entry inside local survive_timed JSON store.
        RU: Обновить запись результата одного уровня внутри локального JSON-хранилища survive_timed.
        """

        number = max(int(level_number), 1)
        survival_value = max(float(survival_sec), 0.0)
        payload = load_level_results()
        levels = dict(payload.get("levels", {}))
        current = dict(levels.get(str(number), {}))
        best_survival = max(float(current.get("best_survival_sec", 0.0) or 0.0), survival_value)
        completed_count = max(int(current.get("completed_count", 0) or 0), 0)
        if result == "success":
            completed_count += 1
        levels[str(number)] = {
            "best_survival_sec": best_survival,
            "last_survival_sec": survival_value,
            "attempts_count": max(int(current.get("attempts_count", 0) or 0), 0) + 1,
            "completed_count": completed_count,
            "last_result": result,
        }
        payload["levels"] = levels
        stored = save_level_results(payload)
        return dict(stored["levels"][str(number)])
