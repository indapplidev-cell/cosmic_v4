"""EN: Short-lived numeric code generation and hashing helpers.
RU: Хелперы генерации и хеширования коротких одноразовых кодов.
"""

from __future__ import annotations

import hashlib
import secrets


def hash_code(code: str, secret: str) -> str:
    """EN: Hash one-time code with server secret salt using SHA-256.
    RU: Хешировать одноразовый код с серверной солью через SHA-256.
    """

    payload = f"{(code or '').strip()}{(secret or '').strip()}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def gen_6digit_code() -> str:
    """EN: Generate cryptographically secure 6-digit code in 000000..999999 range.
    RU: Сгенерировать криптографически стойкий 6-значный код в диапазоне 000000..999999.
    """

    return f"{secrets.randbelow(1_000_000):06d}"

