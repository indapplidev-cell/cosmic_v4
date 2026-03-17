"""EN: Compatibility wrapper for the shared ads provider base contract.
RU: Совместимая обёртка для общего базового контракта ads-провайдера.
"""

from manager.ads.providers.base import AdProvider, BaseAdsProvider

__all__ = ["BaseAdsProvider", "AdProvider"]
