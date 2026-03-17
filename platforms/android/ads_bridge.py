"""EN: pyjnius bridge between Python ads provider and Java Google Mobile Ads helper.
RU: pyjnius-мост между Python ads provider и Java-helper для Google Mobile Ads.
"""

from __future__ import annotations

from kivy.core.window import Window
from manager.ads.ads_types import ads_log


class AndroidAdsBridge:
    """EN: Runtime-safe bridge that forwards Android ads operations into the compiled Java helper.
    RU: Runtime-safe bridge, перенаправляющий Android ads-операции в скомпилированный Java-helper.
    """

    def __init__(self) -> None:
        """EN: Bind Java classes lazily so Windows and desktop imports remain safe.
        RU: Лениво привязать Java-классы, чтобы импорты на Windows и desktop оставались безопасными.
        """

        from jnius import autoclass

        self._python_activity = autoclass("org.kivy.android.PythonActivity")
        self._activity = self._python_activity.mActivity
        self._bridge = autoclass("org.zenol.ads.AdsBridge")

    def initialize(self, admob_app_id: str) -> None:
        """EN: Initialize the Java helper and underlying Mobile Ads SDK once per runtime.
        RU: Инициализировать Java-helper и базовый Mobile Ads SDK один раз за runtime.
        """

        ads_log("bridge init request", provider="admob_mediation", app_id=str(admob_app_id or "-"))
        self._bridge.init(self._activity)

    def is_initialized(self) -> bool:
        """EN: Return whether the Java helper reports Mobile Ads SDK initialized.
        RU: Вернуть, сообщает ли Java-helper об инициализированном Mobile Ads SDK.
        """

        return bool(self._bridge.isInitialized())

    def get_last_init_detail(self) -> str:
        """EN: Return the latest Mobile Ads initialization detail string.
        RU: Вернуть последнюю строку detail по инициализации Mobile Ads.
        """

        return str(self._bridge.getLastInitDetail() or "")

    def _slot_bounds_px(self, slot_widget) -> tuple[int, int, int, int]:
        """EN: Convert Kivy slot bounds into Android top-left pixel coordinates and size.
        RU: Конвертировать границы Kivy-слота в Android-координаты и размер в пикселях с верхним левым углом.
        """

        x_win, y_win = slot_widget.to_window(0, 0)
        width = float(getattr(slot_widget, "width", 0.0) or 0.0)
        height = float(getattr(slot_widget, "height", 0.0) or 0.0)
        top = float(Window.height) - (float(y_win) + height)
        return (
            max(int(round(float(x_win))), 0),
            max(int(round(top)), 0),
            max(int(round(width)), 1),
            max(int(round(height)), 1),
        )

    def attach_banner(self, slot_widget, banner_unit_id: str) -> None:
        """EN: Show a native AdView over the Kivy banner slot using current slot geometry.
        RU: Показать нативный AdView поверх Kivy banner-slot, используя текущую геометрию слота.
        """

        x_px, y_px, w_px, h_px = self._slot_bounds_px(slot_widget)
        ads_log("bridge banner slot px", w=w_px, h=h_px)
        self._bridge.showBanner(self._activity, str(banner_unit_id), int(x_px), int(y_px), int(w_px), int(h_px))

    def get_last_banner_detail(self) -> str:
        """EN: Return the latest Java-side banner detail string for diagnostics.
        RU: Вернуть последнюю Java-строку detail баннера для диагностики.
        """

        return str(self._bridge.getLastBannerDetail() or "")

    def detach_banner(self) -> None:
        """EN: Hide the native AdView.
        RU: Скрыть нативный AdView.
        """

        self._bridge.hideBanner(self._activity)

    def load_rewarded(self, rewarded_unit_id: str) -> None:
        """EN: Start loading one rewarded instance in Java.
        RU: Начать загрузку одного rewarded-инстанса на стороне Java.
        """

        self._bridge.loadRewarded(self._activity, str(rewarded_unit_id))

    def show_rewarded(self) -> None:
        """EN: Show the previously loaded rewarded if the Java helper marked it ready.
        RU: Показать ранее загруженный rewarded, если Java-helper отметил его готовым.
        """

        self._bridge.showRewarded(self._activity)

    def is_rewarded_finished(self) -> bool:
        """EN: Return True after rewarded fullscreen content was dismissed or failed.
        RU: Вернуть True после закрытия rewarded fullscreen-контента или ошибки показа.
        """

        return bool(self._bridge.isRewardedFinished())

    def consume_rewarded_earned(self) -> bool:
        """EN: Consume and reset the earned-reward flag reported by Java helper.
        RU: Забрать и сбросить флаг earned-reward, сообщённый Java-helper.
        """

        return bool(self._bridge.consumeRewardedEarned())

    def get_last_rewarded_detail(self) -> str:
        """EN: Return the latest Java-side rewarded detail string for diagnostics.
        RU: Вернуть последнюю Java-строку detail rewarded для диагностики.
        """

        return str(self._bridge.getLastRewardedDetail() or "")
