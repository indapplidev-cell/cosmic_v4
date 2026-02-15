"""EN: Counters for game over and rewarded receive clicks.
RU: Счётчики для GameOver и нажатий на кнопку "Получить".
"""


class GameOverCounters:
    """EN: Store counters for GameOver flow events.
    RU: Хранить счётчики событий в процессе GameOver.
    """

    def __init__(self) -> None:
        """EN: Initialize counters with zero values.
        RU: Инициализировать счётчики нулевыми значениями.
        """
        self.gameover_count: int = 0
        self.receive_click_count: int = 0

    def inc_gameover(self) -> None:
        """EN: Increase GameOver events counter by one.
        RU: Увеличить счётчик GameOver на единицу.
        """
        self.gameover_count += 1

    def inc_receive_click(self) -> None:
        """EN: Increase rewarded receive button clicks counter by one.
        RU: Увеличить счётчик нажатий "Получить" на единицу.
        """
        self.receive_click_count += 1

    def dump_to_print(self) -> None:
        """EN: Print current counters in one line.
        RU: Вывести текущие счётчики одной строкой.
        """
        print(
            f"[GameOverCounters] gameover={self.gameover_count} "
            f"receive_click={self.receive_click_count}",
            flush=True,
        )


counters = GameOverCounters()

