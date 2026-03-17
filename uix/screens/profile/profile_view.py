"""EN: View for the profile screen.
RU: Р СџРЎР‚Р ВµР Т‘РЎРѓРЎвЂљР В°Р Р†Р В»Р ВµР Р…Р С‘Р Вµ РЎРЊР С”РЎР‚Р В°Р Р…Р В° Р С—РЎР‚Р С•РЎвЂћР С‘Р В»РЎРЏ.
"""

from pathlib import Path
from threading import Thread
from data.gameplay.record_storage import RecordStorage
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Line
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog import MDDialog, MDDialogContentContainer, MDDialogHeadlineText
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen
from manager import auth_backend
from manager.lang.lang_manager import t
from uix.debug.debug_borders import apply_debug_borders_to_ids
from uix.screens.common.button_text_style import apply_button_text_style, caps
from uix.screens.layouts.layout_constants import (
    RATING_DIALOG_HEIGHT_RATIO,
    RATING_DIALOG_WIDTH_RATIO,
    RATING_GRID_LINE_WIDTH,
    RATING_OK_BUTTON_HEIGHT_RATIO,
    RATING_OK_BUTTON_WIDTH_RATIO,
    RATING_OK_ROW_HEIGHT_RATIO,
    RATING_TABLE_HEADER_HEIGHT_RATIO,
    RATING_TABLE_ROW_HEIGHT_RATIO,
)

from .profile_controller import ProfileScreenController
from .profile_layout import PROFILE_DEBUG_IDS, apply_profile_layout
from .profile_vm import ProfileScreenVM

KV_PATH = Path(__file__).with_name("profile.kv")
Builder.load_file(str(KV_PATH))


class ProfileScreenView(MDScreen):
    """EN: Profile screen view that wires layout, VM, and controller.
    RU: Р СџРЎР‚Р ВµР Т‘РЎРѓРЎвЂљР В°Р Р†Р В»Р ВµР Р…Р С‘Р Вµ Р С—РЎР‚Р С•РЎвЂћР С‘Р В»РЎРЏ, РЎРѓР Р†РЎРЏР В·РЎвЂ№Р Р†Р В°РЎР‹РЎвЂ°Р ВµР Вµ РЎР‚Р В°РЎРѓР С”Р В»Р В°Р Т‘Р С”РЎС“, VM Р С‘ Р С”Р С•Р Р…РЎвЂљРЎР‚Р С•Р В»Р В»Р ВµРЎР‚.
    """

    best_score_text = StringProperty("0")
    rating_text = StringProperty("0")
    balance_text = StringProperty("0")
    login_text = StringProperty(t("common.no_data"))
    phone_text = StringProperty(t("common.no_data"))
    tg_text = StringProperty(t("common.no_data"))

    def __init__(self, **kwargs):
        """EN: Initialize view state used by the rating dialog.
        RU: Р ВР Р…Р С‘РЎвЂ Р С‘Р В°Р В»Р С‘Р В·Р С‘РЎР‚Р С•Р Р†Р В°РЎвЂљРЎРЉ РЎРѓР С•РЎРѓРЎвЂљР С•РЎРЏР Р…Р С‘Р Вµ Р С—РЎР‚Р ВµР Т‘РЎРѓРЎвЂљР В°Р Р†Р В»Р ВµР Р…Р С‘РЎРЏ Р Т‘Р В»РЎРЏ Р Т‘Р С‘Р В°Р В»Р С•Р С–Р В° РЎР‚Р ВµР в„–РЎвЂљР С‘Р Р…Р С–Р В°.
        """
        super().__init__(**kwargs)
        self._rating_dialog: MDDialog | None = None
        self._rating_rows_grid: GridLayout | None = None
        self._rating_row_height = dp(34)

    def on_pre_enter(self, *args):
        """EN: Refresh profile data before showing the screen.
        RU: Р С›Р В±Р Р…Р С•Р Р†Р С‘РЎвЂљРЎРЉ Р Т‘Р В°Р Р…Р Р…РЎвЂ№Р Вµ Р С—РЎР‚Р С•РЎвЂћР С‘Р В»РЎРЏ Р С—Р ВµРЎР‚Р ВµР Т‘ Р С—Р С•Р С”Р В°Р В·Р С•Р С РЎРЊР С”РЎР‚Р В°Р Р…Р В°.
        """
        if hasattr(self, "vm"):
            self.ids.profile_top_left_title.text = self.vm.title
        self.controller.refresh_profile_cards(self)
        return super().on_pre_enter(*args)

    def on_kv_post(self, base_widget) -> None:
        """EN: Apply layout after KV is ready.
        RU: Р СџРЎР‚Р С‘Р СР ВµР Р…Р С‘РЎвЂљРЎРЉ РЎР‚Р В°РЎРѓР С”Р В»Р В°Р Т‘Р С”РЎС“ Р С—Р С•РЎРѓР В»Р Вµ Р В·Р В°Р С–РЎР‚РЎС“Р В·Р С”Р С‘ KV.
        """
        apply_profile_layout(self)
        apply_button_text_style(
            self,
            [
                self.ids.back_label,
                self.ids.payout_label,
                self.ids.login_label,
            ],
        )
        apply_debug_borders_to_ids(self, PROFILE_DEBUG_IDS)
        self._ids_keepalive = dict(self.ids)
        for _key, _widget in self._ids_keepalive.items():
            self.ids[_key] = _widget
        self._contentbar_widget = getattr(self.ids.contentbar, "__self__", self.ids.contentbar)
        self._bottombar_widget = getattr(self.ids.bottombar, "__self__", self.ids.bottombar)

    def configure(self, vm: ProfileScreenVM, controller: ProfileScreenController) -> None:
        """EN: Configure texts and bind callbacks.
        RU: Р СњР В°РЎРѓРЎвЂљРЎР‚Р С•Р С‘РЎвЂљРЎРЉ РЎвЂљР ВµР С”РЎРѓРЎвЂљРЎвЂ№ Р С‘ Р С—РЎР‚Р С‘Р Р†РЎРЏР В·Р В°РЎвЂљРЎРЉ Р С”Р С•Р В»Р В±РЎРЊР С”Р С‘.
        """
        self.vm = vm
        self.controller = controller
        self.ids.back_label.text = caps(vm.back_text)
        self.ids.payout_label.text = caps(vm.payout_text)
        self.ids.login_label.text = caps(vm.login_text)

        self._back_callback = lambda *_: controller.back()
        self._open_rating_dialog_callback = lambda *_: self.open_rating_dialog()
        self._login_callback = lambda *_: controller.login()
        self.ids.back_btn.unbind(on_release=self._back_callback)
        self.ids.back_btn.bind(on_release=self._back_callback)
        self.ids.payout_btn.unbind(on_release=self._open_rating_dialog_callback)
        self.ids.payout_btn.bind(on_release=self._open_rating_dialog_callback)
        self.ids.login_btn.unbind(on_release=self._login_callback)
        self.ids.login_btn.bind(on_release=self._login_callback)
        self.best_score_text = str(RecordStorage().get_best_score())

    def open_rating_dialog(self) -> None:
        """EN: Open rating dialog and asynchronously load top-100 rows.
        RU: Р С›РЎвЂљР С”РЎР‚РЎвЂ№РЎвЂљРЎРЉ Р Т‘Р С‘Р В°Р В»Р С•Р С– РЎР‚Р ВµР в„–РЎвЂљР С‘Р Р…Р С–Р В° Р С‘ Р В°РЎРѓР С‘Р Р…РЎвЂ¦РЎР‚Р С•Р Р…Р Р…Р С• Р В·Р В°Р С–РЎР‚РЎС“Р В·Р С‘РЎвЂљРЎРЉ РЎвЂљР С•Р С—-100 РЎРѓРЎвЂљРЎР‚Р С•Р С”.
        """
        self._close_rating_dialog()
        content, rows_grid = self._build_rating_content()
        self._rating_rows_grid = rows_grid
        self._set_rating_rows(
            [{"user": t("profile.rating_dialog.loading"), "record": "", "rating": ""}]
        )

        self._rating_dialog = MDDialog(
            MDDialogHeadlineText(text=t("profile.rating_dialog.title"), halign="left"),
            MDDialogContentContainer(content),
            auto_dismiss=False,
        )
        self._rating_dialog.size_hint_x = RATING_DIALOG_WIDTH_RATIO
        self._rating_dialog.open()
        Clock.schedule_once(lambda *_: self._load_rating_rows(), 0)

    def _build_rating_content(self) -> tuple[MDBoxLayout, GridLayout]:
        """EN: Build fixed header + scrollable rows layout for rating table.
        RU: Р РЋР С•Р В·Р Т‘Р В°РЎвЂљРЎРЉ РЎР‚Р В°РЎРѓР С”Р В»Р В°Р Т‘Р С”РЎС“ РЎРѓ РЎвЂћР С‘Р С”РЎРѓР С‘РЎР‚Р С•Р Р†Р В°Р Р…Р Р…Р С•Р в„– РЎв‚¬Р В°Р С—Р С”Р С•Р в„– Р С‘ РЎРѓР С”РЎР‚Р С•Р В»Р В»Р С‘РЎР‚РЎС“Р ВµР СРЎвЂ№Р СР С‘ РЎРѓРЎвЂљРЎР‚Р С•Р С”Р В°Р СР С‘ РЎР‚Р ВµР в„–РЎвЂљР С‘Р Р…Р С–Р В°.
        """
        dialog_height = max(dp(300), Window.height * RATING_DIALOG_HEIGHT_RATIO)
        self._rating_row_height = max(dp(28), dialog_height * RATING_TABLE_ROW_HEIGHT_RATIO)
        header_height = max(dp(32), dialog_height * RATING_TABLE_HEADER_HEIGHT_RATIO)
        ok_row_height = max(dp(44), dialog_height * RATING_OK_ROW_HEIGHT_RATIO)
        ok_btn_height = max(dp(36), ok_row_height * RATING_OK_BUTTON_HEIGHT_RATIO)

        content = MDBoxLayout(
            orientation="vertical",
            spacing=0,
            size_hint_y=None,
            height=dialog_height,
        )

        table_box = MDBoxLayout(orientation="vertical", spacing=0, size_hint=(1, 1))
        content.add_widget(table_box)

        header = GridLayout(cols=3, size_hint_y=None, height=header_height, spacing=0)
        header.add_widget(
            self._make_table_cell(
                t("profile.rating_dialog.col_user"),
                "center",
                bold=True,
                cell_height=header_height,
            )
        )
        header.add_widget(
            self._make_table_cell(
                t("profile.rating_dialog.col_record"),
                "center",
                bold=True,
                cell_height=header_height,
            )
        )
        header.add_widget(
            self._make_table_cell(
                t("profile.rating_dialog.col_rating"),
                "center",
                bold=True,
                cell_height=header_height,
            )
        )
        table_box.add_widget(header)
        self._bind_grid_borders(header, include_row_dividers=False)

        rows_grid = GridLayout(cols=3, spacing=0, size_hint_y=None, padding=(0, 0, 0, 0))
        rows_grid.bind(minimum_height=rows_grid.setter("height"))

        scroll = ScrollView(
            do_scroll_x=False,
            do_scroll_y=True,
            bar_width=dp(4),
            size_hint=(1, 1),
        )
        scroll.add_widget(rows_grid)
        table_box.add_widget(scroll)
        self._bind_grid_borders(rows_grid, include_row_dividers=True)

        ok_row = AnchorLayout(anchor_x="center", anchor_y="center", size_hint_y=None, height=ok_row_height)
        ok_button = Button(
            text=t("common.ok"),
            size_hint=(RATING_OK_BUTTON_WIDTH_RATIO, None),
            height=ok_btn_height,
        )
        ok_button.bind(on_release=lambda *_: self._close_rating_dialog())
        ok_row.add_widget(ok_button)
        content.add_widget(ok_row)

        return content, rows_grid

    def _make_table_label(self, text_value: str, halign: str, *, bold: bool = False) -> MDLabel:
        """EN: Create table cell label with consistent sizing/alignment rules.
        RU: Р РЋР С•Р В·Р Т‘Р В°РЎвЂљРЎРЉ label-РЎРЏРЎвЂЎР ВµР в„–Р С”РЎС“ РЎвЂљР В°Р В±Р В»Р С‘РЎвЂ РЎвЂ№ РЎРѓ Р ВµР Т‘Р С‘Р Р…РЎвЂ№Р СР С‘ Р С—РЎР‚Р В°Р Р†Р С‘Р В»Р В°Р СР С‘ РЎР‚Р В°Р В·Р СР ВµРЎР‚Р В°/Р Р†РЎвЂ№РЎР‚Р В°Р Р†Р Р…Р С‘Р Р†Р В°Р Р…Р С‘РЎРЏ.
        """
        label = MDLabel(
            text=f"[b]{text_value}[/b]" if bold else text_value,
            markup=bold,
            halign=halign,
            valign="middle",
            shorten=not bold,
            shorten_from="right",
            size_hint_y=None,
            height=dp(32),
        )
        label.bind(size=lambda inst, value: setattr(inst, "text_size", value))
        return label

    def _make_table_cell(
        self,
        text_value: str,
        halign: str,
        *,
        bold: bool = False,
        cell_height: float | None = None,
    ) -> MDBoxLayout:
        """EN: Create one table cell wrapper with label.
        RU: Р РЋР С•Р В·Р Т‘Р В°РЎвЂљРЎРЉ Р С•Р Т‘Р Р…РЎС“ РЎРЏРЎвЂЎР ВµР в„–Р С”РЎС“ РЎвЂљР В°Р В±Р В»Р С‘РЎвЂ РЎвЂ№ РЎРѓ Р Р†Р В»Р С•Р В¶Р ВµР Р…Р Р…РЎвЂ№Р С label.
        """
        cell = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=self._rating_row_height if cell_height is None else cell_height,
            padding=(dp(8), 0, dp(8), 0),
        )
        label = self._make_table_label(text_value, halign, bold=bold)
        cell.add_widget(label)
        return cell

    def _bind_grid_borders(self, grid: GridLayout, *, include_row_dividers: bool) -> None:
        """EN: Draw continuous grid borders for table header/body.
        RU: Р В Р С‘РЎРѓР С•Р Р†Р В°РЎвЂљРЎРЉ Р Р…Р ВµР С—РЎР‚Р ВµРЎР‚РЎвЂ№Р Р†Р Р…РЎвЂ№Р Вµ Р С–РЎР‚Р В°Р Р…Р С‘РЎвЂ РЎвЂ№ РЎРѓР ВµРЎвЂљР С”Р С‘ Р Т‘Р В»РЎРЏ РЎв‚¬Р В°Р С—Р С”Р С‘/РЎвЂљР ВµР В»Р В° РЎвЂљР В°Р В±Р В»Р С‘РЎвЂ РЎвЂ№.
        """

        def _redraw(*_):
            grid.canvas.after.clear()
            with grid.canvas.after:
                Color(0.0, 0.8, 1.0, 0.75)
                Line(rectangle=(grid.x, grid.y, grid.width, grid.height), width=RATING_GRID_LINE_WIDTH)
                col_w = grid.width / 3.0 if grid.width else 0.0
                for i in (1, 2):
                    x = grid.x + col_w * i
                    Line(
                        points=[x, grid.y, x, grid.y + grid.height],
                        width=RATING_GRID_LINE_WIDTH,
                    )

                if include_row_dividers:
                    rows_count = len(grid.children) // 3
                    row_h = self._rating_row_height
                    for row_idx in range(1, rows_count):
                        y = grid.y + row_h * row_idx
                        Line(
                            points=[grid.x, y, grid.x + grid.width, y],
                            width=RATING_GRID_LINE_WIDTH,
                        )

        grid.bind(pos=_redraw, size=_redraw, children=_redraw)
        _redraw()

    def _set_rating_rows(self, rows: list[dict]) -> None:
        """EN: Fill rating rows area with provided data.
        RU: Р вЂ”Р В°Р С—Р С•Р В»Р Р…Р С‘РЎвЂљРЎРЉ Р С•Р В±Р В»Р В°РЎРѓРЎвЂљРЎРЉ РЎРѓРЎвЂљРЎР‚Р С•Р С” РЎР‚Р ВµР в„–РЎвЂљР С‘Р Р…Р С–Р В° Р С—Р ВµРЎР‚Р ВµР Т‘Р В°Р Р…Р Р…РЎвЂ№Р СР С‘ Р Т‘Р В°Р Р…Р Р…РЎвЂ№Р СР С‘.
        """
        if self._rating_rows_grid is None:
            return

        self._rating_rows_grid.clear_widgets()
        for row in rows[:100]:
            user_text = str(row.get("user", "") or "").strip()
            if not user_text or user_text == "no data":
                user_text = t("common.no_data")
            self._rating_rows_grid.add_widget(
                self._make_table_cell(user_text, "left")
            )
            self._rating_rows_grid.add_widget(
                self._make_table_cell(str(int(row.get("record", 0) or 0)), "right")
            )
            self._rating_rows_grid.add_widget(
                self._make_table_cell(str(int(row.get("rating", 0) or 0)), "right")
            )

    def _load_rating_rows(self) -> None:
        """EN: Request rating data from bridge and update UI rows.
        RU: Р вЂ”Р В°Р С—РЎР‚Р С•РЎРѓР С‘РЎвЂљРЎРЉ Р Т‘Р В°Р Р…Р Р…РЎвЂ№Р Вµ РЎР‚Р ВµР в„–РЎвЂљР С‘Р Р…Р С–Р В° РЎвЂЎР ВµРЎР‚Р ВµР В· bridge Р С‘ Р С•Р В±Р Р…Р С•Р Р†Р С‘РЎвЂљРЎРЉ РЎРѓРЎвЂљРЎР‚Р С•Р С”Р С‘ UI.
        """
        def _worker() -> None:
            try:
                rows = auth_backend.get_top_ratings(100, timeout=8)
            except Exception:
                rows = []

            def _apply(_dt) -> None:
                if not rows:
                    self._set_rating_rows([{"user": t("common.no_data"), "record": 0, "rating": 0}])
                    return
                self._set_rating_rows(rows)

            Clock.schedule_once(_apply, 0)

        Thread(target=_worker, daemon=True).start()

    def _close_rating_dialog(self) -> None:
        """EN: Close and clear rating dialog resources.
        RU: Р вЂ”Р В°Р С”РЎР‚РЎвЂ№РЎвЂљРЎРЉ Р С‘ Р С•РЎвЂЎР С‘РЎРѓРЎвЂљР С‘РЎвЂљРЎРЉ РЎР‚Р ВµРЎРѓРЎС“РЎР‚РЎРѓРЎвЂ№ Р Т‘Р С‘Р В°Р В»Р С•Р С–Р В° РЎР‚Р ВµР в„–РЎвЂљР С‘Р Р…Р С–Р В°.
        """
        if self._rating_dialog is not None:
            try:
                self._rating_dialog.dismiss()
            except Exception:
                pass
        self._rating_dialog = None
        self._rating_rows_grid = None

    def get_shell_content_widget(self):
        """EN: Return the reusable content bar widget for the shared shell host.
        RU: Р’РµСЂРЅСѓС‚СЊ РїРµСЂРµРёСЃРїРѕР»СЊР·СѓРµРјС‹Р№ content bar-РІРёРґР¶РµС‚ РґР»СЏ РѕР±С‰РµРіРѕ host-РєРѕРЅС‚РµР№РЅРµСЂР° shell.
        """

        return self._contentbar_widget

    def get_shell_bottom_widget(self):
        """EN: Return the reusable bottom bar widget for the shared shell host.
        RU: Р’РµСЂРЅСѓС‚СЊ РїРµСЂРµРёСЃРїРѕР»СЊР·СѓРµРјС‹Р№ bottom bar-РІРёРґР¶РµС‚ РґР»СЏ РѕР±С‰РµРіРѕ host-РєРѕРЅС‚РµР№РЅРµСЂР° shell.
        """

        return self._bottombar_widget


