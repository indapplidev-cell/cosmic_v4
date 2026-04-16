from __future__ import annotations

from kivy.graphics.context_instructions import Color
from kivy.graphics.vertex_instructions import Line, Quad

from client.gameplay.road.render.visual_road_geometry import VisualRoadSegment, build_visual_row_segments
from client.gameplay.road.render.render_quality_profile import RenderQualityProfile, build_render_quality_profile
from client.gameplay.road.road_models import FrameSnapshot, RoadRow
from client.gameplay.road.world_grid_spec import WorldGridSpec


class _QuadBinding:
    def __init__(self, canvas) -> None:
        with canvas:
            self._color = Color(0, 0, 0, 0)
            self._quad = Quad(points=self._hidden_quad())

    def draw(self, visual_quad) -> None:
        if visual_quad is None:
            self.hide()
            return
        points, rgba = visual_quad
        self._color.rgba = rgba
        self._quad.points = list(points)

    def hide(self) -> None:
        self._color.rgba = (0, 0, 0, 0)
        self._quad.points = self._hidden_quad()

    @staticmethod
    def _hidden_quad() -> list[float]:
        return [-10_000.0, -10_000.0] * 4


class _LineBinding:
    def __init__(self, canvas) -> None:
        with canvas:
            self._color = Color(0, 0, 0, 0)
            self._line = Line(points=self._hidden_line(), width=1.0)

    def draw(self, visual_line) -> None:
        if visual_line is None:
            self.hide()
            return
        points, rgba, width = visual_line
        self._color.rgba = rgba
        self._line.width = float(width)
        self._line.points = list(points)

    def hide(self) -> None:
        self._color.rgba = (0, 0, 0, 0)
        self._line.points = self._hidden_line()

    @staticmethod
    def _hidden_line() -> list[float]:
        return [-10_000.0, -10_000.0, -10_000.0, -10_000.0]


class _RowBinding:
    def __init__(
        self,
        canvas,
        max_lane_count: int,
        max_grid_lines: int,
        max_entities: int,
        max_road_segments: int,
    ) -> None:
        self._road_quads = [_QuadBinding(canvas) for _ in range(max_road_segments)]
        self._road_outlines = [_LineBinding(canvas) for _ in range(max_road_segments)]
        self._lane_quads = [_QuadBinding(canvas) for _ in range(max_lane_count)]
        self._grid_lines = [_LineBinding(canvas) for _ in range(max_grid_lines)]
        self._entity_quads = [_QuadBinding(canvas) for _ in range(max_entities)]
        self._entity_outlines = [_LineBinding(canvas) for _ in range(max_entities)]

    def draw(self, row_visual) -> None:
        if row_visual is None:
            self.hide()
            return
        road_quads = row_visual['road_quads']
        for index, binding in enumerate(self._road_quads):
            binding.draw(road_quads[index] if index < len(road_quads) else None)

        road_outlines = row_visual['road_outlines']
        for index, binding in enumerate(self._road_outlines):
            binding.draw(road_outlines[index] if index < len(road_outlines) else None)

        lane_quads = row_visual['lane_quads']
        for index, binding in enumerate(self._lane_quads):
            binding.draw(lane_quads[index] if index < len(lane_quads) else None)

        grid_lines = row_visual['grid_lines']
        for index, binding in enumerate(self._grid_lines):
            binding.draw(grid_lines[index] if index < len(grid_lines) else None)

        entity_visuals = row_visual['entity_visuals']
        for index, binding in enumerate(self._entity_quads):
            quad = entity_visuals[index][0] if index < len(entity_visuals) else None
            binding.draw(quad)
        for index, binding in enumerate(self._entity_outlines):
            outline = entity_visuals[index][1] if index < len(entity_visuals) else None
            binding.draw(outline)

    def hide(self) -> None:
        for binding in self._road_quads:
            binding.hide()
        for binding in self._road_outlines:
            binding.hide()
        for binding in self._lane_quads:
            binding.hide()
        for binding in self._grid_lines:
            binding.hide()
        for binding in self._entity_quads:
            binding.hide()
        for binding in self._entity_outlines:
            binding.hide()


class GameplayRenderer:
    def __init__(self, canvas, config, projector) -> None:
        self._canvas = canvas
        self._config = config
        self._projector = projector
        self._row_bindings: list[_RowBinding] = []
        self._quality_profile: RenderQualityProfile = build_render_quality_profile(0, 1)

    def set_quality_profile(self, profile: RenderQualityProfile) -> None:
        self._quality_profile = profile

    def render(self, snapshot: FrameSnapshot, size: tuple[float, float]) -> None:
        width, height = size
        if width < 2 or height < 2:
            for binding in self._row_bindings:
                binding.hide()
            return

        road_profile = self._config.road_profile
        grid_spec = WorldGridSpec.from_profile(road_profile)
        self._projector.configure(
            width,
            height,
            grid_spec,
            road_profile.perspective,
            world_offset_x=float(snapshot.world_offset_x),
        )

        visible_rows = self._extract_visible_rows(snapshot.rows, grid_spec, snapshot.render_offset_y)
        visible_rows = self._apply_visible_row_limit(visible_rows)
        max_lane_count = max(int(getattr(self._config, 'MAX_LANES_SUPPORTED', 8)), int(road_profile.lane.lane_count), 1)
        max_grid_lines = max(int(grid_spec.line_end_index - grid_spec.line_start_index + 1), max_lane_count + 1, 1)
        max_entities = max_lane_count
        max_road_segments = max_lane_count
        max_rows = max(int(getattr(self._config, 'MAX_VISUAL_SEGMENTS_SUPPORTED', road_profile.pool_size)), len(visible_rows))
        self._ensure_row_bindings(max_rows, max_lane_count, max_grid_lines, max_entities, max_road_segments)

        tile_size_world = float(grid_spec.tile_size_world)
        total_rows = max(len(visible_rows) - 1, 1)
        row_visuals: list[dict[str, object]] = []

        for visible_index, (row, row_index, row_world) in enumerate(visible_rows):
            prev_row = visible_rows[visible_index - 1][0] if visible_index > 0 else None
            next_row = visible_rows[visible_index + 1][0] if visible_index < (len(visible_rows) - 1) else None
            variant = road_profile.visual_variants[int(row.seq) % len(road_profile.visual_variants)]
            visual_segments = build_visual_row_segments(prev_row, row, next_row)
            road_quads, road_outlines = self._build_row_road_segment_visuals(
                row=row,
                row_world=row_world,
                grid_spec=grid_spec,
                projector=self._projector,
                road_profile=road_profile,
                visual_segments=visual_segments,
            )
            lane_quads = self._build_visual_lane_quads(
                visual_segments,
                row_world,
                row.seq,
                grid_spec,
                self._projector,
                variant.lane_open_color,
            )
            grid_lines = self._build_grid_lines(
                row,
                row_world,
                visual_segments,
                grid_spec,
                self._projector,
                road_profile,
            )
            entity_visuals = tuple(
                visual
                for entity in row.entities
                for visual in (self._build_entity_visuals(
                    entity,
                    row_world,
                    tile_size_world,
                    grid_spec.playable_column_start,
                    self._projector,
                    road_profile,
                ),)
                if visual is not None
            )
            row_visuals.append(
                self._apply_depth_fade(
                    {
                        'road_quads': road_quads,
                        'road_outlines': road_outlines,
                        'lane_quads': lane_quads,
                        'grid_lines': grid_lines,
                        'entity_visuals': entity_visuals,
                    },
                    row_index,
                    total_rows,
                    float(road_profile.perspective.far_opacity),
                )
            )

        far_to_near = list(reversed(row_visuals))
        for index, binding in enumerate(self._row_bindings):
            binding.draw(far_to_near[index] if index < len(far_to_near) else None)

    def _extract_visible_rows(self, rows, grid_spec, row_offset):
        visible_count = max(int(grid_spec.visible_row_end - grid_spec.visible_row_start + 1), 0)
        resolved_rows = self._resolve_rows(rows, visible_count)
        visible_rows: list[tuple[RoadRow, int, float]] = []
        tile_size_world = float(grid_spec.tile_size_world)
        for index, row in enumerate(resolved_rows):
            world_row = float(grid_spec.visible_row_start + index) - float(row_offset)
            if (world_row + 1.0) * tile_size_world <= 0.0:
                continue
            visible_rows.append((row, index, world_row))
        return tuple(visible_rows)

    def _apply_visible_row_limit(self, visible_rows):
        max_visible_rows = getattr(self._quality_profile, 'max_visible_rows', None)
        if max_visible_rows is None:
            return tuple(visible_rows)
        return tuple(visible_rows[:max(int(max_visible_rows), 1)])

    def _resolve_rows(self, row_source, visible_count):
        if hasattr(row_source, 'visible_rows'):
            return row_source.visible_rows(visible_count)
        return tuple(tuple(row_source)[:visible_count])

    def _build_row_road_segment_visuals(
        self,
        row,
        row_world,
        grid_spec,
        projector,
        road_profile,
        visual_segments,
    ):
        segments = tuple(visual_segments)
        variant = road_profile.visual_variants[int(row.seq) % len(road_profile.visual_variants)]
        fill_alpha = float(road_profile.perspective.road_fill_alpha)
        outline_width = float(road_profile.perspective.grid_line_width)
        tile_size_world = float(grid_spec.tile_size_world)
        playable_column_start = int(grid_spec.playable_column_start)
        road_quads = []
        road_outlines = []
        for segment in segments:
            projected_band = self._build_visual_segment_quad(
                segment,
                row_world,
                row.seq,
                tile_size_world,
                playable_column_start,
                projector,
            )
            road_quads.append(
                (
                    self._flatten_quad(projected_band),
                    self._with_alpha(variant.road_color, fill_alpha),
                )
            )
            if self._quality_profile.draw_outlines:
                road_outlines.append(
                    (
                        self._flatten_polyline((projected_band[0], projected_band[1], projected_band[2], projected_band[3], projected_band[0])),
                        variant.shoulder_color,
                        outline_width,
                    )
                )
        return tuple(road_quads), tuple(road_outlines)

    def _build_visual_segment_quad(self, segment: VisualRoadSegment, row_world, row_seq, tile_size_world, playable_column_start, projector):
        x_lb = self._logical_x_to_world_x(segment.left, playable_column_start, tile_size_world)
        x_rb = self._logical_x_to_world_x(segment.right, playable_column_start, tile_size_world)
        x_lt = self._logical_x_to_world_x(segment.left, playable_column_start, tile_size_world)
        x_rt = self._logical_x_to_world_x(segment.right, playable_column_start, tile_size_world)
        row_base = float(row_seq)
        z0 = float(row_world + (float(segment.bottom) - row_base)) * tile_size_world
        z1 = float(row_world + (float(segment.top) - row_base)) * tile_size_world
        return (
            projector.project(x_lb, z0),
            projector.project(x_lt, z1),
            projector.project(x_rt, z1),
            projector.project(x_rb, z0),
        )

    def _logical_x_to_world_x(self, logical_x, playable_column_start, tile_size_world):
        return (float(playable_column_start) + float(logical_x) + 0.5) * float(tile_size_world)

    def _build_lane_quad(self, column, row_world, tile_size_world, playable_column_start, projector):
        world_column = int(playable_column_start) + int(column)
        world_quad = self._build_world_tile_quad(world_column, row_world, tile_size_world)
        return self._flatten_quad(self._project_tile_quad(world_quad, projector))

    def _build_visual_lane_quads(self, visual_segments, row_world, row_seq, grid_spec, projector, color):
        tile_size_world = float(grid_spec.tile_size_world)
        playable_column_start = int(grid_spec.playable_column_start)
        return tuple(
            (
                self._flatten_quad(
                    self._build_visual_segment_quad(
                        segment,
                        row_world,
                        row_seq,
                        tile_size_world,
                        playable_column_start,
                        projector,
                    )
                ),
                color,
            )
            for segment in visual_segments
        )

    def _build_world_tile_quad(self, col, row, tile_size_world):
        size = float(tile_size_world)
        x0 = float(col) * size
        x1 = float(col + 1) * size
        z0 = float(row) * size
        z1 = float(row + 1.0) * size
        return ((x0, z0), (x1, z0), (x1, z1), (x0, z1))

    def _project_tile_quad(self, world_quad, projector):
        projected = [projector.project(x, z) for x, z in world_quad]
        return projected[0], projected[3], projected[2], projected[1]

    def _build_grid_lines(self, road_row, row_world, visual_segments, grid_spec, projector, road_profile):
        if not self._quality_profile.draw_grid_lines:
            return ()
        variant = road_profile.visual_variants[int(road_row.seq) % len(road_profile.visual_variants)]
        width = float(road_profile.perspective.grid_line_width)
        tile_size_world = float(grid_spec.tile_size_world)
        playable_column_start = int(grid_spec.playable_column_start)
        grid_lines = []
        seen_boundaries: set[tuple[float, float]] = set()
        for segment in visual_segments:
            left_bottom = projector.project(
                self._logical_x_to_world_x(segment.left, playable_column_start, tile_size_world),
                float(row_world + (float(segment.bottom) - float(road_row.seq))) * tile_size_world,
            )
            left_top = projector.project(
                self._logical_x_to_world_x(segment.left, playable_column_start, tile_size_world),
                float(row_world + (float(segment.top) - float(road_row.seq))) * tile_size_world,
            )
            right_top = projector.project(
                self._logical_x_to_world_x(segment.right, playable_column_start, tile_size_world),
                float(row_world + (float(segment.top) - float(road_row.seq))) * tile_size_world,
            )
            right_bottom = projector.project(
                self._logical_x_to_world_x(segment.right, playable_column_start, tile_size_world),
                float(row_world + (float(segment.bottom) - float(road_row.seq))) * tile_size_world,
            )
            left_key = (
                round(float(segment.left), 6),
                round(float(segment.left), 6),
            )
            if left_key not in seen_boundaries:
                seen_boundaries.add(left_key)
                grid_lines.append(
                    (
                        self._flatten_polyline((left_bottom, left_top)),
                        variant.grid_color,
                        width,
                    )
                )
            right_key = (
                round(float(segment.right), 6),
                round(float(segment.right), 6),
            )
            if right_key not in seen_boundaries:
                seen_boundaries.add(right_key)
                grid_lines.append(
                    (
                        self._flatten_polyline((right_bottom, right_top)),
                        variant.grid_color,
                        width,
                    )
                )
        return tuple(grid_lines)

    def _build_entity_visuals(self, entity, row_world, tile_size_world, playable_column_start, projector, road_profile):
        world_column = int(playable_column_start) + int(entity.lane)
        entity_row = float(row_world) + float(entity.row_offset)
        tile_quad = self._build_world_tile_quad(world_column, entity_row, tile_size_world)
        tile_points = self._project_tile_quad(tile_quad, projector)
        config = road_profile.obstacle_visual

        if entity.kind == 'obstacle':
            fill_color = config.fill_color
            outline_color = config.outline_color
            outline_width = float(config.outline_width)
            bottom_alpha = float(config.inset_y_ratio)
            top_alpha = 1.0 - bottom_alpha
            left_bottom_edge = self._lerp_point(tile_points[0], tile_points[1], bottom_alpha)
            right_bottom_edge = self._lerp_point(tile_points[3], tile_points[2], bottom_alpha)
            left_top_edge = self._lerp_point(tile_points[0], tile_points[1], top_alpha)
            right_top_edge = self._lerp_point(tile_points[3], tile_points[2], top_alpha)
            bottom_left = self._lerp_point(left_bottom_edge, right_bottom_edge, float(config.inset_x_ratio))
            bottom_right = self._lerp_point(left_bottom_edge, right_bottom_edge, 1.0 - float(config.inset_x_ratio))
            top_inset = min(float(config.inset_x_ratio) + float(config.top_narrow_ratio), 0.45)
            top_left = self._lerp_point(left_top_edge, right_top_edge, top_inset)
            top_right = self._lerp_point(left_top_edge, right_top_edge, 1.0 - top_inset)
        else:
            fill_color = {
                'life': (0.22, 0.82, 0.34, 0.94),
                'speed': (0.18, 0.62, 0.98, 0.94),
                'time': (0.98, 0.76, 0.20, 0.94),
            }.get(entity.kind, (0.72, 0.72, 0.76, 0.94))
            outline_color = (1.0, 1.0, 1.0, 0.82)
            outline_width = float(config.outline_width)
            bottom_alpha = 0.28
            top_alpha = 0.72
            left_bottom_edge = self._lerp_point(tile_points[0], tile_points[1], bottom_alpha)
            right_bottom_edge = self._lerp_point(tile_points[3], tile_points[2], bottom_alpha)
            left_top_edge = self._lerp_point(tile_points[0], tile_points[1], top_alpha)
            right_top_edge = self._lerp_point(tile_points[3], tile_points[2], top_alpha)
            bottom_left = self._lerp_point(left_bottom_edge, right_bottom_edge, 0.28)
            bottom_right = self._lerp_point(left_bottom_edge, right_bottom_edge, 0.72)
            top_left = self._lerp_point(left_top_edge, right_top_edge, 0.34)
            top_right = self._lerp_point(left_top_edge, right_top_edge, 0.66)

        quad = (
            self._flatten_quad((bottom_left, top_left, top_right, bottom_right)),
            fill_color,
        )
        outline = (
            self._flatten_polyline((bottom_left, top_left, top_right, bottom_right, bottom_left)),
            outline_color,
            outline_width,
        )
        if not self._quality_profile.draw_outlines:
            outline = None
        return quad, outline

    def _apply_depth_fade(self, row_visual, row_index, total_rows, far_opacity):
        opacity = self._row_opacity(row_index, total_rows, far_opacity)
        return {
            'road_quads': tuple(
                (quad[0], self._fade_rgba(quad[1], opacity))
                for quad in row_visual['road_quads']
            ),
            'road_outlines': tuple(
                (outline[0], self._fade_rgba(outline[1], opacity), outline[2])
                for outline in row_visual['road_outlines']
            ),
            'lane_quads': tuple(
                (quad[0], self._fade_rgba(quad[1], opacity))
                for quad in row_visual['lane_quads']
            ),
            'grid_lines': tuple(
                (line[0], self._fade_rgba(line[1], opacity), line[2])
                for line in row_visual['grid_lines']
            ),
            'entity_visuals': tuple(
                (
                    (entity[0][0], self._fade_rgba(entity[0][1], opacity)),
                    None if entity[1] is None else (entity[1][0], self._fade_rgba(entity[1][1], opacity), entity[1][2]),
                )
                for entity in row_visual['entity_visuals']
            ),
        }

    def _row_opacity(self, row_index, total_rows, far_opacity):
        alpha = min(max(float(row_index) / float(max(total_rows, 1)), 0.0), 1.0)
        return 1.0 + (float(far_opacity) - 1.0) * alpha

    def _fade_rgba(self, rgba, opacity):
        return rgba[0], rgba[1], rgba[2], rgba[3] * opacity

    def _with_alpha(self, rgba, alpha_multiplier):
        return rgba[0], rgba[1], rgba[2], rgba[3] * alpha_multiplier

    def _flatten_quad(self, points):
        return (
            points[0][0], points[0][1],
            points[1][0], points[1][1],
            points[2][0], points[2][1],
            points[3][0], points[3][1],
        )

    def _flatten_polyline(self, points):
        flat_points = []
        for point in points:
            flat_points.extend((point[0], point[1]))
        return tuple(flat_points)

    def _ensure_row_bindings(self, count, max_lane_count, max_grid_lines, max_entities, max_road_segments):
        while len(self._row_bindings) < count:
            self._row_bindings.append(
                _RowBinding(self._canvas, max_lane_count, max_grid_lines, max_entities, max_road_segments)
            )

    def _lerp_point(self, start, end, alpha):
        return (
            start[0] + (end[0] - start[0]) * alpha,
            start[1] + (end[1] - start[1]) * alpha,
        )
