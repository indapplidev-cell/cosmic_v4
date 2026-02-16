"""EN: Runtime screen orientation helpers for Android.
RU: Вспомогательные функции ориентации экрана для Android во время выполнения.
"""

from kivy.utils import platform as kivy_platform


def force_landscape() -> bool:
    """EN: Try to switch the Android activity to landscape orientation.
    RU: Попытаться переключить Android-активность в ландшафтную ориентацию.

    EN: Returns True when a landscape request was sent to the activity,
    otherwise returns False without raising errors.
    RU: Возвращает True, когда запрос ориентации отправлен активности,
    иначе возвращает False без выброса ошибок.
    """
    if kivy_platform != "android":
        return False

    try:
        from jnius import autoclass

        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        ActivityInfo = autoclass("android.content.pm.ActivityInfo")
        activity = PythonActivity.mActivity
        activity.setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_SENSOR_LANDSCAPE)
        return True
    except Exception:
        return False
