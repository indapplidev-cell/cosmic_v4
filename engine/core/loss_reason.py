# -*- coding: utf-8 -*-
"""
Loss reason types for classifying why the ship left the safe tile path.

EN: Data-only definitions that label the type of loss without any gameplay or
UI decisions.
RU: Только типы данных, которые маркируют причину поражения без логики игры
или UI-решений.
"""

from enum import Enum


class LossReason(Enum):
    """
    Classification of why the ship is considered off the tiles.

    EN: Used by collision/tick code to communicate the loss cause to
    higher-level orchestration logic.
    RU: Используется кодом коллизий/тика для передачи причины поражения
    в более высокий уровень оркестрации.
    """

    OUT_OF_TILE_X = "out_of_tile_x"
    OUT_OF_TILE_TIP = "out_of_tile_tip"
    OUT_OF_TILE_GENERIC = "out_of_tile_generic"
