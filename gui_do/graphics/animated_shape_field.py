"""Reusable animated geometric sprite field for backgrounds and effects."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

import pygame
from pygame import Surface


def random_shape_sprite(
    rng: random.Random,
    radius_range: Tuple[int, int],
    color_palette: Sequence[Tuple[int, int, int]],
    alpha_range: Tuple[int, int],
    border_color: Tuple[int, int, int],
    shape_def: Tuple[int, bool],
) -> Tuple[int, Surface]:
    """Create a sprite surface for a random shape (circle, polygon, star)."""
    num_sides, is_star = shape_def
    radius = rng.randint(*radius_range)
    diameter = radius * 2
    sprite = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
    base_color = rng.choice(color_palette)
    fill_alpha = rng.randint(*alpha_range)
    border_alpha = rng.randint(*alpha_range)
    fill_color = base_color + (fill_alpha,)
    border_color_rgba = border_color + (border_alpha,)
    center = (radius, radius)
    if num_sides == 0:
        pygame.draw.circle(sprite, border_color_rgba, center, radius)
        pygame.draw.circle(sprite, fill_color, center, max(1, radius - 3))
    else:
        outer_r = float(radius - 1)
        inner_r = outer_r * 0.5
        num_points = num_sides * 2 if is_star else num_sides
        step_deg = 360.0 / num_points
        start_deg = rng.uniform(0.0, 360.0)
        points = []
        for i in range(num_points):
            angle_deg = start_deg + step_deg * i
            angle_rad = math.radians(angle_deg)
            point_r = (inner_r if i % 2 else outer_r) if is_star else outer_r
            px = center[0] + math.cos(angle_rad) * point_r
            py = center[1] + math.sin(angle_rad) * point_r
            points.append((int(round(px)), int(round(py))))
        pygame.draw.polygon(sprite, fill_color, points)
        pygame.draw.polygon(sprite, border_color_rgba, points, width=3)
    return radius, sprite


@dataclass
class AnimatedShapeSprite:
    radius: int
    sprite: Surface
    x: float
    y: float
    dx: float
    dy: float


class AnimatedShapeField:
    """Generalized animated geometric sprite field for backgrounds/effects."""
    def __init__(
        self,
        *,
        total_shapes: int = 48,
        shape_defs: Sequence[Tuple[int, bool]] = ((0, False),),
        color_palette: Sequence[Tuple[int, int, int]] = ((220, 60, 60),),
        border_color: Tuple[int, int, int] = (0, 0, 0),
        radius_range: Tuple[int, int] = (12, 38),
        alpha_range: Tuple[int, int] = (150, 230),
        speed_base: float = 2.8,
        speed_variance: float = 1.8,
        seed: Optional[int] = None,
    ) -> None:
        self._rng = random.Random(seed)
        self._total_shapes = max(0, int(total_shapes))
        self._shape_defs = shape_defs
        self._color_palette = color_palette
        self._border_color = border_color
        self._radius_range = radius_range
        self._alpha_range = alpha_range
        self._speed_base = speed_base
        self._speed_variance = speed_variance
        self._shapes: list[AnimatedShapeSprite] = []
        self._create_shapes()

    def _create_shapes(self) -> None:
        num_types = len(self._shape_defs)
        if num_types == 0:
            return
        base, remainder = divmod(self._total_shapes, num_types)
        for i, shape_def in enumerate(self._shape_defs):
            count = base + (1 if i < remainder else 0)
            for _ in range(count):
                radius, sprite = random_shape_sprite(
                    self._rng,
                    self._radius_range,
                    self._color_palette,
                    self._alpha_range,
                    self._border_color,
                    shape_def,
                )
                dx, dy = self._random_velocity()
                self._shapes.append(AnimatedShapeSprite(
                    radius=radius,
                    sprite=sprite,
                    x=0.0,
                    y=0.0,
                    dx=dx,
                    dy=dy,
                ))

    def _random_velocity(self) -> Tuple[float, float]:
        speed = self._speed_base + self._rng.uniform(0.0, self._speed_variance)
        angle = self._rng.uniform(0.0, math.tau)
        dx = math.cos(angle) * speed
        dy = math.sin(angle) * speed
        return dx, dy

    def randomize_positions(self, width: int, height: int) -> None:
        for shape in self._shapes:
            min_x = shape.radius
            max_x = max(min_x, int(width) - shape.radius)
            min_y = shape.radius
            max_y = max(min_y, int(height) - shape.radius)
            shape.x = float(self._rng.randint(min_x, max_x))
            shape.y = float(self._rng.randint(min_y, max_y))

    def update(self, width: int, height: int) -> None:
        for shape in self._shapes:
            shape.x += shape.dx
            shape.y += shape.dy
            if shape.x - shape.radius <= 0:
                shape.x = float(shape.radius)
                shape.dx = abs(shape.dx)
            elif shape.x + shape.radius >= width:
                shape.x = float(width - shape.radius)
                shape.dx = -abs(shape.dx)
            if shape.y - shape.radius <= 0:
                shape.y = float(shape.radius)
                shape.dy = abs(shape.dy)
            elif shape.y + shape.radius >= height:
                shape.y = float(height - shape.radius)
                shape.dy = -abs(shape.dy)

    def draw(self, surface: Surface) -> None:
        for shape in self._shapes:
            left = int(round(shape.x - shape.radius))
            top = int(round(shape.y - shape.radius))
            surface.blit(shape.sprite, (left, top))

    @property
    def shapes(self) -> Sequence[AnimatedShapeSprite]:
        return self._shapes
