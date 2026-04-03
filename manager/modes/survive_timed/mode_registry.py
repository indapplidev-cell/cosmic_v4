# -*- coding: utf-8 -*-
"""EN: Mode selector entrypoint for survive_timed default gameplay.
RU: Точка выбора режима, делающая survive_timed режимом по умолчанию.
"""

from __future__ import annotations


SURVIVE_TIMED_MODE_CODE = "survive_timed"
_DEFAULT_GAME_MODE_CODE = SURVIVE_TIMED_MODE_CODE


def get_default_game_mode_code() -> str:
    """EN: Return the default gameplay mode code for the project.
    RU: Вернуть код игрового режима по умолчанию для проекта.
    """

    return _DEFAULT_GAME_MODE_CODE