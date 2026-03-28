"""EN: Minimal server-side wallet address validation for internal payout request contract.
RU: Минимальная серверная валидация адреса кошелька для внутреннего payout request контракта.
"""

from __future__ import annotations

import re


_WALLET_RE = re.compile(r"^[A-Za-z0-9:_-]{8,128}$")


class PayoutWalletValidationError(Exception):
    """EN: Domain error for invalid payout wallet address input.
    RU: Доменная ошибка для невалидного входного адреса payout-кошелька.
    """

    def __init__(self, error_code: str = "PAYOUT_WALLET_ADDRESS_INVALID") -> None:
        super().__init__(error_code)
        self.error_code = str(error_code)


def validate_payout_wallet_address(wallet_address: str) -> str:
    """EN: Validate payout wallet address with honest rail-agnostic structural checks only.
    RU: Проверить payout wallet address только честными rail-agnostic структурными проверками.

    EN: The project does not yet fix the final payout rail, so this validator does not claim
    chain-specific crypto correctness. It only rejects empty, too short/long, or unsafe values.
    RU: В проекте пока не зафиксирован окончательный payout rail, поэтому валидатор не изображает
    chain-specific крипто-проверку. Он отклоняет только пустые, слишком короткие/длинные или небезопасные значения.
    """

    normalized = str((wallet_address or "").strip())
    if not normalized:
        raise PayoutWalletValidationError()
    if not _WALLET_RE.fullmatch(normalized):
        raise PayoutWalletValidationError()
    return normalized
