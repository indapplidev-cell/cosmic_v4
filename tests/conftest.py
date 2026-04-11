from __future__ import annotations

import sys
import types


def _simple_type(name: str):
    return type(name, (), {})


class _FakeEvent:
    def __init__(self, callback, interval) -> None:
        self.callback = callback
        self.interval = interval
        self.cancelled = False

    def cancel(self) -> None:
        self.cancelled = True


class _FakeClock:
    @staticmethod
    def schedule_once(callback, delay=0.0):
        return _FakeEvent(callback, delay)

    @staticmethod
    def schedule_interval(callback, interval):
        return _FakeEvent(callback, interval)


class _FakeKeyboard:
    def __init__(self) -> None:
        self.closed = False

    def bind(self, **_kwargs) -> None:
        return None

    def unbind(self, **_kwargs) -> None:
        return None

    def release(self) -> None:
        self.closed = True

    @staticmethod
    def keycode_to_string(key):
        return str(key)


class _FakeWindow:
    keyboard_focused = None

    @staticmethod
    def bind(**_kwargs) -> None:
        return None

    @staticmethod
    def unbind(**_kwargs) -> None:
        return None

    @staticmethod
    def request_keyboard(_closed_cb, _widget=None):
        return _FakeKeyboard()


class _FakeInstructionGroup:
    def __init__(self) -> None:
        self.children = []

    def add(self, instruction) -> None:
        self.children.append(instruction)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeCanvas(_FakeInstructionGroup):
    def __init__(self) -> None:
        super().__init__()
        self.after = _FakeInstructionGroup()


class _FakeWidget:
    def __init__(self, **kwargs) -> None:
        self.x = kwargs.get("x", 0)
        self.y = kwargs.get("y", 0)
        self._size = (0, 0)
        self.size = kwargs.get("size", (0, 0))
        self.canvas = _FakeCanvas()
        self.opacity = kwargs.get("opacity", 1)

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, value) -> None:
        self._size = tuple(value)
        self.width, self.height = self._size

    def bind(self, **_kwargs) -> None:
        return None

    def unbind(self, **_kwargs) -> None:
        return None

    def collide_point(self, x, y) -> bool:
        return self.x <= x <= (self.x + self.width) and self.y <= y <= (self.y + self.height)


class _FakeInstruction:
    def __init__(self, *args, **kwargs) -> None:
        self.points = list(kwargs.get("points", []))
        self.width = float(kwargs.get("width", 1.0))
        self.rgba = kwargs.get("rgba", (0, 0, 0, 0))


def _install_kivy_stubs() -> None:
    kivy_module = types.ModuleType("kivy")
    app_module = types.ModuleType("kivy.app")
    app_module.App = type("App", (), {"get_running_app": staticmethod(lambda: None)})
    clock_module = types.ModuleType("kivy.clock")
    clock_module.Clock = _FakeClock
    logger_module = types.ModuleType("kivy.logger")
    logger_module.Logger = type("Logger", (), {"info": staticmethod(lambda *_args, **_kwargs: None)})
    lang_module = types.ModuleType("kivy.lang")
    lang_module.Builder = type(
        "Builder",
        (),
        {
            "load_file": staticmethod(lambda *_args, **_kwargs: None),
            "load_string": staticmethod(lambda *_args, **_kwargs: None),
        },
    )
    properties_module = types.ModuleType("kivy.properties")
    properties_module.StringProperty = lambda default="", **_kwargs: default
    properties_module.NumericProperty = lambda default=0, **_kwargs: default
    properties_module.BooleanProperty = lambda default=False, **_kwargs: default
    properties_module.ObjectProperty = lambda default=None, **_kwargs: default

    utils_module = types.ModuleType("kivy.utils")
    utils_module.platform = "win"

    core_module = types.ModuleType("kivy.core")
    window_module = types.ModuleType("kivy.core.window")
    window_module.Window = _FakeWindow
    core_module.window = window_module

    uix_module = types.ModuleType("kivy.uix")
    widget_module = types.ModuleType("kivy.uix.widget")
    widget_module.Widget = _FakeWidget
    boxlayout_module = types.ModuleType("kivy.uix.boxlayout")
    boxlayout_module.BoxLayout = _simple_type("BoxLayout")
    button_module = types.ModuleType("kivy.uix.button")
    button_module.Button = _simple_type("Button")
    label_module = types.ModuleType("kivy.uix.label")
    label_module.Label = _simple_type("Label")
    popup_module = types.ModuleType("kivy.uix.popup")
    popup_module.Popup = _simple_type("Popup")
    scrollview_module = types.ModuleType("kivy.uix.scrollview")
    scrollview_module.ScrollView = _simple_type("ScrollView")
    anchorlayout_module = types.ModuleType("kivy.uix.anchorlayout")
    anchorlayout_module.AnchorLayout = _simple_type("AnchorLayout")
    gridlayout_module = types.ModuleType("kivy.uix.gridlayout")
    gridlayout_module.GridLayout = _simple_type("GridLayout")
    modalview_module = types.ModuleType("kivy.uix.modalview")
    modalview_module.ModalView = _simple_type("ModalView")
    screenmanager_module = types.ModuleType("kivy.uix.screenmanager")
    screenmanager_module.NoTransition = _simple_type("NoTransition")
    textinput_module = types.ModuleType("kivy.uix.textinput")
    textinput_module.TextInput = type("TextInput", (), {})
    uix_module.widget = widget_module
    uix_module.textinput = textinput_module

    graphics_module = types.ModuleType("kivy.graphics")
    context_module = types.ModuleType("kivy.graphics.context_instructions")
    instructions_module = types.ModuleType("kivy.graphics.instructions")
    context_module.Color = _FakeInstruction
    vertex_module = types.ModuleType("kivy.graphics.vertex_instructions")
    vertex_module.Line = _FakeInstruction
    vertex_module.Quad = _FakeInstruction
    vertex_module.Triangle = _FakeInstruction
    instructions_module.InstructionGroup = _FakeInstructionGroup
    graphics_module.Color = _FakeInstruction
    graphics_module.InstructionGroup = _FakeInstructionGroup
    graphics_module.Line = _FakeInstruction
    graphics_module.Rectangle = _FakeInstruction
    graphics_module.context_instructions = context_module
    graphics_module.instructions = instructions_module
    graphics_module.vertex_instructions = vertex_module
    texture_module = types.ModuleType("kivy.graphics.texture")
    texture_module.Texture = _simple_type("Texture")

    metrics_module = types.ModuleType("kivy.metrics")
    metrics_module.dp = lambda value: value
    metrics_module.sp = lambda value: value
    resources_module = types.ModuleType("kivy.resources")
    resources_module.resource_add_path = lambda *_args, **_kwargs: None
    resources_module.resource_find = lambda path: path
    event_module = types.ModuleType("kivy.event")
    event_module.EventDispatcher = _simple_type("EventDispatcher")

    kivymd_module = types.ModuleType("kivymd")
    kivymd_app_module = types.ModuleType("kivymd.app")
    kivymd_app_module.MDApp = type("MDApp", (), {"get_running_app": staticmethod(lambda: None)})
    kivymd_icon_module = types.ModuleType("kivymd.icon_definitions")
    kivymd_icon_module.md_icons = {}
    kivymd_uix_module = types.ModuleType("kivymd.uix")
    kivymd_screen_module = types.ModuleType("kivymd.uix.screen")
    kivymd_screen_module.MDScreen = _simple_type("MDScreen")
    kivymd_list_module = types.ModuleType("kivymd.uix.list")
    kivymd_list_module.MDListItem = _simple_type("MDListItem")
    kivymd_label_module = types.ModuleType("kivymd.uix.label")
    kivymd_label_module.MDLabel = _simple_type("MDLabel")
    kivymd_label_module.MDIcon = _simple_type("MDIcon")
    kivymd_button_module = types.ModuleType("kivymd.uix.button")
    kivymd_button_module.MDIconButton = _simple_type("MDIconButton")
    kivymd_button_module.MDButton = _simple_type("MDButton")
    kivymd_button_module.MDButtonText = _simple_type("MDButtonText")
    kivymd_dialog_module = types.ModuleType("kivymd.uix.dialog")
    kivymd_dialog_module.MDDialog = _simple_type("MDDialog")
    kivymd_dialog_module.MDDialogContentContainer = _simple_type("MDDialogContentContainer")
    kivymd_dialog_module.MDDialogHeadlineText = _simple_type("MDDialogHeadlineText")
    kivymd_boxlayout_module = types.ModuleType("kivymd.uix.boxlayout")
    kivymd_boxlayout_module.MDBoxLayout = _simple_type("MDBoxLayout")
    kivymd_screenmanager_module = types.ModuleType("kivymd.uix.screenmanager")
    kivymd_screenmanager_module.MDScreenManager = _simple_type("MDScreenManager")

    sys.modules["kivy"] = kivy_module
    sys.modules["kivy.app"] = app_module
    sys.modules["kivy.clock"] = clock_module
    sys.modules["kivy.logger"] = logger_module
    sys.modules["kivy.lang"] = lang_module
    sys.modules["kivy.properties"] = properties_module
    sys.modules["kivy.utils"] = utils_module
    sys.modules["kivy.core"] = core_module
    sys.modules["kivy.core.window"] = window_module
    sys.modules["kivy.uix"] = uix_module
    sys.modules["kivy.uix.widget"] = widget_module
    sys.modules["kivy.uix.boxlayout"] = boxlayout_module
    sys.modules["kivy.uix.button"] = button_module
    sys.modules["kivy.uix.label"] = label_module
    sys.modules["kivy.uix.popup"] = popup_module
    sys.modules["kivy.uix.scrollview"] = scrollview_module
    sys.modules["kivy.uix.anchorlayout"] = anchorlayout_module
    sys.modules["kivy.uix.gridlayout"] = gridlayout_module
    sys.modules["kivy.uix.modalview"] = modalview_module
    sys.modules["kivy.uix.screenmanager"] = screenmanager_module
    sys.modules["kivy.uix.textinput"] = textinput_module
    sys.modules["kivy.graphics"] = graphics_module
    sys.modules["kivy.graphics.context_instructions"] = context_module
    sys.modules["kivy.graphics.instructions"] = instructions_module
    sys.modules["kivy.graphics.texture"] = texture_module
    sys.modules["kivy.graphics.vertex_instructions"] = vertex_module
    sys.modules["kivy.metrics"] = metrics_module
    sys.modules["kivy.resources"] = resources_module
    sys.modules["kivy.event"] = event_module
    sys.modules["kivymd"] = kivymd_module
    sys.modules["kivymd.app"] = kivymd_app_module
    sys.modules["kivymd.icon_definitions"] = kivymd_icon_module
    sys.modules["kivymd.uix"] = kivymd_uix_module
    sys.modules["kivymd.uix.screen"] = kivymd_screen_module
    sys.modules["kivymd.uix.list"] = kivymd_list_module
    sys.modules["kivymd.uix.label"] = kivymd_label_module
    sys.modules["kivymd.uix.button"] = kivymd_button_module
    sys.modules["kivymd.uix.dialog"] = kivymd_dialog_module
    sys.modules["kivymd.uix.boxlayout"] = kivymd_boxlayout_module
    sys.modules["kivymd.uix.screenmanager"] = kivymd_screenmanager_module


_install_kivy_stubs()
