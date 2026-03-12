"""EN: Future AdMob provider hook reserved for Android SDK integration.
RU: Будущий hook-провайдер AdMob, зарезервированный для Android SDK integration.
"""


class AdMobProvider:
    """EN: Placeholder provider class until real AdMob SDK bridge is connected.
    RU: Placeholder-класс провайдера до подключения реального AdMob SDK bridge.
    """

    def __init__(self, *args, **kwargs) -> None:
        """EN: Refuse runtime usage until real SDK-backed implementation is added.
        RU: Запретить runtime-использование, пока не добавлена реальная SDK-backed реализация.
        """

        raise NotImplementedError("AdMob SDK bridge is not connected yet.")
