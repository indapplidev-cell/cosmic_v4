# -*- coding: utf-8 -*-
"""EN: Runtime bridge that layers survive_timed business rules over existing gameplay loop.
RU: Runtime-РјРѕСЃС‚, РєРѕС‚РѕСЂС‹Р№ РЅР°РєР»Р°РґС‹РІР°РµС‚ Р±РёР·РЅРµСЃ-Р»РѕРіРёРєСѓ survive_timed РїРѕРІРµСЂС… СЃСѓС‰РµСЃС‚РІСѓСЋС‰РµРіРѕ РёРіСЂРѕРІРѕРіРѕ С†РёРєР»Р°.
"""

from __future__ import annotations

from time import perf_counter

from client.application.auth import auth_backend
from client.application.gameplay.modes.survive_timed.level_bootstrap_service import SurviveTimedLevelBootstrapService
from client.application.gameplay.modes.survive_timed.level_progress_service import SurviveTimedLevelProgressService
from client.application.gameplay.modes.survive_timed.level_result_service import SurviveTimedLevelResultService
from shared.contracts.survive_timed import SurviveTimedLevelProfile


class SurviveTimedRuntimeBridge:
    """EN: Own active survive_timed run state, win/fail evaluation, and progress/result persistence.
    RU: Р’Р»Р°РґРµС‚СЊ СЃРѕСЃС‚РѕСЏРЅРёРµРј Р°РєС‚РёРІРЅРѕРіРѕ Р·Р°Р±РµРіР° survive_timed, РїСЂРѕРІРµСЂРєРѕР№ win/fail Рё СЃРѕС…СЂР°РЅРµРЅРёРµРј progress/result.
    """

    def __init__(
        self,
        bootstrap_service: SurviveTimedLevelBootstrapService | None = None,
        progress_service: SurviveTimedLevelProgressService | None = None,
        result_service: SurviveTimedLevelResultService | None = None,
    ) -> None:
        """EN: Store survive_timed services required for runtime session orchestration.
        RU: РЎРѕС…СЂР°РЅРёС‚СЊ survive_timed СЃРµСЂРІРёСЃС‹, РЅРµРѕР±С…РѕРґРёРјС‹Рµ РґР»СЏ orchestration runtime-СЃРµСЃСЃРёРё.
        """

        self._progress_service = progress_service or SurviveTimedLevelProgressService()
        self._result_service = result_service or SurviveTimedLevelResultService()
        self._bootstrap_service = bootstrap_service or SurviveTimedLevelBootstrapService(self._progress_service)
        self._active_profile: SurviveTimedLevelProfile | None = None
        self._run_started_at: float | None = None
        self._run_finalized = False

    def resolve_start_level_number(self) -> int:
        """EN: Return survive_timed level number that should start on next run.
        RU: Р’РµСЂРЅСѓС‚СЊ РЅРѕРјРµСЂ СѓСЂРѕРІРЅСЏ survive_timed, РєРѕС‚РѕСЂС‹Р№ РґРѕР»Р¶РµРЅ СЃС‚Р°СЂС‚РѕРІР°С‚СЊ РІ СЃР»РµРґСѓСЋС‰РµРј Р·Р°Р±РµРіРµ.
        """

        return self._bootstrap_service.resolve_start_level_number()

    def activate_level(self, level_number: int) -> SurviveTimedLevelProfile:
        """EN: Activate survive_timed level and clear any previous run state.
        RU: РђРєС‚РёРІРёСЂРѕРІР°С‚СЊ СѓСЂРѕРІРµРЅСЊ survive_timed Рё СЃР±СЂРѕСЃРёС‚СЊ СЃРѕСЃС‚РѕСЏРЅРёРµ РїСЂРµРґС‹РґСѓС‰РµРіРѕ Р·Р°Р±РµРіР°.
        """

        self._active_profile = self._bootstrap_service.activate_level(level_number)
        self._run_started_at = None
        self._run_finalized = False
        return self._active_profile

    def begin_run(self) -> SurviveTimedLevelProfile:
        """EN: Start survive_timed run timer exactly once for the currently active level.
        RU: Р—Р°РїСѓСЃС‚РёС‚СЊ С‚Р°Р№РјРµСЂ survive_timed СЂРѕРІРЅРѕ РѕРґРёРЅ СЂР°Р· РґР»СЏ С‚РµРєСѓС‰РµРіРѕ Р°РєС‚РёРІРЅРѕРіРѕ СѓСЂРѕРІРЅСЏ.
        """

        profile = self.get_active_profile()
        self._run_started_at = perf_counter()
        self._run_finalized = False
        return profile

    def get_active_profile(self) -> SurviveTimedLevelProfile:
        """EN: Return active survive_timed profile, resolving bootstrap state when needed.
        RU: Р’РµСЂРЅСѓС‚СЊ Р°РєС‚РёРІРЅС‹Р№ РїСЂРѕС„РёР»СЊ survive_timed, РїСЂРё РЅРµРѕР±С…РѕРґРёРјРѕСЃС‚Рё СЂРµР·РѕР»РІСЏ bootstrap-state.
        """

        if self._active_profile is None:
            self._active_profile = self._bootstrap_service.get_active_profile()
        return self._active_profile

    def get_elapsed_sec(self) -> float:
        """EN: Return elapsed survive_timed run duration or zero before the run starts.
        RU: Р’РµСЂРЅСѓС‚СЊ РїСЂРѕС€РµРґС€РµРµ РІСЂРµРјСЏ survive_timed РёР»Рё РЅРѕР»СЊ РґРѕ СЃС‚Р°СЂС‚Р° Р·Р°Р±РµРіР°.
        """

        if self._run_started_at is None:
            return 0.0
        return max(perf_counter() - float(self._run_started_at), 0.0)

    def is_success_ready(self) -> bool:
        """EN: Return whether the active survive_timed run already reached target survival time.
        RU: Р’РµСЂРЅСѓС‚СЊ, РґРѕСЃС‚РёРі Р»Рё Р°РєС‚РёРІРЅС‹Р№ Р·Р°Р±РµРі survive_timed С†РµР»РµРІРѕРіРѕ РІСЂРµРјРµРЅРё РІС‹Р¶РёРІР°РЅРёСЏ.
        """

        if self._run_finalized or self._run_started_at is None:
            return False
        profile = self.get_active_profile()
        return self.get_elapsed_sec() >= float(profile.target_survival_sec)

    def build_hud_payload(self) -> dict:
        """EN: Return survive_timed HUD data for current level and timer overlay.
        RU: Р’РµСЂРЅСѓС‚СЊ HUD-РґР°РЅРЅС‹Рµ survive_timed РґР»СЏ С‚РµРєСѓС‰РµРіРѕ СѓСЂРѕРІРЅСЏ Рё С‚Р°Р№РјРµСЂРЅРѕРіРѕ overlay.
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
        RU: РЎРѕС…СЂР°РЅРёС‚СЊ СѓСЃРїРµС… survive_timed С‡РµСЂРµР· server-authoritative sync РёР»Рё guest fallback.
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
        RU: РЎРѕС…СЂР°РЅРёС‚СЊ РЅРµСѓСЃРїРµС… survive_timed С‡РµСЂРµР· server-authoritative sync РёР»Рё guest fallback.
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
        RU: РЎРѕР±СЂР°С‚СЊ РѕРґРёРЅ backend payload survive_timed РІ РјРёР»Р»РёСЃРµРєСѓРЅРґР°С….
        """

        return {
            "level_number": int(level_number),
            "survival_ms": max(int(round(float(survival_sec) * 1000.0)), 0),
        }

    def _record_authorized_success(self, level_number: int, survival_sec: float) -> dict:
        """EN: Submit survive_timed success first and then mirror backend result/progress locally.
        RU: РЎРЅР°С‡Р°Р»Р° РѕС‚РїСЂР°РІРёС‚СЊ СѓСЃРїРµС… survive_timed РЅР° СЃРµСЂРІРµСЂ, Р·Р°С‚РµРј РѕС‚Р·РµСЂРєР°Р»РёС‚СЊ backend result/progress Р»РѕРєР°Р»СЊРЅРѕ.
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
        RU: РЎРЅР°С‡Р°Р»Р° РѕС‚РїСЂР°РІРёС‚СЊ fail survive_timed РЅР° СЃРµСЂРІРµСЂ, Р·Р°С‚РµРј РѕС‚Р·РµСЂРєР°Р»РёС‚СЊ backend result Р»РѕРєР°Р»СЊРЅРѕ.
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

