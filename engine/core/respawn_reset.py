# -*- coding: utf-8 -*-
"""
Respawn reset that restores the start-of-run state without touching score.

EN: Provides a single function that places the ship and tiles into the same
start position used for a fresh run, while keeping score intact.
RU: Предоставляет одну функцию, которая возвращает корабль и тайлы в стартовое
состояние, сохраняя текущий счет.
"""


def respawn_to_start(state, ship_engine, tiles_model, config) -> None:
    """
    Reset gameplay state to the start-of-run position without resetting score.

    EN: Re-centers the ship laterally, clears offsets/speed, and rebuilds tiles
    at the current loop height so score is preserved and respawn is safe.
    RU: Сбрасывает положение/скорость и смещения, пересоздаёт тайлы
    на текущей высоте цикла, чтобы счёт сохранялся и респаун был безопасным.
    """
    state.current_offset_x = 0
    state.current_speed_x = 0
    state.current_offset_y = 0
    state.state_game_over = False
    tiles_model.reset_at_loop(state.current_y_loop, config)
    tiles_model.ensure_respawn_tiles(state)
    ship_engine.reset_to_start(state)
