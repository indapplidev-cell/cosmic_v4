"""EN: View for the profile screen.
RU: Р В РЎСџР РЋР вЂљР В Р’ВµР В РўвЂР РЋР С“Р РЋРІР‚С™Р В Р’В°Р В Р вЂ Р В Р’В»Р В Р’ВµР В Р вЂ¦Р В РЎвЂР В Р’Вµ Р РЋР РЉР В РЎвЂќР РЋР вЂљР В Р’В°Р В Р вЂ¦Р В Р’В° Р В РЎвЂ”Р РЋР вЂљР В РЎвЂўР РЋРІР‚С›Р В РЎвЂР В Р’В»Р РЋР РЏ.
"""

from pathlib import Path
from threading import Thread
from client.infrastructure.storage.gameplay.record_store import RecordStore
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.factory import Factory
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
from client.application.auth import auth_backend
from client.application.lang.lang_manager import t
from client.infrastructure.branding.remote_profile_icon_loader import resolve_profile_icon_source
from client.presentation.debug.debug_borders import apply_debug_borders_to_ids
from client.presentation.common.button_text_style import apply_button_text_style, caps
from client.presentation.layouts.layout_constants import (
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
    RU: Р В РЎСџР РЋР вЂљР В Р’ВµР В РўвЂР РЋР С“Р РЋРІР‚С™Р В Р’В°Р В Р вЂ Р В Р’В»Р В Р’ВµР В Р вЂ¦Р В РЎвЂР В Р’Вµ Р В РЎвЂ”Р РЋР вЂљР В РЎвЂўР РЋРІР‚С›Р В РЎвЂР В Р’В»Р РЋР РЏ, Р РЋР С“Р В Р вЂ Р РЋР РЏР В Р’В·Р РЋРІР‚в„–Р В Р вЂ Р В Р’В°Р РЋР вЂ№Р РЋРІР‚В°Р В Р’ВµР В Р’Вµ Р РЋР вЂљР В Р’В°Р РЋР С“Р В РЎвЂќР В Р’В»Р В Р’В°Р В РўвЂР В РЎвЂќР РЋРЎвЂњ, VM Р В РЎвЂ Р В РЎвЂќР В РЎвЂўР В Р вЂ¦Р РЋРІР‚С™Р РЋР вЂљР В РЎвЂўР В Р’В»Р В Р’В»Р В Р’ВµР РЋР вЂљ.
    """

    best_score_text = StringProperty("0")
    rating_text = StringProperty("0")
    balance_text = StringProperty("0")
    login_text = StringProperty(t("common.no_data"))
    phone_text = StringProperty(t("common.no_data"))
    tg_text = StringProperty(t("common.no_data"))

    def __init__(self, **kwargs):
        """EN: Initialize view state used by the rating dialog.
        RU: Р В Р’ВР В Р вЂ¦Р В РЎвЂР РЋРІР‚В Р В РЎвЂР В Р’В°Р В Р’В»Р В РЎвЂР В Р’В·Р В РЎвЂР РЋР вЂљР В РЎвЂўР В Р вЂ Р В Р’В°Р РЋРІР‚С™Р РЋР Р‰ Р РЋР С“Р В РЎвЂўР РЋР С“Р РЋРІР‚С™Р В РЎвЂўР РЋР РЏР В Р вЂ¦Р В РЎвЂР В Р’Вµ Р В РЎвЂ”Р РЋР вЂљР В Р’ВµР В РўвЂР РЋР С“Р РЋРІР‚С™Р В Р’В°Р В Р вЂ Р В Р’В»Р В Р’ВµР В Р вЂ¦Р В РЎвЂР РЋР РЏ Р В РўвЂР В Р’В»Р РЋР РЏ Р В РўвЂР В РЎвЂР В Р’В°Р В Р’В»Р В РЎвЂўР В РЎвЂ“Р В Р’В° Р РЋР вЂљР В Р’ВµР В РІвЂћвЂ“Р РЋРІР‚С™Р В РЎвЂР В Р вЂ¦Р В РЎвЂ“Р В Р’В°.
        """
        super().__init__(**kwargs)
        self._rating_dialog: MDDialog | None = None
        self._rating_rows_grid: GridLayout | None = None
        self._rating_row_height = dp(34)

    def on_pre_enter(self, *args):
        """EN: Refresh profile data before showing the screen.
        RU: Р В РЎвЂєР В Р’В±Р В Р вЂ¦Р В РЎвЂўР В Р вЂ Р В РЎвЂР РЋРІР‚С™Р РЋР Р‰ Р В РўвЂР В Р’В°Р В Р вЂ¦Р В Р вЂ¦Р РЋРІР‚в„–Р В Р’Вµ Р В РЎвЂ”Р РЋР вЂљР В РЎвЂўР РЋРІР‚С›Р В РЎвЂР В Р’В»Р РЋР РЏ Р В РЎвЂ”Р В Р’ВµР РЋР вЂљР В Р’ВµР В РўвЂ Р В РЎвЂ”Р В РЎвЂўР В РЎвЂќР В Р’В°Р В Р’В·Р В РЎвЂўР В РЎВ Р РЋР РЉР В РЎвЂќР РЋР вЂљР В Р’В°Р В Р вЂ¦Р В Р’В°.
        """
        if hasattr(self, "vm"):
            self.ids.profile_top_left_title.text = self.vm.title
        self.controller.refresh_profile_cards(self)
        return super().on_pre_enter(*args)

    def on_kv_post(self, base_widget) -> None:
        """EN: Apply layout after KV is ready.
        RU: Р В РЎСџР РЋР вЂљР В РЎвЂР В РЎВР В Р’ВµР В Р вЂ¦Р В РЎвЂР РЋРІР‚С™Р РЋР Р‰ Р РЋР вЂљР В Р’В°Р РЋР С“Р В РЎвЂќР В Р’В»Р В Р’В°Р В РўвЂР В РЎвЂќР РЋРЎвЂњ Р В РЎвЂ”Р В РЎвЂўР РЋР С“Р В Р’В»Р В Р’Вµ Р В Р’В·Р В Р’В°Р В РЎвЂ“Р РЋР вЂљР РЋРЎвЂњР В Р’В·Р В РЎвЂќР В РЎвЂ KV.
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
        self._shell_profile_title_widget = self._strong_widget(Factory.ProfileShellTitleWidget())
        self._shell_profile_title_text_widget = self._strong_widget(
            self._shell_profile_title_widget.ids.profile_shell_title_text
        )
        self._shell_profile_title_icon_widget = self._strong_widget(
            self._shell_profile_title_widget.ids.profile_shell_title_icon
        )
        self._shell_profile_title_icon_source = ""
        self._shell_profile_title_icon_attempted = False

    def configure(self, vm: ProfileScreenVM, controller: ProfileScreenController) -> None:
        """EN: Configure texts and bind callbacks.
        RU: Р В РЎСљР В Р’В°Р РЋР С“Р РЋРІР‚С™Р РЋР вЂљР В РЎвЂўР В РЎвЂР РЋРІР‚С™Р РЋР Р‰ Р РЋРІР‚С™Р В Р’ВµР В РЎвЂќР РЋР С“Р РЋРІР‚С™Р РЋРІР‚в„– Р В РЎвЂ Р В РЎвЂ”Р РЋР вЂљР В РЎвЂР В Р вЂ Р РЋР РЏР В Р’В·Р В Р’В°Р РЋРІР‚С™Р РЋР Р‰ Р В РЎвЂќР В РЎвЂўР В Р’В»Р В Р’В±Р РЋР РЉР В РЎвЂќР В РЎвЂ.
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
        self.best_score_text = str(RecordStore().get_best_score())

    def open_rating_dialog(self) -> None:
        """EN: Open rating dialog and asynchronously load top-100 rows.
        RU: Р В РЎвЂєР РЋРІР‚С™Р В РЎвЂќР РЋР вЂљР РЋРІР‚в„–Р РЋРІР‚С™Р РЋР Р‰ Р В РўвЂР В РЎвЂР В Р’В°Р В Р’В»Р В РЎвЂўР В РЎвЂ“ Р РЋР вЂљР В Р’ВµР В РІвЂћвЂ“Р РЋРІР‚С™Р В РЎвЂР В Р вЂ¦Р В РЎвЂ“Р В Р’В° Р В РЎвЂ Р В Р’В°Р РЋР С“Р В РЎвЂР В Р вЂ¦Р РЋРІР‚В¦Р РЋР вЂљР В РЎвЂўР В Р вЂ¦Р В Р вЂ¦Р В РЎвЂў Р В Р’В·Р В Р’В°Р В РЎвЂ“Р РЋР вЂљР РЋРЎвЂњР В Р’В·Р В РЎвЂР РЋРІР‚С™Р РЋР Р‰ Р РЋРІР‚С™Р В РЎвЂўР В РЎвЂ”-100 Р РЋР С“Р РЋРІР‚С™Р РЋР вЂљР В РЎвЂўР В РЎвЂќ.
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
        RU: Р В Р Р‹Р В РЎвЂўР В Р’В·Р В РўвЂР В Р’В°Р РЋРІР‚С™Р РЋР Р‰ Р РЋР вЂљР В Р’В°Р РЋР С“Р В РЎвЂќР В Р’В»Р В Р’В°Р В РўвЂР В РЎвЂќР РЋРЎвЂњ Р РЋР С“ Р РЋРІР‚С›Р В РЎвЂР В РЎвЂќР РЋР С“Р В РЎвЂР РЋР вЂљР В РЎвЂўР В Р вЂ Р В Р’В°Р В Р вЂ¦Р В Р вЂ¦Р В РЎвЂўР В РІвЂћвЂ“ Р РЋРІвЂљВ¬Р В Р’В°Р В РЎвЂ”Р В РЎвЂќР В РЎвЂўР В РІвЂћвЂ“ Р В РЎвЂ Р РЋР С“Р В РЎвЂќР РЋР вЂљР В РЎвЂўР В Р’В»Р В Р’В»Р В РЎвЂР РЋР вЂљР РЋРЎвЂњР В Р’ВµР В РЎВР РЋРІР‚в„–Р В РЎВР В РЎвЂ Р РЋР С“Р РЋРІР‚С™Р РЋР вЂљР В РЎвЂўР В РЎвЂќР В Р’В°Р В РЎВР В РЎвЂ Р РЋР вЂљР В Р’ВµР В РІвЂћвЂ“Р РЋРІР‚С™Р В РЎвЂР В Р вЂ¦Р В РЎвЂ“Р В Р’В°.
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
        RU: Р В Р Р‹Р В РЎвЂўР В Р’В·Р В РўвЂР В Р’В°Р РЋРІР‚С™Р РЋР Р‰ label-Р РЋР РЏР РЋРІР‚РЋР В Р’ВµР В РІвЂћвЂ“Р В РЎвЂќР РЋРЎвЂњ Р РЋРІР‚С™Р В Р’В°Р В Р’В±Р В Р’В»Р В РЎвЂР РЋРІР‚В Р РЋРІР‚в„– Р РЋР С“ Р В Р’ВµР В РўвЂР В РЎвЂР В Р вЂ¦Р РЋРІР‚в„–Р В РЎВР В РЎвЂ Р В РЎвЂ”Р РЋР вЂљР В Р’В°Р В Р вЂ Р В РЎвЂР В Р’В»Р В Р’В°Р В РЎВР В РЎвЂ Р РЋР вЂљР В Р’В°Р В Р’В·Р В РЎВР В Р’ВµР РЋР вЂљР В Р’В°/Р В Р вЂ Р РЋРІР‚в„–Р РЋР вЂљР В Р’В°Р В Р вЂ Р В Р вЂ¦Р В РЎвЂР В Р вЂ Р В Р’В°Р В Р вЂ¦Р В РЎвЂР РЋР РЏ.
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
        RU: Р В Р Р‹Р В РЎвЂўР В Р’В·Р В РўвЂР В Р’В°Р РЋРІР‚С™Р РЋР Р‰ Р В РЎвЂўР В РўвЂР В Р вЂ¦Р РЋРЎвЂњ Р РЋР РЏР РЋРІР‚РЋР В Р’ВµР В РІвЂћвЂ“Р В РЎвЂќР РЋРЎвЂњ Р РЋРІР‚С™Р В Р’В°Р В Р’В±Р В Р’В»Р В РЎвЂР РЋРІР‚В Р РЋРІР‚в„– Р РЋР С“ Р В Р вЂ Р В Р’В»Р В РЎвЂўР В Р’В¶Р В Р’ВµР В Р вЂ¦Р В Р вЂ¦Р РЋРІР‚в„–Р В РЎВ label.
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
        RU: Р В Р’В Р В РЎвЂР РЋР С“Р В РЎвЂўР В Р вЂ Р В Р’В°Р РЋРІР‚С™Р РЋР Р‰ Р В Р вЂ¦Р В Р’ВµР В РЎвЂ”Р РЋР вЂљР В Р’ВµР РЋР вЂљР РЋРІР‚в„–Р В Р вЂ Р В Р вЂ¦Р РЋРІР‚в„–Р В Р’Вµ Р В РЎвЂ“Р РЋР вЂљР В Р’В°Р В Р вЂ¦Р В РЎвЂР РЋРІР‚В Р РЋРІР‚в„– Р РЋР С“Р В Р’ВµР РЋРІР‚С™Р В РЎвЂќР В РЎвЂ Р В РўвЂР В Р’В»Р РЋР РЏ Р РЋРІвЂљВ¬Р В Р’В°Р В РЎвЂ”Р В РЎвЂќР В РЎвЂ/Р РЋРІР‚С™Р В Р’ВµР В Р’В»Р В Р’В° Р РЋРІР‚С™Р В Р’В°Р В Р’В±Р В Р’В»Р В РЎвЂР РЋРІР‚В Р РЋРІР‚в„–.
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
        RU: Р В РІР‚вЂќР В Р’В°Р В РЎвЂ”Р В РЎвЂўР В Р’В»Р В Р вЂ¦Р В РЎвЂР РЋРІР‚С™Р РЋР Р‰ Р В РЎвЂўР В Р’В±Р В Р’В»Р В Р’В°Р РЋР С“Р РЋРІР‚С™Р РЋР Р‰ Р РЋР С“Р РЋРІР‚С™Р РЋР вЂљР В РЎвЂўР В РЎвЂќ Р РЋР вЂљР В Р’ВµР В РІвЂћвЂ“Р РЋРІР‚С™Р В РЎвЂР В Р вЂ¦Р В РЎвЂ“Р В Р’В° Р В РЎвЂ”Р В Р’ВµР РЋР вЂљР В Р’ВµР В РўвЂР В Р’В°Р В Р вЂ¦Р В Р вЂ¦Р РЋРІР‚в„–Р В РЎВР В РЎвЂ Р В РўвЂР В Р’В°Р В Р вЂ¦Р В Р вЂ¦Р РЋРІР‚в„–Р В РЎВР В РЎвЂ.
        """
        if self._rating_rows_grid is None:
            return

        self._rating_rows_grid.clear_widgets()
        for row in rows[:100]:
            user_text = str(row.get("user", "") or "").strip()
            if not user_text:
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
        RU: Р В РІР‚вЂќР В Р’В°Р В РЎвЂ”Р РЋР вЂљР В РЎвЂўР РЋР С“Р В РЎвЂР РЋРІР‚С™Р РЋР Р‰ Р В РўвЂР В Р’В°Р В Р вЂ¦Р В Р вЂ¦Р РЋРІР‚в„–Р В Р’Вµ Р РЋР вЂљР В Р’ВµР В РІвЂћвЂ“Р РЋРІР‚С™Р В РЎвЂР В Р вЂ¦Р В РЎвЂ“Р В Р’В° Р РЋРІР‚РЋР В Р’ВµР РЋР вЂљР В Р’ВµР В Р’В· bridge Р В РЎвЂ Р В РЎвЂўР В Р’В±Р В Р вЂ¦Р В РЎвЂўР В Р вЂ Р В РЎвЂР РЋРІР‚С™Р РЋР Р‰ Р РЋР С“Р РЋРІР‚С™Р РЋР вЂљР В РЎвЂўР В РЎвЂќР В РЎвЂ UI.
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
        RU: Р В РІР‚вЂќР В Р’В°Р В РЎвЂќР РЋР вЂљР РЋРІР‚в„–Р РЋРІР‚С™Р РЋР Р‰ Р В РЎвЂ Р В РЎвЂўР РЋРІР‚РЋР В РЎвЂР РЋР С“Р РЋРІР‚С™Р В РЎвЂР РЋРІР‚С™Р РЋР Р‰ Р РЋР вЂљР В Р’ВµР РЋР С“Р РЋРЎвЂњР РЋР вЂљР РЋР С“Р РЋРІР‚в„– Р В РўвЂР В РЎвЂР В Р’В°Р В Р’В»Р В РЎвЂўР В РЎвЂ“Р В Р’В° Р РЋР вЂљР В Р’ВµР В РІвЂћвЂ“Р РЋРІР‚С™Р В РЎвЂР В Р вЂ¦Р В РЎвЂ“Р В Р’В°.
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
        RU: Р вЂ™Р ВµРЎР‚Р Р…РЎС“РЎвЂљРЎРЉ Р С—Р ВµРЎР‚Р ВµР С‘РЎРѓР С—Р С•Р В»РЎРЉР В·РЎС“Р ВµР СРЎвЂ№Р в„– content bar-Р Р†Р С‘Р Т‘Р В¶Р ВµРЎвЂљ Р Т‘Р В»РЎРЏ Р С•Р В±РЎвЂ°Р ВµР С–Р С• host-Р С”Р С•Р Р…РЎвЂљР ВµР в„–Р Р…Р ВµРЎР‚Р В° shell.
        """

        return self._contentbar_widget

    def get_shell_bottom_widget(self):
        """EN: Return the reusable bottom bar widget for the shared shell host.
        RU: Р вЂ™Р ВµРЎР‚Р Р…РЎС“РЎвЂљРЎРЉ Р С—Р ВµРЎР‚Р ВµР С‘РЎРѓР С—Р С•Р В»РЎРЉР В·РЎС“Р ВµР СРЎвЂ№Р в„– bottom bar-Р Р†Р С‘Р Т‘Р В¶Р ВµРЎвЂљ Р Т‘Р В»РЎРЏ Р С•Р В±РЎвЂ°Р ВµР С–Р С• host-Р С”Р С•Р Р…РЎвЂљР ВµР в„–Р Р…Р ВµРЎР‚Р В° shell.
        """

        return self._bottombar_widget

    def on_shell_present(self, shell) -> None:
        """Mount profile-specific shell title widget into the shared top-left slot."""

        self._shell_profile_title_text_widget.text = shell.ids.top_left_title.text
        self._set_profile_title_icon_source(self._shell_profile_title_icon_source)
        shell.set_top_left_widget(self._shell_profile_title_widget)
        self._start_profile_title_icon_resolve()

    def _start_profile_title_icon_resolve(self) -> None:
        """Resolve the profile-screen shell icon in the background and update UI on the main thread."""

        if self._shell_profile_title_icon_source:
            self._set_profile_title_icon_source(self._shell_profile_title_icon_source)
            return
        if self._shell_profile_title_icon_attempted:
            return
        self._shell_profile_title_icon_attempted = True

        def _worker() -> None:
            source = resolve_profile_icon_source()
            Clock.schedule_once(lambda _dt: self._apply_resolved_profile_title_icon(source), 0)

        Thread(target=_worker, daemon=True).start()

    def _apply_resolved_profile_title_icon(self, source: str) -> None:
        """Apply resolved profile icon source, leaving the fallback title text when unavailable."""

        source = str(source or "").strip()
        if not source:
            return
        self._shell_profile_title_icon_source = source
        self._set_profile_title_icon_source(source)

    def _set_profile_title_icon_source(self, source: str) -> None:
        """Toggle between fallback shell title text and the cached local profile icon source."""

        source = str(source or "").strip()
        if source:
            self._shell_profile_title_icon_widget.source = source
            self._shell_profile_title_icon_widget.opacity = 1
            self._shell_profile_title_icon_widget.reload()
            self._shell_profile_title_text_widget.opacity = 0
            return
        self._shell_profile_title_icon_widget.opacity = 0
        self._shell_profile_title_icon_widget.source = ""
        self._shell_profile_title_text_widget.opacity = 1

    @staticmethod
    def _strong_widget(widget):
        """Return the real widget behind a Kivy ids weak proxy."""

        return getattr(widget, "__self__", widget)



