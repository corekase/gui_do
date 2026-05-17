"""Animated shape backdrop feature for the gui_do demo screen."""

from __future__ import annotations

import math
import random
from typing import Optional

import pygame

from gui_do import DirectFeature

from .moving_shapes_specs import (
    DEMO_BORDER_BASE_COLOUR,
    DEMO_SHAPE_COLOURS,
    MOVING_SHAPES_ALPHA_RANGE,
    MOVING_SHAPES_DEFINITIONS,
    MOVING_SHAPES_MIN_SPEED,
    MOVING_SHAPES_RADIUS_RANGE,
    MOVING_SHAPES_SPEED_BASE,
    MOVING_SHAPES_SPEED_VARIANCE,
)
from .shape_sprite_state import ShapeSpriteState


class MovingShapesBackdropFeature(DirectFeature):
    """Render and animate cached random geometric sprites directly on screen."""

    HOST_REQUIREMENTS = {
        "bind_runtime": ("app", "screen_rect"),
    }

    def __init__(
        self,
        *,
        total_shapes: int = 48,
        seed: Optional[int] = None,
        scene_name: Optional[str] = None,
        feature_name: str = "moving_shapes_backdrop",
    ) -> None:
        super().__init__(feature_name, scene_name=scene_name)
        self._total_shapes = max(0, int(total_shapes))
        self._rng = random.Random(seed)
        self._shapes: list[ShapeSpriteState] = []
        self._create_shapes()
        self._rng.shuffle(self._shapes)

    def bind_runtime(self, host) -> None:
        """Initialize random shape positions using screen bounds from the host."""
        width, height = host.screen_rect.size
        self._randomize_positions(width, height)

    def on_direct_update(self, host, dt_seconds: float) -> None:
        """Advance shape centers by velocity * dt and bounce off screen boundaries."""
        width = int(host.screen_rect.width)
        height = int(host.screen_rect.height)
        frame_delta = max(0.0, float(dt_seconds))
        for shape in self._shapes:
            shape.center_x += shape.velocity_x * frame_delta
            shape.center_y += shape.velocity_y * frame_delta

            if shape.center_x - shape.radius <= 0:
                shape.center_x = float(shape.radius)
                shape.velocity_x = abs(shape.velocity_x)
            elif shape.center_x + shape.radius >= width:
                shape.center_x = float(width - shape.radius)
                shape.velocity_x = -abs(shape.velocity_x)

            if shape.center_y - shape.radius <= 0:
                shape.center_y = float(shape.radius)
                shape.velocity_y = abs(shape.velocity_y)
            elif shape.center_y + shape.radius >= height:
                shape.center_y = float(height - shape.radius)
                shape.velocity_y = -abs(shape.velocity_y)

    def draw_direct(self, _host, surface, _theme) -> None:
        """Draw current shape sprites on the already-restored frame surface."""
        for shape in self._shapes:
            left = int(round(shape.center_x - shape.radius))
            top = int(round(shape.center_y - shape.radius))
            surface.blit(shape.sprite, (left, top))

    def _create_shapes(self) -> None:
        """Divide total_shapes evenly among all available shape types."""
        num_types = len(MOVING_SHAPES_DEFINITIONS)
        if num_types == 0:
            return
        base, remainder = divmod(self._total_shapes, num_types)
        for i, (num_sides, is_star) in enumerate(MOVING_SHAPES_DEFINITIONS):
            count = base + (1 if i < remainder else 0)
            for _ in range(count):
                if num_sides == 0:
                    self._shapes.append(self._create_circle_shape())
                else:
                    self._shapes.append(self._create_polygon_shape(num_sides, is_star))

    def _create_circle_shape(self) -> ShapeSpriteState:
        """Create one cached circular sprite with initial velocity."""
        radius, sprite, fill_color, border_color = self._create_shape_surface_and_colors()
        center = (radius, radius)
        pygame.draw.circle(sprite, border_color, center, radius)
        pygame.draw.circle(sprite, fill_color, center, max(1, radius - 3))
        return self._build_shape_state(sprite, radius)

    def _create_polygon_shape(self, num_sides: int, is_star: bool) -> ShapeSpriteState:
        """Create a polygon sprite using evenly-divided degree points and a random rotation offset."""
        radius, sprite, fill_color, border_color = self._create_shape_surface_and_colors()
        center_x = float(radius)
        center_y = float(radius)
        outer_r = float(radius - 1)
        inner_r = outer_r * 0.5
        num_points = num_sides * 2 if is_star else num_sides
        step_deg = 360.0 / num_points
        start_deg = self._rng.uniform(0.0, 360.0)
        points = []
        for i in range(num_points):
            angle_deg = start_deg + step_deg * i
            angle_rad = math.radians(angle_deg)
            point_r = (inner_r if i % 2 else outer_r) if is_star else outer_r
            px = center_x + math.cos(angle_rad) * point_r
            py = center_y + math.sin(angle_rad) * point_r
            points.append((int(round(px)), int(round(py))))
        pygame.draw.polygon(sprite, fill_color, points)
        pygame.draw.polygon(sprite, border_color, points, width=3)
        return self._build_shape_state(sprite, radius)

    def _create_shape_surface_and_colors(self) -> tuple[int, pygame.Surface, tuple[int, int, int, int], tuple[int, int, int, int]]:
        """Build a base square ARGB surface plus randomized fill/border colors."""
        radius = self._rng.randint(*MOVING_SHAPES_RADIUS_RANGE)
        diameter = radius * 2
        sprite = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        base_color = self._rng.choice(DEMO_SHAPE_COLOURS)
        fill_alpha = self._rng.randint(*MOVING_SHAPES_ALPHA_RANGE)
        border_alpha = self._rng.randint(*MOVING_SHAPES_ALPHA_RANGE)
        fill_color = base_color + (fill_alpha,)
        border_color = DEMO_BORDER_BASE_COLOUR + (border_alpha,)
        return radius, sprite, fill_color, border_color

    def _build_shape_state(self, sprite: pygame.Surface, radius: int) -> ShapeSpriteState:
        """Finalize sprite and motion into a ShapeSpriteState."""
        velocity_x, velocity_y = self._random_velocity()
        return ShapeSpriteState(
            radius=int(radius),
            sprite=sprite,
            center_x=0.0,
            center_y=0.0,
            velocity_x=velocity_x,
            velocity_y=velocity_y,
        )

    def _random_velocity(self) -> tuple[float, float]:
        """Create a random velocity vector with bounded speed."""
        boosted_min_speed = float(MOVING_SHAPES_MIN_SPEED) * 1.10
        random_bonus = MOVING_SHAPES_SPEED_BASE + self._rng.uniform(0.0, MOVING_SHAPES_SPEED_VARIANCE)
        speed = boosted_min_speed + random_bonus
        angle = self._rng.uniform(0.0, math.tau)
        velocity_x = math.cos(angle) * speed
        velocity_y = math.sin(angle) * speed
        return velocity_x, velocity_y

    def _randomize_positions(self, width: int, height: int) -> None:
        """Initialize random on-screen starting positions using current host size."""
        for shape in self._shapes:
            min_x = shape.radius
            max_x = max(min_x, int(width) - shape.radius)
            min_y = shape.radius
            max_y = max(min_y, int(height) - shape.radius)
            shape.center_x = float(self._rng.randint(min_x, max_x))
            shape.center_y = float(self._rng.randint(min_y, max_y))
