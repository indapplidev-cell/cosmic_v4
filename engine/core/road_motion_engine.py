"""
Motion stepper for advancing offsets based on elapsed time.

RU: Движок движения для обновления смещений по прошедшему времени.
"""


class MotionResult:
    """
    Result container describing how many rows were advanced this tick.

    RU: Контейнер результата с количеством пройденных рядов за тик.
    """
    def __init__(self, advanced_rows):
        """
        Store the number of advanced rows.

        RU: Сохраняет количество пройденных рядов.
        """
        self.advanced_rows = advanced_rows


class RoadMotionEngine:
    """
    Update longitudinal and lateral offsets based on current speed.

    RU: Обновляет продольные и боковые смещения на основе текущей скорости.
    """
    def step(self, dt, state, size, config):
        """
        Advance state offsets for one frame and return motion summary.

        RU: Обновляет смещения состояния за один кадр и возвращает итог.
        """
        time_factor = dt * 60
        height = size[1]

        base_speed_y = config.SPEED * height / 100
        speed_y = base_speed_y * state.speed_y_factor
        spacing_y = config.H_LINES_SPACING * height
        advanced_rows = self._advance_forward(state, time_factor, speed_y, spacing_y)

        speed_x = state.current_speed_x * size[0] / 100
        self._apply_lateral(state, time_factor, speed_x)

        return MotionResult(advanced_rows)

    def _advance_forward(self, state, time_factor, speed_y, spacing_y):
        """
        Update forward offset and loop count based on vertical speed.

        RU: Обновляет продольное смещение и счётчик рядов по вертикальной скорости.
        """
        state.current_offset_y += speed_y * time_factor
        advanced_rows = 0
        while state.current_offset_y >= spacing_y:
            state.current_offset_y -= spacing_y
            state.current_y_loop += 1
            advanced_rows += 1
        return advanced_rows

    def _apply_lateral(self, state, time_factor, speed_x):
        """
        Update lateral offset based on horizontal speed.

        RU: Обновляет боковое смещение по горизонтальной скорости.
        """
        state.current_offset_x += speed_x * time_factor
