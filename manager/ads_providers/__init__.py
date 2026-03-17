"""EN: Compatibility wrapper package for ads providers.
RU: Совместимый пакет-обёртка для ads-провайдеров.
"""

from manager.ads.providers.admob import AdMobAdsProvider
from manager.ads.providers.base import BaseAdsProvider
from manager.ads.providers.dummy import DummyAdProvider, DummyAdsProvider

__all__ = ["BaseAdsProvider", "DummyAdProvider", "DummyAdsProvider", "AdMobAdsProvider"]
