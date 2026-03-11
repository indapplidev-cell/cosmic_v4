"""EN: Controller for profile screen actions and callbacks.
RU: РљРѕРЅС‚СЂРѕР»Р»РµСЂ РґР»СЏ РґРµР№СЃС‚РІРёР№ СЌРєСЂР°РЅР° РїСЂРѕС„РёР»СЏ Рё РєРѕР»Р±СЌРєРѕРІ.
"""

from dataclasses import dataclass, field
from threading import Thread
from typing import Callable

from ads.payment.balance_store import BalanceStore
from ads.payment.payment_math import format_balance
from kivy.clock import Clock
from data.gameplay.rating_storage import RatingStorage
from data.gameplay.record_store import RecordStore
from data.format.phone import format_phone, normalize_phone
from data.user_cache.user_session import UserSession
from kivymd.app import MDApp
from manager import api_client
from manager.lang.lang_manager import t
from manager.user_snapshot_store import UserSnapshotStore
from uix.screens.routes import PROFILE_CHANGE


def _noop() -> None:
    """EN: Default no-op callback.
    RU: РљРѕР»Р±СЌРє РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ Р±РµР· РґРµР№СЃС‚РІРёР№.
    """
    return


@dataclass(slots=True)
class ProfileScreenController:
    """EN: Dispatch-only controller for the profile screen.
    RU: РљРѕРЅС‚СЂРѕР»Р»РµСЂ С‚РѕР»СЊРєРѕ РґР»СЏ РґРёСЃРїРµС‚С‡РµСЂРёР·Р°С†РёРё СЌРєСЂР°РЅР° РїСЂРѕС„РёР»СЏ.
    """

    on_back: Callable[[], None] = _noop
    on_refresh: Callable[[], None] = _noop
    on_payout: Callable[[], None] = _noop
    on_login: Callable[[], None] = _noop
    _app: object = field(init=False, repr=False)
    _snapshot_store: UserSnapshotStore = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """EN: Store app reference for navigation and state.
        RU: РЎРѕС…СЂР°РЅРёС‚СЊ СЃСЃС‹Р»РєСѓ РЅР° РїСЂРёР»РѕР¶РµРЅРёРµ РґР»СЏ РЅР°РІРёРіР°С†РёРё Рё СЃРѕСЃС‚РѕСЏРЅРёСЏ.
        """
        self._app = MDApp.get_running_app()
        self._snapshot_store = UserSnapshotStore()

    def back(self) -> None:
        """EN: Dispatch back action.
        RU: Р”РёСЃРїРµС‚С‡РµСЂРёР·РѕРІР°С‚СЊ РґРµР№СЃС‚РІРёРµ РЅР°Р·Р°Рґ.
        """
        self.on_back()

    def refresh(self) -> None:
        """EN: Dispatch refresh action.
        RU: Р”РёСЃРїРµС‚С‡РµСЂРёР·РѕРІР°С‚СЊ РґРµР№СЃС‚РІРёРµ РѕР±РЅРѕРІР»РµРЅРёСЏ.
        """
        self.on_refresh()

    def refresh_profile_cards(self, view) -> None:
        """EN: Fill profile top bar and card texts on refresh.
        RU: Р—Р°РїРѕР»РЅРёС‚СЊ РІРµСЂС…РЅСЋСЋ РїР°РЅРµР»СЊ Рё С‚РµРєСЃС‚С‹ РєР°СЂС‚РѕС‡РµРє РїСЂРѕС„РёР»СЏ РїСЂРё РѕР±РЅРѕРІР»РµРЅРёРё.
        """
        no_data = t("common.no_data")
        snapshot = self._snapshot_store.load()

        if hasattr(self._app, "is_logged_in"):
            self._app.is_logged_in = UserSession().is_logged_in()
        if getattr(self._app, "is_logged_in", False):
            login_raw = snapshot.get("login") or ""
            login_val = login_raw.strip() or no_data
            phone_val = snapshot.get("phone") or no_data
            tg_val = snapshot.get("telegram") or snapshot.get("telegram_username") or no_data
            val_email = str((snapshot.get("email") or UserSession().get_email() or "").strip()) or no_data
            view.ids.profile_top_right_login.text = login_val
        else:
            login_val = no_data
            phone_val = no_data
            tg_val = no_data
            val_email = no_data
            view.ids.profile_top_right_login.text = no_data

        view.ids.lbl_record_title.text = t("profile.card.record")
        view.ids.lbl_rating_title.text = t("profile.card.rating")
        view.ids.lbl_balance_title.text = t("profile.card.balance")
        view.ids.lbl_email_title.text = t("profile.card.email")
        view.ids.lbl_phone_title.text = t("profile.card.phone")
        view.ids.lbl_tg_title.text = t("profile.card.tg")

        record, rating, balance = self._snapshot_store.get_game()
        print(
            f"[Profile] profile_game local_cache: r={record}, rating={rating}, bal={balance}",
            flush=True,
        )
        view.ids.val_record.text = str(int(record))
        view.rating_text = str(int(rating))
        view.ids.val_balance.text = format_balance(float(balance))
        view.ids.val_email.text = val_email
        if phone_val == no_data:
            view.ids.val_phone.text = no_data
        else:
            view.ids.val_phone.text = format_phone(normalize_phone(phone_val))
        view.ids.val_tg.text = tg_val
        self._refresh_profile_from_server_async(view)

    def _refresh_profile_from_server_async(self, view) -> None:
        """EN: Fetch latest profile snapshot from server in background and refresh UI.
        RU: Фоново получить актуальный snapshot профиля с сервера и обновить UI.
        """

        snapshot = self._snapshot_store.load()
        user_id = int(snapshot.get("user_id") or 0)
        if user_id <= 0:
            return

        def _worker() -> None:
            ok, payload = api_client.auth_me(user_id, timeout=6)
            if not ok or not isinstance(payload, dict) or not payload.get("ok"):
                Clock.schedule_once(lambda *_: setattr(view, "is_offline_profile", True), 0)
                return

            user = payload.get("user") if isinstance(payload, dict) else None
            if not isinstance(user, dict):
                Clock.schedule_once(lambda *_: setattr(view, "is_offline_profile", True), 0)
                return

            self._snapshot_store.save(user)
            record = int(user.get("record") or 0)
            rating = int(user.get("rating") or 0)
            balance = round(float(user.get("balance") or 0.0), 3)
            print(
                f"[Profile] profile_game server: r={record}, rating={rating}, bal={balance}",
                flush=True,
            )
            # Keep legacy storages in sync for other screens while Profile remains server-first.
            RecordStore().set_best_score(record)
            RatingStorage().save_points(rating)
            BalanceStore().set_balance(float(balance))
            Clock.schedule_once(lambda *_: self._apply_server_snapshot(view), 0)

        Thread(target=_worker, daemon=True).start()

    def _apply_server_snapshot(self, view) -> None:
        """EN: Apply already saved server snapshot to profile widgets.
        RU: Применить уже сохраненный серверный snapshot к виджетам профиля.
        """

        no_data = t("common.no_data")
        snapshot = self._snapshot_store.load()
        record, rating, balance = self._snapshot_store.get_game()
        login_val = str((snapshot.get("login") or "").strip()) or no_data
        phone_val = str((snapshot.get("phone") or "").strip()) or no_data
        tg_val = str((snapshot.get("telegram") or snapshot.get("telegram_username") or "").strip()) or no_data
        email_val = str((snapshot.get("email") or "").strip()) or no_data

        view.ids.profile_top_right_login.text = login_val
        view.ids.val_record.text = str(int(record))
        view.rating_text = str(int(rating))
        view.ids.val_balance.text = format_balance(float(balance))
        view.ids.val_email.text = email_val
        if phone_val == no_data:
            view.ids.val_phone.text = no_data
        else:
            view.ids.val_phone.text = format_phone(normalize_phone(phone_val))
        view.ids.val_tg.text = tg_val
        setattr(view, "is_offline_profile", False)

    def payout(self) -> None:
        """EN: Dispatch payout action.
        RU: Р”РёСЃРїРµС‚С‡РµСЂРёР·РѕРІР°С‚СЊ РґРµР№СЃС‚РІРёРµ РІС‹РїР»Р°С‚С‹.
        """
        self.on_payout()

    def login(self) -> None:
        """EN: Dispatch login action.
        RU: Р”РёСЃРїРµС‚С‡РµСЂРёР·РѕРІР°С‚СЊ РґРµР№СЃС‚РІРёРµ РІС…РѕРґР°.
        """
        self.on_login()

    def open_profile_change(self) -> None:
        """EN: Open profile change screen.
        RU: РћС‚РєСЂС‹С‚СЊ СЌРєСЂР°РЅ СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёСЏ РїСЂРѕС„РёР»СЏ.
        """
        self._app.change_screen(PROFILE_CHANGE)

