"""EN: Export all model classes so metadata is fully discoverable.
RU: Экспортировать все модели, чтобы metadata видела полный набор таблиц.
"""

from server.models.balance import Balance
from server.models.ads_event import AdsEvent
from server.models.ads_setting import AdsSetting
from server.models.payout_link_code import PayoutLinkCode
from server.models.payout_miniapp_session import PayoutMiniAppSession
from server.models.profile_game import ProfileGame
from server.models.profile_user import ProfileUser
from server.models.refresh_token import RefreshToken
from server.models.telegram_account import TelegramAccount
from server.models.telegram_link_token import TelegramLinkToken
from server.models.telegram_outbox import TelegramOutbox
from server.models.telegram_reset_challenge import TelegramResetChallenge
from server.models.telegram_reset_request import TelegramResetRequest
from server.models.telegram_verify_challenge import TelegramVerifyChallenge
from server.models.user import User
from server.models.user_level_score_record import UserLevelScoreRecord

__all__ = [
    "User",
    "AdsSetting",
    "AdsEvent",
    "ProfileUser",
    "ProfileGame",
    "Balance",
    "RefreshToken",
    "PayoutLinkCode",
    "PayoutMiniAppSession",
    "TelegramAccount",
    "TelegramLinkToken",
    "TelegramOutbox",
    "TelegramResetRequest",
    "TelegramResetChallenge",
    "TelegramVerifyChallenge",
    "UserLevelScoreRecord",
]
