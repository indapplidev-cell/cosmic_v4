"""
Tile coordinate model and generation logic.

RU: Модель координат тайлов и логика их генерации.
"""

import random


class TilesModel:
    """
    Maintain the list of tile grid coordinates and generate more as needed.

    RU: Хранит список координат тайлов и генерирует новые по необходимости.
    """
    def __init__(self):
        """
        Initialize with an empty coordinate list.

        RU: Инициализирует пустой список координат.
        """
        self.tiles_coordinates = []


    def reset(self, state, config):
        """
        Clear coordinates and rebuild the initial path from loop 0.

        EN: Prefills a straight segment at y=0 and extends to NB_TILES.
        RU: Предзаполняет прямой участок на y=0 и расширяет до NB_TILES.
        """
        self.tiles_coordinates = []
        self._prefill_from_base(0)
        self.extend_to_limit(config)

    def reset_at_loop(self, base_y: int, config) -> None:
        """
        Clear coordinates and rebuild the initial path starting at base_y.

        EN: Prefills a straight segment at base_y and extends to NB_TILES
        without resetting the current loop progress.
        RU: Предзаполняет прямой участок на base_y и расширяет до NB_TILES
        без сброса текущего прогресса цикла.
        """
        self.tiles_coordinates = []
        self._prefill_from_base(base_y)
        self.extend_to_limit(config)

    def _prefill_from_base(self, base_y: int) -> None:
        """
        Add a fixed initial straight section of tiles starting at base_y.

        EN: Appends ten center-lane tiles starting at base_y.
        RU: Добавляет десять тайлов центральной дорожки начиная с base_y.
        """
        for i in range(0, 10):
            self.tiles_coordinates.append((0, base_y + i))

    def _prefill(self):
        """
        Add a fixed initial straight section of tiles at loop start.

        EN: Convenience wrapper for prefill at base_y=0.
        RU: Удобный вызов prefill с base_y=0.
        """
        self._prefill_from_base(0)

    def _clamp_tile_x(self, tile_x, min_x, max_x):
        """
        Clamp tile_x to keep tile rectangles inside the grid bounds.

        RU: Ограничивает tile_x, чтобы прямоугольники тайлов оставались
        внутри границ сетки.
        """
        if tile_x < min_x:
            return min_x
        if tile_x > max_x:
            return max_x
        return tile_x

    def prune_passed_tiles(self, state):
        """
        Remove tiles that are already behind the current loop position.

        RU: Удаляет тайлы, уже оставшиеся позади текущей позиции.
        """
        for i in range(len(self.tiles_coordinates) - 1, -1, -1):
            if self.tiles_coordinates[i][1] < state.current_y_loop:
                del self.tiles_coordinates[i]


    def extend_to_limit(self, config) -> None:
        """
        Extend the tile path up to the configured count.

        EN: Continues from the current last tile so respawns preserve height.
        RU: Продолжает от последнего тайла, чтобы респауны сохраняли высоту.
        """
        last_x = 0
        last_y = 0

        if len(self.tiles_coordinates) > 0:
            last_coordinates = self.tiles_coordinates[-1]
            last_x = last_coordinates[0]
            last_y = last_coordinates[1] + 1

        for _ in range(len(self.tiles_coordinates), config.NB_TILES):
            r = random.randint(0, 2)
            start_index = -int(config.V_NB_LINES / 2) + 1
            end_index = start_index + config.V_NB_LINES - 1
            min_x = start_index
            max_x = end_index - 1
            last_x = self._clamp_tile_x(last_x, min_x, max_x)
            if last_x <= min_x:
                r = 1
            if last_x >= max_x:
                r = 2

            self.tiles_coordinates.append((last_x, last_y))
            if r == 1:
                last_x = self._clamp_tile_x(last_x + 1, min_x, max_x)
                self.tiles_coordinates.append((last_x, last_y))
                last_y += 1
                self.tiles_coordinates.append((last_x, last_y))
            if r == 2:
                last_x = self._clamp_tile_x(last_x - 1, min_x, max_x)
                self.tiles_coordinates.append((last_x, last_y))
                last_y += 1
                self.tiles_coordinates.append((last_x, last_y))

            last_y += 1

    def generate_more(self, state, config):
        """
        Extend the tile path up to the configured count using the step algorithm.

        EN: Delegates to extend_to_limit to continue from existing tiles.
        RU: Делегирует в extend_to_limit, чтобы продолжить от текущих тайлов.
        """
        self.extend_to_limit(config)

    def ensure_respawn_tiles(self, state) -> None:
        """
        Ensure center tiles exist under the ship for the current loop rows.

        EN: Adds the center lane tiles at the current loop row and the next row
        so a soft reset does not immediately trigger another loss.
        RU: Добавляет тайлы центральной дорожки в текущем ряду и следующем, чтобы
        мягкий сброс не приводил к мгновенному повторному проигрышу.
        """
        respawn_x = 0
        y0 = state.current_y_loop
        y1 = state.current_y_loop + 1
        for tile in ((respawn_x, y0), (respawn_x, y1)):
            if tile not in self.tiles_coordinates:
                self.tiles_coordinates.append(tile)

