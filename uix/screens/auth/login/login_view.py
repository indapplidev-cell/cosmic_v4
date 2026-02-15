"""EN: View for the login screen.
RU: Представление экрана входа.
"""

from pathlib import Path

from data.user_cache.user_session import UserSession
from kivy.clock import Clock
from kivy.lang import Builder
from kivymd.uix.screen import MDScreen
from manager.auth.login_manager import LoginManager
from manager.lang.lang_manager import t
from uix.debug.debug_borders import apply_debug_borders_to_ids
from uix.screens.common.button_text_style import apply_button_text_style, caps
from uix.screens.common.password_eye import wire_password_eye

from .login_controller import LoginController
from .login_layout import LOGIN_DEBUG_IDS, apply_login_layout
from .login_vm import LoginVM

KV_PATH = Path(__file__).with_name("login.kv")
Builder.load_file(str(KV_PATH))


class LoginScreenView(MDScreen):
    """EN: Login screen view that wires layout, VM, and controller.
    RU: Представление входа, связывающее раскладку, VM и контроллер.
    """

    def on_kv_post(self, base_widget) -> None:
        """EN: Apply layout after KV is ready.
        RU: Применить раскладку после загрузки KV.
        """
        apply_login_layout(self)
        wire_password_eye(self.ids.password_field, self.ids.password_eye_btn, start_hidden=True)
        apply_button_text_style(
            self,
            [
                self.ids.forgot_btn_text,
                self.ids.login_btn_text,
                self.ids.register_btn_text,
            ],
        )
        apply_debug_borders_to_ids(self, LOGIN_DEBUG_IDS)

    def configure(self, vm: LoginVM, controller: LoginController) -> None:
        """EN: Configure texts and bind callbacks.
        RU: Настроить тексты и привязать колбэки.
        """
        self.controller = controller
        self.ids.title_lbl.text = vm.title
        self.ids.email_hint.text = vm.email_hint
        self.ids.password_hint.text = vm.password_hint
        self.ids.forgot_btn_text.text = caps(vm.forgot_text)
        self.ids.login_btn_text.text = caps(vm.login_text)
        self.ids.register_btn_text.text = caps(vm.register_text)
        self.set_error(vm.error_text)

        self.ids.login_btn.on_release = self._on_login_pressed
        self.ids.forgot_btn.on_release = controller.forgot
        self.ids.register_btn.on_release = controller.register

    def on_pre_enter(self, *args) -> None:
        """EN: Ensure email field focus on screen entry.
        RU: Обеспечить фокус на поле email при входе на экран.
        """
        super().on_pre_enter(*args)

        def _focus(_dt: float) -> None:
            """EN: Move focus to email field after layout is ready.
            RU: Перевести фокус на поле email после готовности раскладки.
            """
            self.ids.password_field.focus = False
            self.ids.email_field.focus = True
            self.ids.email_field.cursor = (len(self.ids.email_field.text or ""), 0)

        Clock.schedule_once(_focus, 0)

    def _on_login_pressed(self) -> None:
        """EN: Validate credentials before dispatching login.
        RU: Проверить учетные данные перед диспетчеризацией входа.
        """
        email = (self.ids.email_field.text or "").strip()
        password = self.ids.password_field.text or ""
        if not LoginManager.check(email, password):
            self.set_error(t("login.error.invalid_credentials"))
            return
        self.set_error("")
        UserSession().set_email(email)
        self.controller.login()
        self._clear_fields()

    def set_error(self, text: str) -> None:
        """EN: Set error text visibility.
        RU: Установить видимость текста ошибки.
        """
        self.ids.error_lbl.text = text
        self.ids.error_lbl.opacity = 1 if text else 0

    def _clear_fields(self) -> None:
        """EN: Clear login input fields after successful validation.
        RU: Очистить поля входа после успешной проверки.
        """
        self.ids.email_field.text = ""
        self.ids.password_field.text = ""
