"""EN: Export all model classes so metadata is fully discoverable.
RU: Экспортировать все модели, чтобы metadata видела полный набор таблиц.
"""

from server.models.balance import Balance
from server.models.password_reset import PasswordResetToken
from server.models.profile_game import ProfileGame
from server.models.profile_user import ProfileUser
from server.models.telegram_account import TelegramAccount
from server.models.telegram_link_token import TelegramLinkToken
from server.models.telegram_outbox import TelegramOutbox
from server.models.telegram_verify_challenge import TelegramVerifyChallenge
from server.models.user import User

__all__ = [
    "User",
    "ProfileUser",
    "ProfileGame",
    "Balance",
    "PasswordResetToken",
    "TelegramAccount",
    "TelegramLinkToken",
    "TelegramOutbox",
    "TelegramVerifyChallenge",
]
