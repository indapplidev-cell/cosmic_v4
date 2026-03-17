"""EN: Password hashing and verification utilities for server-side authentication.
RU: Утилиты хеширования и проверки паролей для серверной аутентификации.
"""

from __future__ import annotations

import os

from passlib.context import CryptContext


def _get_bcrypt_rounds() -> int:
    """EN: Read bcrypt rounds from env and return a safe integer value.
    RU: Прочитать количество раундов bcrypt из окружения и вернуть безопасное целое значение.
    """

    rounds_raw = os.getenv("BCRYPT_ROUNDS", "12").strip()
    try:
        rounds = int(rounds_raw)
    except (TypeError, ValueError):
        rounds = 12

    if rounds < 4:
        return 4
    if rounds > 31:
        return 31
    return rounds


def _get_pepper() -> str:
    """EN: Return optional password pepper from environment.
    RU: Вернуть опциональный pepper для паролей из переменных окружения.
    """

    return os.getenv("PASSWORD_PEPPER", "")


def _apply_pepper(plain: str) -> str:
    """EN: Combine plaintext password with optional pepper before hashing/verification.
    RU: Объединить plaintext-пароль с опциональным pepper перед хешированием/проверкой.
    """

    pepper = _get_pepper()
    return f"{plain}{pepper}" if pepper else plain


def get_pwd_context() -> CryptContext:
    """EN: Build passlib CryptContext configured for bcrypt and current cost.
    RU: Создать passlib CryptContext, настроенный на bcrypt и текущий cost.
    """

    return CryptContext(
        schemes=["bcrypt"],
        deprecated="auto",
        bcrypt__rounds=_get_bcrypt_rounds(),
    )


def hash_password(plain: str) -> str:
    """EN: Hash plaintext password using bcrypt with optional pepper.
    RU: Захешировать plaintext-пароль через bcrypt с опциональным pepper.
    """

    return get_pwd_context().hash(_apply_pepper(plain))


def verify_password(plain: str, hashed: str) -> bool:
    """EN: Verify plaintext password against stored bcrypt hash.
    RU: Проверить plaintext-пароль против сохранённого bcrypt-хеша.
    """

    return get_pwd_context().verify(_apply_pepper(plain), hashed)


def needs_rehash(hashed: str) -> bool:
    """EN: Check whether stored hash should be upgraded to current bcrypt cost.
    RU: Проверить, требуется ли обновить сохранённый хеш до текущего cost bcrypt.
    """

    return get_pwd_context().needs_update(hashed)
