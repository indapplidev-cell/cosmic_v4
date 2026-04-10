"""EN: Export all model classes so metadata is fully discoverable.
RU: Экспортировать все модели, чтобы metadata видела полный набор таблиц.
"""

from server.db.models.balance import Balance
from server.db.models.ads_event import AdsEvent
from server.db.models.ads_setting import AdsSetting
from server.db.models.payout_link_code import PayoutLinkCode
from server.db.models.payout_miniapp_session import PayoutMiniAppSession
from server.db.models.payout_request import PayoutRequest
from server.db.models.profile_game import ProfileGame
from server.db.models.profile_user import ProfileUser
from server.db.models.refresh_token import RefreshToken
from server.db.models.telegram_account import TelegramAccount
from server.db.models.telegram_link_token import TelegramLinkToken
from server.db.models.telegram_outbox import TelegramOutbox
from server.db.models.telegram_reset_challenge import TelegramResetChallenge
from server.db.models.telegram_reset_request import TelegramResetRequest
from server.db.models.telegram_verify_challenge import TelegramVerifyChallenge
from server.db.models.user import User
from server.db.models.user_level_score_record import UserLevelScoreRecord
from server.db.models.modes.survive_timed.user_campaign_progress import SurviveTimedUserCampaignProgress
from server.db.models.modes.survive_timed.user_level_result import SurviveTimedUserLevelResult

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
    "PayoutRequest",
    "TelegramAccount",
    "TelegramLinkToken",
    "TelegramOutbox",
    "TelegramResetRequest",
    "TelegramResetChallenge",
    "TelegramVerifyChallenge",
    "UserLevelScoreRecord",
    "SurviveTimedUserCampaignProgress",
    "SurviveTimedUserLevelResult",
]
