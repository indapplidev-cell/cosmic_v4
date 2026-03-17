"""EN: Smoke checks for server-side validation rules that map to FastAPI 422 responses.
RU: Smoke-проверки правил серверной валидации, которые в FastAPI мапятся в ответы 422.
"""

from __future__ import annotations

from pydantic import ValidationError

from server.api.schemas import LoginRequest, ProfileUserUpdateRequest, RegisterRequest


_BAD_PROFILE_PAYLOADS = [
    "'); DROP TABLE users; --",
    "<script>alert(1)</script>",
    "${jndi:ldap://x}",
    "javascript:alert(1)",
    "http://evil.com",
]


def _expect_validation_error(func, label: str) -> None:
    """EN: Expect schema validation to fail for invalid payload.
    RU: Ожидать ошибку валидации схемы для невалидного payload.
    """

    try:
        func()
    except ValidationError:
        print(f"OK reject: {label}")
        return
    raise RuntimeError(f"Expected validation error for: {label}")


def main() -> None:
    """EN: Run smoke checks for payload rejection and valid examples.
    RU: Запустить smoke-проверки на отклонение payload и валидные примеры.
    """

    for value in _BAD_PROFILE_PAYLOADS:
        _expect_validation_error(
            lambda value=value: ProfileUserUpdateRequest(user_id=1, login=value),
            f"profile.login={value}",
        )

    ok_profile = ProfileUserUpdateRequest(user_id=1, login="user_01", telegram="@user_name", phone="+31612345678")
    print("OK valid profile sample:", {"login": ok_profile.login, "telegram": ok_profile.telegram, "phone": ok_profile.phone})

    _expect_validation_error(
        lambda: RegisterRequest(email="not-email", psw="Qwerty12345!"),
        "auth.invalid_email",
    )
    _expect_validation_error(
        lambda: LoginRequest(email="test@test.com", psw="Qwerty\n12345!"),
        "auth.password_control_chars",
    )

    ok_auth = LoginRequest(email="test@test.com", psw="Qwerty12345!")
    print("OK valid auth sample:", {"email": str(ok_auth.email), "psw_len": len(ok_auth.psw)})


if __name__ == "__main__":
    main()
