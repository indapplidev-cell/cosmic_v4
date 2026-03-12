"""EN: Future Yandex provider hook reserved for Android SDK integration.
RU: Будущий hook-провайдер Yandex, зарезервированный для Android SDK integration.
"""


class YandexProvider:
    """EN: Placeholder provider class until real Yandex SDK bridge is connected.
    RU: Placeholder-класс провайдера до подключения реального Yandex SDK bridge.
    """

    def __init__(self, *args, **kwargs) -> None:
        """EN: Refuse runtime usage until real SDK-backed implementation is added.
        RU: Запретить runtime-использование, пока не добавлена реальная SDK-backed реализация.
        """

        raise NotImplementedError("Yandex SDK bridge is not connected yet.")
