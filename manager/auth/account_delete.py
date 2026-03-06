from kivy.uix.widget import Widget
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.dialog import (
    MDDialog,
    MDDialogButtonContainer,
    MDDialogHeadlineText,
    MDDialogSupportingText,
)

from data.user_cache.user_cache_reader import get_user_cache
from manager import auth_backend
from manager.lang.lang_manager import t
from manager.auth.account_wipe import wipe_all_user_data


_dialog = None


def confirm_delete_account(on_deleted, on_cancel) -> None:
    """
    EN: Shows account deletion confirmation dialog and executes callbacks.
    RU: Показывает диалог подтверждения удаления аккаунта и вызывает колбэки.
    """
    global _dialog
    if _dialog:
        try:
            _dialog.dismiss()
        except Exception:
            pass
        _dialog = None

    def _close():
        global _dialog
        if _dialog:
            _dialog.dismiss()
        _dialog = None

    def _sure(*_):
        _close()
        cache = get_user_cache() or {}
        user_id_raw = cache.get("user_id")

        user_id = None
        if isinstance(user_id_raw, int):
            user_id = user_id_raw
        elif isinstance(user_id_raw, str) and user_id_raw.isdigit():
            user_id = int(user_id_raw)

        deleted = False
        if user_id is not None:
            deleted = auth_backend.delete_account(user_id)
        else:
            email = (cache.get("email") or "").strip()
            if email:
                ok_resolve, payload = auth_backend.resolve_user_id(email)
                if ok_resolve:
                    deleted = auth_backend.delete_account(int(payload))

        if not deleted:
            on_cancel()
            return

        wipe_all_user_data()
        on_deleted()

    def _stay(*_):
        _close()
        on_cancel()

    _dialog = MDDialog(
        MDDialogHeadlineText(
            text=t("settings.delete_confirm.title"),
            halign="left",
        ),
        MDDialogSupportingText(
            text=t("settings.delete_confirm.text"),
            halign="left",
        ),
        MDDialogButtonContainer(
            Widget(),
            MDButton(
                MDButtonText(text=t("settings.delete_confirm.cancel")),
                style="text",
                on_release=_stay,
            ),
            MDButton(
                MDButtonText(text=t("settings.delete_confirm.ok")),
                style="text",
                on_release=_sure,
            ),
            spacing="8dp",
        ),
        auto_dismiss=False,
    )
    _dialog.open()
