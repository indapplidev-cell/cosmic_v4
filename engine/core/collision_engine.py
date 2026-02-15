"""
Collision checks between the ship points and tile rectangles.

RU: Проверки коллизий между точками корабля и прямоугольниками тайлов.
"""


class CollisionEngine:
    """
    Evaluate whether the ship is still on any valid tile.

    RU: Определяет, находится ли корабль на допустимом тайле.
    """
    def ship_on_any_tile(
        self,
        ship_world_points,
        candidate_tiles,
        geometry,
        state,
        width,
        height,
        config,
        perspective_point_x,
        perspective_point_y,
    ):
        """
        Check if any ship vertex lies within any candidate tile rectangle.

        RU: Проверяет, попадает ли вершина корабля в прямоугольник любого тайла.
        """
        tiles_to_check = self._select_candidate_tiles(candidate_tiles, state)
        for tile_x, tile_y in tiles_to_check:
            if self._ship_on_tile(
                ship_world_points,
                tile_x,
                tile_y,
                geometry,
                state,
                width,
                height,
                config,
                perspective_point_x,
                perspective_point_y,
            ):
                return True
        return False

    def get_ship_points_on_tiles(
        self,
        ship_world_points,
        candidate_tiles,
        geometry,
        state,
        width,
        height,
        config,
        perspective_point_x,
        perspective_point_y,
    ):
        """
        Return per-point flags indicating whether each ship vertex is on a tile.

        EN: Produces a list of booleans aligned with ship_world_points order.
        RU: Возвращает список флагов по порядку ship_world_points.
        """
        tiles_to_check = self._select_candidate_tiles(candidate_tiles, state)
        tile_rects = [
            geometry.get_tile_rect_world(
                tile_x,
                tile_y,
                state,
                width,
                height,
                perspective_point_x,
                perspective_point_y,
                config,
            )
            for tile_x, tile_y in tiles_to_check
        ]
        results = []
        for px, py in ship_world_points:
            results.append(self._point_on_any_rect(px, py, tile_rects))
        return results

    def _select_candidate_tiles(self, tiles_coordinates, state):
        """
        Select tiles near the current loop position for collision checks.

        RU: Отбирает тайлы возле текущей позиции для проверки коллизий.
        """
        tiles_to_check = []
        for tile_x, tile_y in tiles_coordinates:
            if tile_y > state.current_y_loop + 1:
                break
            tiles_to_check.append((tile_x, tile_y))
        return tiles_to_check

    def _ship_on_tile(
        self,
        ship_world_points,
        tile_x,
        tile_y,
        geometry,
        state,
        width,
        height,
        config,
        perspective_point_x,
        perspective_point_y,
    ):
        """
        Determine if any ship vertex lies inside the given tile rectangle.

        RU: Определяет, находится ли вершина корабля внутри прямоугольника тайла.
        """
        xmin, ymin, xmax, ymax = geometry.get_tile_rect_world(
            tile_x,
            tile_y,
            state,
            width,
            height,
            perspective_point_x,
            perspective_point_y,
            config,
        )
        for px, py in ship_world_points:
            if xmin <= px <= xmax and ymin <= py <= ymax:
                return True
        return False

    def _point_on_any_rect(self, px, py, rects):
        """
        Check whether a point falls inside any rectangle in the list.

        EN: Uses axis-aligned rectangle bounds to evaluate containment.
        RU: Использует границы прямоугольников для проверки попадания.
        """
        for xmin, ymin, xmax, ymax in rects:
            if xmin <= px <= xmax and ymin <= py <= ymax:
                return True
        return False
