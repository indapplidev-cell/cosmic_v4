"""EN: Shared application shell with one persistent top/content/bottom layer.
RU: Общий shell приложения с одним постоянным top/content/bottom-слоем.
"""

from __future__ import annotations

from pathlib import Path

from data.user_cache.user_cache_reader import get_user_cache
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.logger import Logger
from kivy.metrics import dp
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.utils import platform as kivy_platform
from kivymd.uix.screen import MDScreen
from manager.lang.lang_manager import t

from uix.debug.debug_borders import apply_debug_borders_to_ids
from uix.screens.screen_manager import AppScreenManager

KV_PATH = Path(__file__).with_name("app_shell.kv")
Builder.load_file(str(KV_PATH))

APP_SHELL_DEBUG_IDS = [
    "topbar_container",
    "topbar",
    "lefttopbar",
    "top_left_custom_host",
    "midltopbar",
    "righttopbar",
    "top_right_custom_host",
    "content_container",
    "content_host",
    "bottom_container",
    "bottom_host",
]


class AppShell(MDScreen):
    """EN: Root shell that owns one persistent TopBar, ContentBar, BottomBar, and banner slot.
    RU: Корневой shell, который владеет единым постоянным TopBar, ContentBar, BottomBar и слотом баннера.

    EN: Logical screens stay inside an internal `ScreenManager`, while their reusable UI containers
    are mounted into the shared hosts exposed by this shell.
    RU: Логические экраны остаются внутри внутреннего `ScreenManager`, а их переиспользуемые UI-контейнеры
    монтируются в общие host-контейнеры, которые предоставляет этот shell.
    """

    def __init__(self, manager: AppScreenManager, **kwargs) -> None:
        """EN: Attach the logical screen manager and initialize shared shell state.
        RU: Подключить логический screen manager и инициализировать состояние общего shell.
        """
        super().__init__(**kwargs)
        self._manager = manager
        self._mounted_background: Widget | None = None
        self._mounted_content: Widget | None = None
        self._mounted_bottom: Widget | None = None
        self._mounted_top_left: Widget | None = None
        self._mounted_top_right: Widget | None = None
        self._bar_visibility = {"top": True, "content": True, "bottom": True}
        self._layout_frozen = False
        self.add_widget(manager)
        manager.opacity = 0
        manager.disabled = True
        manager.size_hint = (None, None)
        manager.size = Window.size
        manager.pos = (-10_000, -10_000)
        manager.attach_shell(self)
        self.bind(size=self._sync_hidden_manager_size)
        Window.bind(size=self._sync_hidden_manager_size)
        self._backspace_bound = False
        if kivy_platform in ("android", "ios"):
            Window.bind(on_key_down=self._on_window_key_down)
            self._backspace_bound = True
        apply_debug_borders_to_ids(self, APP_SHELL_DEBUG_IDS)
        self._bind_layout()

    @property
    def screen_manager(self) -> AppScreenManager:
        """EN: Return the hidden logical screen manager.
        RU: Вернуть скрытый логический screen manager.
        """
        return self._manager

    def get_banner_slot(self):
        """EN: Return the one persistent banner slot hosted in the shell top bar.
        RU: Вернуть единственный постоянный слот баннера, размещенный в top bar shell.
        """
        return self.ids.ads_banner_slot

    def set_title(self, text: str) -> None:
        """EN: Set shared top-left title text and remove any transient left widget.
        RU: Установить общий текст заголовка слева вверху и убрать временный левый виджет.
        """
        self.ids.top_left_title.text = str(text or "")
        self._replace_top_widget("left", None)
        self.ids.top_left_title.opacity = 1

    def set_user_info_visible(self, visible: bool) -> None:
        """EN: Show or hide the default user-info label in the shared top-right area.
        RU: Показать или скрыть стандартный label с данными пользователя в общей правой верхней области.
        """
        label = self.ids.top_right_user
        label.opacity = 1 if visible else 0
        label.disabled = not visible

    def refresh_user_info(self) -> None:
        """EN: Refresh nickname/no-data text from cached user profile for shared top-right label.
        RU: Обновить текст ника/«нет данных» из кэша профиля пользователя для общего правого верхнего label.
        """
        cache = get_user_cache() or {}
        nickname = str((cache.get("login") or "").strip())
        self.ids.top_right_user.text = nickname or t("common.no_data")

    def set_top_left_widget(self, widget: Widget | None) -> None:
        """EN: Replace title label with a custom left-top widget, e.g. gameplay score.
        RU: Заменить label заголовка кастомным левым верхним виджетом, например счётом gameplay.
        """
        self.ids.top_left_title.opacity = 0 if widget is not None else 1
        self._replace_top_widget("left", widget)

    def set_top_right_widget(self, widget: Widget | None) -> None:
        """EN: Replace default right-top user label with a custom widget, e.g. gameplay lives.
        RU: Заменить стандартный правый верхний label пользователя кастомным виджетом, например жизнями gameplay.
        """
        self.set_user_info_visible(widget is None)
        self._replace_top_widget("right", widget)

    def set_content_widget(self, widget: Widget | None) -> None:
        """EN: Mount current screen content widget into the shared content host.
        RU: Смонтировать content-виджет текущего экрана в общий content-host.
        """
        self._mounted_content = self._replace_host_widget("content_host", widget)

    def set_bottom_widget(self, widget: Widget | None) -> None:
        """EN: Mount current screen bottom widget into the shared bottom host.
        RU: Смонтировать bottom-виджет текущего экрана в общий bottom-host.
        """
        self._mounted_bottom = self._replace_host_widget("bottom_host", widget)

    def set_background_widget(self, widget: Widget | None) -> None:
        """EN: Mount screen-specific background/gameplay layer behind the shared bars.
        RU: Смонтировать экранно-специфичный background/gameplay-слой позади общих баров.
        """
        self._mounted_background = self._replace_host_widget("background_host", widget)

    def set_ads_visible(self, visible: bool) -> None:
        """EN: Hide/show the one persistent ad slot without destroying it.
        RU: Скрыть/показать единственный постоянный ad-slot без его уничтожения.
        """
        slot = self.ids.midltopbar
        slot.opacity = 1 if visible else 0
        slot.disabled = not visible

    def set_bar_visibility(self, *, top: bool, content: bool, bottom: bool) -> None:
        """EN: Toggle visibility of shared shell bars while preserving mounted widgets.
        RU: ??????????? ????????? ????? ????? shell, ???????? ??? ?????????????? ???????.
        """
        self._bar_visibility = {"top": bool(top), "content": bool(content), "bottom": bool(bottom)}
        self._apply_layout()

    def present_load_screen(self, widget: Widget) -> None:
        """EN: Present startup loading widget inside the shared content area with bars hidden.
        RU: Показать стартовый loading-виджет внутри общей content-области со скрытыми барами.
        """
        self.set_background_widget(None)
        self.set_content_widget(widget)
        self.set_bottom_widget(None)
        self.set_top_left_widget(None)
        self.set_top_right_widget(None)
        self.set_user_info_visible(False)
        self.set_ads_visible(False)
        self.set_bar_visibility(top=False, content=True, bottom=False)

    def freeze_layout(self) -> None:
        """EN: Temporarily block shell layout recalculation during transient fullscreen overlays.
        RU: ???????? ????????????? ???????? layout shell ?? ????? ??????????????? fullscreen-overlay.
        """
        self._layout_frozen = True

    def unfreeze_layout(self) -> None:
        """EN: Re-enable shell layout recalculation and immediately restore current bar geometry.
        RU: ????? ???????? ???????? layout shell ? ????? ???????????? ??????? ????????? ?????.
        """
        self._layout_frozen = False
        self._apply_layout()

    def _sync_hidden_manager_size(self, *_args) -> None:
        """EN: Keep the hidden manager non-zero-sized for KivyMD transitions while staying outside the visible shell.
        RU: Держать скрытый manager ненулевого размера для KivyMD transition, но оставлять его вне видимого shell.
        """
        self._manager.size = Window.size
        self._manager.pos = (-10_000, -10_000)

    def _replace_host_widget(self, host_id: str, widget: Widget | None) -> Widget | None:
        """EN: Replace the only child of a host container with the provided widget.
        RU: Заменить единственного потомка host-контейнера переданным виджетом.
        """
        host = self.ids[host_id]
        target = self._resolve_widget(widget)
        host.clear_widgets()
        if target is not None:
            parent = self._safe_widget_parent(target)
            if parent is not None:
                parent.remove_widget(target)
            self._apply_host_constraints(host_id, target)
            host.add_widget(target)
        self._log_host_mount(host_id, target)
        return target

    def _resolve_widget(self, widget: Widget | None) -> Widget | None:
        """EN: Convert Kivy weak-proxy widgets from `ids` into strong widget references for shell mounting.
        RU: Преобразовать weak-proxy-виджеты Kivy из `ids` в сильные ссылки на виджеты для монтирования в shell.
        """
        if widget is None:
            return None
        try:
            return getattr(widget, "__self__", widget)
        except ReferenceError:
            return None

    def _safe_widget_parent(self, widget: Widget | None) -> Widget | None:
        """EN: Read widget parent without crashing when the incoming object is an expired weak proxy.
        RU: Получить parent виджета без падения, если пришёл уже истёкший weak proxy.
        """
        if widget is None:
            return None
        try:
            return getattr(widget, "parent", None)
        except ReferenceError:
            return None

    def _apply_host_constraints(self, host_id: str, widget: Widget) -> None:
        """EN: Normalize mounted widget geometry so screen-local layout code cannot collapse shared shell hosts.
        RU: Нормализовать геометрию смонтированного виджета, чтобы локальные layout-функции экранов не ломали общие host-области shell.
        """
        if hasattr(widget, "adaptive_height"):
            widget.adaptive_height = False
        if hasattr(widget, "adaptive_size"):
            widget.adaptive_size = False
        widget.size_hint_x = 1
        widget.pos_hint = {}

        if host_id == "background_host":
            widget.size_hint = (1, 1)
            widget.pos = (0, 0)
            return

        if host_id == "content_host":
            widget.size_hint_y = 1
            return

        if host_id == "bottom_host":
            widget.size_hint_y = 1
            return

        widget.size_hint_y = 1

    def _refresh_mounted_widgets(self) -> None:
        """EN: Re-apply host geometry constraints after shell resize so content and bottom bars stay attached to the shared layout.
        RU: Повторно применить ограничения геометрии host-областей после ресайза shell, чтобы content и bottom bar оставались приклеены к общему layout.
        """
        for host_id, widget in (
            ("background_host", self._mounted_background),
            ("content_host", self._mounted_content),
            ("bottom_host", self._mounted_bottom),
            ("top_left_custom_host", self._mounted_top_left),
            ("top_right_custom_host", self._mounted_top_right),
        ):
            target = self._resolve_widget(widget)
            if target is not None:
                self._apply_host_constraints(host_id, target)

    def _replace_top_widget(self, side: str, widget: Widget | None) -> None:
        """EN: Replace optional transient widget in left or right shared top slot.
        RU: Заменить необязательный временный виджет в левом или правом общем top-слоте.
        """
        host_id = "top_left_custom_host" if side == "left" else "top_right_custom_host"
        mounted_attr = "_mounted_top_left" if side == "left" else "_mounted_top_right"
        mounted = self._replace_host_widget(host_id, widget)
        setattr(self, mounted_attr, mounted)

    def _apply_bar_visibility(self) -> None:
        """EN: Apply non-destructive visibility to the fixed top, content, and bottom shell zones.
        RU: ????????? ????????????? ????????? ? ????????????? ???????, ??????? ? ?????? ????? shell.
        """
        self._set_area_visibility(self.ids.topbar_container, self._bar_visibility["top"])
        self._set_area_visibility(self.ids.content_container, self._bar_visibility["content"])
        self._set_area_visibility(self.ids.bottom_container, self._bar_visibility["bottom"])

    def _set_area_visibility(self, widget: Widget, visible: bool) -> None:
        """EN: Apply non-destructive visibility state to a shared shell area.
        RU: ????????? ????????????? ????????? ????????? ? ????? ??????? shell.
        """
        widget.opacity = 1 if visible else 0
        widget.disabled = not visible

    def _apply_layout(self, *_args) -> None:
        """EN: Apply current shell geometry unless layout is frozen by a transient overlay.
        RU: ????????? ??????? ????????? shell, ???? layout ?? ????????? ????????? overlay.
        """
        if self._layout_frozen:
            return
        win_w, win_h = Window.size
        ids = self.ids
        top_h = (win_h * 0.15) if self._bar_visibility["top"] else 0
        bottom_h = (win_h * 0.30) if self._bar_visibility["bottom"] else 0
        content_h = (win_h * 0.55) if self._bar_visibility["content"] else 0
        used_h = top_h + content_h + bottom_h
        if used_h > win_h and used_h > 0:
            scale = win_h / used_h
            top_h *= scale
            content_h *= scale
            bottom_h *= scale

        ids.shell_root.pos = (0, 0)
        ids.shell_root.size = (win_w, win_h)
        ids.background_host.pos = (0, 0)
        ids.background_host.size = (win_w, win_h)
        ids.bar_layer.pos = (0, 0)
        ids.bar_layer.size = (win_w, win_h)

        ids.topbar_container.pos = (0, win_h - top_h)
        ids.topbar_container.size = (win_w, top_h)
        ids.topbar.size = ids.topbar_container.size

        ids.content_container.pos = (0, bottom_h)
        ids.content_container.size = (win_w, content_h)
        ids.content_host.size = ids.content_container.size
        ids.content_host.pos = (0, 0)

        ids.bottom_container.pos = (0, 0)
        ids.bottom_container.size = (win_w, bottom_h)
        ids.bottom_host.size = ids.bottom_container.size

        ids.lefttopbar.size_hint = (0.2, 1)
        ids.midltopbar.size_hint = (0.6, 1)
        ids.righttopbar.size_hint = (0.2, 1)

        self._apply_bar_visibility()
        self._sync_hidden_manager_size()
        self._refresh_mounted_widgets()
        Clock.schedule_once(self._log_shell_sizes, 0)

    def _bind_layout(self) -> None:
        """EN: Bind shell geometry recalculation to window-size changes once.
        RU: ???? ??? ????????? ???????? ????????? shell ? ????????? ??????? ????.
        """
        if not getattr(self, "_layout_bound", False):
            Window.bind(size=self._apply_layout)
            self._layout_bound = True
        self._apply_layout()

    def _log_shell_sizes(self, *_args) -> None:
        """EN: Emit one compact shell geometry log with realized root/top/content/bottom sizes after layout.
        RU: Вывести один компактный лог геометрии shell с фактическими размерами root/top/content/bottom после раскладки.
        """
        ids = self.ids
        Logger.info(
            "[UI] shell sizes root=%s top=%s content=%s bottom=%s"
            % (
                tuple(round(float(v), 2) for v in ids.shell_root.size),
                round(float(ids.topbar.height), 2),
                round(float(ids.content_host.height), 2),
                round(float(ids.bottom_host.height), 2),
            )
        )

    def _log_host_mount(self, host_id: str, widget: Widget | None) -> None:
        """EN: Log what widget is currently mounted into a shared host to diagnose empty-content regressions.
        RU: Логировать, какой виджет сейчас смонтирован в общий host, чтобы диагностировать регрессии с пустым content.
        """
        host = self.ids[host_id]
        Logger.info(
            "[UI] shell mount host=%s widget=%s children=%s"
            % (
                host_id,
                widget.__class__.__name__ if widget is not None else "None",
                len(host.children),
            )
        )

    def _on_window_key_down(self, _window, key, _scancode, _codepoint, _modifiers):
        """EN: Normalize mobile backspace/delete for focused text inputs inside the shell.
        RU: Нормализовать mobile backspace/delete для сфокусированных text-input внутри shell.
        """
        if kivy_platform not in ("android", "ios"):
            return False
        if key not in (8, 67, 112, 127):
            return False

        focused = getattr(Window, "keyboard_focused", None)
        if not isinstance(focused, TextInput):
            return False

        mode = "bkspc" if key in (8, 67) else "del"
        focused.do_backspace(mode=mode)
        return True

    def on_touch_down(self, touch):
        """EN: Hide mobile keyboard when user taps outside focused input in shared shell hosts.
        RU: Скрыть mobile-клавиатуру, когда пользователь тапает вне сфокусированного поля в общих host-областях shell.
        """
        if kivy_platform in ("android", "ios"):
            focused = getattr(Window, "keyboard_focused", None)
            if isinstance(focused, TextInput) and not focused.collide_point(*touch.pos):
                focused.focus = False
                try:
                    Window.release_all_keyboards()
                except Exception:
                    pass
        return super().on_touch_down(touch)

