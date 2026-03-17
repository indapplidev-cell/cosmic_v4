"""EN: Ads providers package exports runtime-safe provider implementations.
RU: Пакет ads-провайдеров экспортирует runtime-safe реализации провайдеров.
"""

from manager.ads.providers.admob import AdMobAdsProvider
from manager.ads.providers.base import AdProvider, BaseAdsProvider
from manager.ads.providers.dummy import DummyAdProvider, DummyAdsProvider

__all__ = [
    "BaseAdsProvider",
    "AdProvider",
    "DummyAdProvider",
    "DummyAdsProvider",
    "AdMobAdsProvider",
]
