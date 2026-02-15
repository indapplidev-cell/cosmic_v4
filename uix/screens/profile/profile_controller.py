"""EN: Controller for profile screen actions and callbacks.
RU: РљРѕРЅС‚СЂРѕР»Р»РµСЂ РґР»СЏ РґРµР№СЃС‚РІРёР№ СЌРєСЂР°РЅР° РїСЂРѕС„РёР»СЏ Рё РєРѕР»Р±СЌРєРѕРІ.
"""

from dataclasses import dataclass, field
from typing import Callable

from ads.payment.balance_store import BalanceStore
from ads.payment.payment_math import format_balance
from data.gameplay.rating_storage import RatingStorage
from data.gameplay.record_store import RecordStore
from data.format.phone import format_phone, normalize_phone
from data.user_cache.user_cache_reader import get_user_cache
from data.user_cache.user_session import UserSession
from kivymd.app import MDApp
from manager.lang.lang_manager import t
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

    def __post_init__(self) -> None:
        """EN: Store app reference for navigation and state.
        RU: РЎРѕС…СЂР°РЅРёС‚СЊ СЃСЃС‹Р»РєСѓ РЅР° РїСЂРёР»РѕР¶РµРЅРёРµ РґР»СЏ РЅР°РІРёРіР°С†РёРё Рё СЃРѕСЃС‚РѕСЏРЅРёСЏ.
        """
        self._app = MDApp.get_running_app()

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
        best = RecordStore().get_best_score()
        no_data = t("common.no_data")

        if hasattr(self._app, "is_logged_in"):
            self._app.is_logged_in = UserSession().is_logged_in()
        if getattr(self._app, "is_logged_in", False):
            cache = get_user_cache() or {}
            login_raw = cache.get("login") or ""
            login_val = login_raw.strip() or no_data
            phone_val = cache.get("phone") or no_data
            tg_val = cache.get("tg") or no_data
            email = UserSession().get_email()
            val_email = email if email else no_data
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

        view.ids.val_record.text = str(best)
        points = RatingStorage().load_points()
        view.rating_text = str(points)
        balance = BalanceStore().get_balance()
        view.ids.val_balance.text = format_balance(balance)
        view.ids.val_email.text = val_email
        if phone_val == no_data:
            view.ids.val_phone.text = no_data
        else:
            view.ids.val_phone.text = format_phone(normalize_phone(phone_val))
        view.ids.val_tg.text = tg_val

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

