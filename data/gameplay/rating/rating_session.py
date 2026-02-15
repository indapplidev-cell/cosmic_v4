"""EN: Rating session state for the game screen.
RU: Состояние рейтинговой сессии экрана игры.
"""

from __future__ import annotations


class RatingSession:
    """EN: Collect per-session statistics for rating calculation.
    RU: Собирать статистику сессии для расчета рейтинга.
    """

    def __init__(self) -> None:
        """EN: Initialize session counters and timers.
        RU: Инициализировать счетчики и таймеры сессии.
        """
        self.starts_total = 0
        self.valid_starts = 0
        self.current_run_started_at = None
        self.current_run_validated = False
        self.best_life_score = 0
        self.current_life_score = 0
        self.best_game_score = 0
        self.gameplay_started_at = None
        self.gameplay_duration_sec = 0.0

    def on_press_start(self, now: float, current_score: int) -> None:
        """EN: Register a start press and initialize run state.
        RU: Зарегистрировать нажатие старта и инициализировать run.
        """
        self.starts_total += 1
        self.current_run_started_at = now
        self.current_run_validated = False
        self.current_life_score = int(current_score)
        self.best_game_score = max(self.best_game_score, int(current_score))
        if self.gameplay_started_at is None:
            self.gameplay_started_at = now

    def on_score_changed(self, new_score: int) -> None:
        """EN: Update current and best scores based on the new score.
        RU: Обновить текущие и лучшие значения по новому счету.
        """
        score = int(new_score)
        self.current_life_score = max(self.current_life_score, score)
        self.best_game_score = max(self.best_game_score, score)

    def on_life_lost(self) -> None:
        """EN: Update best life score when a life is lost.
        RU: Обновить лучший счет за жизнь при потере жизни.
        """
        self.best_life_score = max(self.best_life_score, self.current_life_score)
        self.current_life_score = 0

    def on_game_over(self, now: float) -> None:
        """EN: Finalize scores and gameplay duration on game over.
        RU: Финализировать счет и длительность геймплея при проигрыше.
        """
        self.best_life_score = max(self.best_life_score, self.current_life_score)
        self.current_life_score = 0
        if self.gameplay_started_at is not None:
            self.gameplay_duration_sec = max(0.0, now - self.gameplay_started_at)
        self.try_validate_current_run(now)

    def on_exit_back(self, now: float) -> None:
        """EN: Finalize the current run when exiting the game screen.
        RU: Финализировать текущий run при выходе с экрана игры.
        """
        self.try_validate_current_run(now)

    def try_validate_current_run(self, now: float, t_min: float = 9.0) -> None:
        """EN: Validate the current run if it lasts at least t_min seconds.
        RU: Засчитать текущий run, если он длится не меньше t_min секунд.
        """
        if self.current_run_started_at is None:
            return
        if self.current_run_validated:
            return
        if (now - self.current_run_started_at) >= t_min:
            self.valid_starts += 1
            self.current_run_validated = True
