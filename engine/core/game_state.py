"""
Mutable state holder for the current game session.

RU: Изменяемое хранилище состояния текущей игровой сессии.
"""


class GameState:
    """
    Store runtime flags and offsets used by motion, rendering, and scoring.

    RU: Хранит флаги и смещения, используемые движением, рендером и счётом.
    """
    def __init__(self):
        """
        Initialize all state fields to their default values.

        RU: Инициализирует все поля состояния значениями по умолчанию.
        """
        self.state_game_over = False
        self.state_game_has_started = False
        self.current_offset_x = 0
        self.current_offset_y = 0
        self.current_y_loop = 0
        self.current_speed_x = 0
        self.speed_y_factor = 1.0

    def reset(self):
        """
        Reset offsets, speed, and flags for a fresh run.

        RU: Сбрасывает смещения, скорость и флаги для нового запуска.
        """
        self.current_offset_x = 0
        self.current_offset_y = 0
        self.current_y_loop = 0
        self.current_speed_x = 0
        self.speed_y_factor = 1.0
        self.state_game_over = False
        self.state_game_has_started = False

    def mark_started(self):
        """
        Mark the game as started to allow movement updates.

        RU: Помечает игру как стартовавшую для обновлений движения.
        """
        self.state_game_has_started = True

    def mark_game_over(self):
        """
        Mark the game as over to stop progression.

        RU: Помечает игру как завершённую, чтобы остановить прогресс.
        """
        self.state_game_over = True
