"""EN: Ads provider implementations used by the client ads manager.
RU: Реализации рекламных провайдеров, используемые клиентским ads manager.
"""

from manager.ads.providers.base import AdProvider
from manager.ads.providers.dummy import DummyAdProvider

__all__ = ["AdProvider", "DummyAdProvider"]
