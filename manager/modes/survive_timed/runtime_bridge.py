# -*- coding: utf-8 -*-
"""EN: Runtime bridge that layers survive_timed business rules over existing gameplay loop.
RU: Runtime-мост, который накладывает бизнес-логику survive_timed поверх существующего игрового цикла.
"""

from __future__ import annotations

from time import perf_counter

from engine.modes.survive_timed.contracts import SurviveTimedLevelProfile
from manager import auth_backend
from manager.modes.survive_timed.level_bootstrap_service import SurviveTimedLevelBootstrapService
from manager.modes.survive_timed.level_progress_service import SurviveTimedLevelProgressService
from manager.modes.survive_timed.level_result_service import SurviveTimedLevelResultService


class SurviveTimedRuntimeBridge:
    """EN: Own active survive_timed run state, win/fail evaluation, and progress/result persistence.
    RU: Владеть состоянием активного забега survive_timed, проверкой win/fail и сохранением progress/result.
    """

    def __init__(
        self,
        bootstrap_service: SurviveTimedLevelBootstrapService | None = None,
        progress_service: SurviveTimedLevelProgressService | None = None,
        result_service: SurviveTimedLevelResultService | None = None,
    ) -> None:
        """EN: Store survive_timed services required for runtime session orchestration.
        RU: Сохранить survive_timed сервисы, необходимые для orchestration runtime-сессии.
        """

        self._progress_service = progress_service or SurviveTimedLevelProgressService()
        self._result_service = result_service or SurviveTimedLevelResultService()
        self._bootstrap_service = bootstrap_service or SurviveTimedLevelBootstrapService(self._progress_service)
        self._active_profile: SurviveTimedLevelProfile | None = None
        self._run_started_at: float | None = None
        self._run_finalized = False

    def resolve_start_level_number(self) -> int:
        """EN: Return survive_timed level number that should start on next run.
        RU: Вернуть номер уровня survive_timed, который должен стартовать в следующем забеге.
        """

        return self._bootstrap_service.resolve_start_level_number()

    def activate_level(self, level_number: int) -> SurviveTimedLevelProfile:
        """EN: Activate survive_timed level and clear any previous run state.
        RU: Активировать уровень survive_timed и сбросить состояние предыдущего забега.
        """

        self._active_profile = self._bootstrap_service.activate_level(level_number)
        self._run_started_at = None
        self._run_finalized = False
        return self._active_profile

    def begin_run(self) -> SurviveTimedLevelProfile:
        """EN: Start survive_timed run timer exactly once for the currently active level.
        RU: Запустить таймер survive_timed ровно один раз для текущего активного уровня.
        """

        profile = self.get_active_profile()
        self._run_started_at = perf_counter()
        self._run_finalized = False
        return profile

    def get_active_profile(self) -> SurviveTimedLevelProfile:
        """EN: Return active survive_timed profile, resolving bootstrap state when needed.
        RU: Вернуть активный профиль survive_timed, при необходимости резолвя bootstrap-state.
        """

        if self._active_profile is None:
            self._active_profile = self._bootstrap_service.get_active_profile()
        return self._active_profile

    def get_elapsed_sec(self) -> float:
        """EN: Return elapsed survive_timed run duration or zero before the run starts.
        RU: Вернуть прошедшее время survive_timed или ноль до старта забега.
        """

        if self._run_started_at is None:
            return 0.0
        return max(perf_counter() - float(self._run_started_at), 0.0)

    def is_success_ready(self) -> bool:
        """EN: Return whether the active survive_timed run already reached target survival time.
        RU: Вернуть, достиг ли активный забег survive_timed целевого времени выживания.
        """

        if self._run_finalized or self._run_started_at is None:
            return False
        profile = self.get_active_profile()
        return self.get_elapsed_sec() >= float(profile.target_survival_sec)

    def build_hud_payload(self) -> dict:
        """EN: Return survive_timed HUD data for current level and timer overlay.
        RU: Вернуть HUD-данные survive_timed для текущего уровня и таймерного overlay.
        """

        profile = self.get_active_profile()
        elapsed = min(self.get_elapsed_sec(), float(profile.target_survival_sec))
        remaining = max(float(profile.target_survival_sec) - elapsed, 0.0)
        return {
            "level_number": int(profile.level_number),
            "target_survival_sec": int(profile.target_survival_sec),
            "elapsed_sec": float(elapsed),
            "remaining_sec": float(remaining),
        }

    def record_success(self) -> dict:
        """EN: Persist survive_timed success through server-authoritative sync or guest fallback.
        RU: Сохранить успех survive_timed через server-authoritative sync или guest fallback.
        """

        if self._run_finalized:
            return {"ok": True, "profile": self.get_active_profile(), "progress": self._progress_service.get_progress_state()}
        profile = self.get_active_profile()
        survival_sec = min(self.get_elapsed_sec(), float(profile.target_survival_sec))
        if auth_backend.has_valid_session():
            response = self._record_authorized_success(profile.level_number, survival_sec)
        else:
            result_state = self._result_service.record_success(profile.level_number, survival_sec)
            progress_state = self._progress_service.record_success(profile.level_number)
            response = {"ok": True, "profile": profile, "result": result_state, "progress": progress_state}
        self._run_finalized = True
        return response

    def record_fail(self) -> dict:
        """EN: Persist survive_timed failure through server-authoritative sync or guest fallback.
        RU: Сохранить неуспех survive_timed через server-authoritative sync или guest fallback.
        """

        if self._run_finalized:
            return {"ok": True, "profile": self.get_active_profile()}
        profile = self.get_active_profile()
        survival_sec = min(self.get_elapsed_sec(), float(profile.target_survival_sec))
        if auth_backend.has_valid_session():
            response = self._record_authorized_fail(profile.level_number, survival_sec)
        else:
            result_state = self._result_service.record_fail(profile.level_number, survival_sec)
            response = {"ok": True, "profile": profile, "result": result_state}
        self._run_finalized = True
        return response

    @staticmethod
    def _build_submit_payload(level_number: int, survival_sec: float) -> dict:
        """EN: Build one survive_timed backend payload in milliseconds.
        RU: Собрать один backend payload survive_timed в миллисекундах.
        """

        return {
            "level_number": int(level_number),
            "survival_ms": max(int(round(float(survival_sec) * 1000.0)), 0),
        }

    def _record_authorized_success(self, level_number: int, survival_sec: float) -> dict:
        """EN: Submit survive_timed success first and then mirror backend result/progress locally.
        RU: Сначала отправить успех survive_timed на сервер, затем отзеркалить backend result/progress локально.
        """

        profile = self.get_active_profile()
        ok, payload = auth_backend.submit_survive_timed_level_success(self._build_submit_payload(level_number, survival_sec))
        if not ok or not isinstance(payload, dict):
            return {"ok": False, "profile": profile, "progress": self._progress_service.get_progress_state()}
        result_state = self._result_service.apply_server_result(payload.get("result"))
        progress_state = self._progress_service.apply_server_progress(payload.get("progress"))
        if result_state is None or progress_state is None:
            return {"ok": False, "profile": profile, "progress": self._progress_service.get_progress_state()}
        return {"ok": True, "profile": profile, "result": result_state, "progress": progress_state}

    def _record_authorized_fail(self, level_number: int, survival_sec: float) -> dict:
        """EN: Submit survive_timed fail first and then mirror backend result locally.
        RU: Сначала отправить fail survive_timed на сервер, затем отзеркалить backend result локально.
        """

        profile = self.get_active_profile()
        payload = self._build_submit_payload(level_number, survival_sec)
        payload["result"] = "fail"
        ok, response = auth_backend.submit_survive_timed_level_result(payload)
        if not ok or not isinstance(response, dict):
            return {"ok": False, "profile": profile, "result": self._result_service.get_level_result(level_number)}
        result_state = self._result_service.apply_server_result(response.get("result"))
        if result_state is None:
            return {"ok": False, "profile": profile, "result": self._result_service.get_level_result(level_number)}
        return {"ok": True, "profile": profile, "result": result_state}
