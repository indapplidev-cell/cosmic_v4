"""
Perspective projection math used to map world coordinates to screen space.

RU: Математика перспективной проекции для преобразования мировых координат
в экранные.
"""


class Perspective:
    """
    Hold a perspective point and provide transform helpers.

    RU: Хранит точку перспективы и предоставляет методы преобразования.
    """
    def __init__(self):
        """
        Initialize with a zeroed perspective point.

        RU: Инициализирует точку перспективы нулевыми значениями.
        """
        self.perspective_point_x = 0
        self.perspective_point_y = 0

    def set_perspective_point(self, x, y):
        """
        Set the perspective point in screen coordinates.

        RU: Устанавливает точку перспективы в экранных координатах.
        """
        self.perspective_point_x = x
        self.perspective_point_y = y

    def transform(self, x, y, height):
        """
        Transform a world point using the perspective projection.

        RU: Преобразует мировую точку с использованием перспективной проекции.
        """
        return self.transform_perspective(x, y, height)

    def transform_2d(self, x, y):
        """
        Apply a direct 2D transform (identity with int rounding).

        RU: Прямое 2D-преобразование (тождественное с округлением).
        """
        return int(x), int(y)

    def transform_perspective(self, x, y, height):
        """
        Apply the non-linear perspective mapping used by the game.

        RU: Применяет нелинейное перспективное преобразование, используемое в игре.
        """
        lin_y = y * self.perspective_point_y / height
        if lin_y > self.perspective_point_y:
            lin_y = self.perspective_point_y

        diff_x = x - self.perspective_point_x
        diff_y = self.perspective_point_y - lin_y
        factor_y = diff_y / self.perspective_point_y
        factor_y = pow(factor_y, 4)

        tr_x = self.perspective_point_x + diff_x * factor_y
        tr_y = self.perspective_point_y - factor_y * self.perspective_point_y

        return int(tr_x), int(tr_y)
