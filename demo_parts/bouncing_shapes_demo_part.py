"""Animated shape backdrop feature for the gui_do demo screen."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Optional

import pygame

from shared.part_lifecycle import ScreenPart


@dataclass
class ShapeSpriteState:
    """Per-shape cached sprite with runtime position and velocity."""

    kind: str
    radius: int
    sprite: pygame.Surface
    x: float
    y: float
    dx: float
    dy: float


class BouncingShapesBackdropFeature(ScreenPart):
    """Render and animate cached random circles/diamonds directly on screen."""

    HOST_REQUIREMENTS = {
        "bind_runtime": ("app", "screen_rect"),
    }

    def __init__(
        self,
        *,
        circle_count: int = 28,
        diamond_count: int = 0,
        seed: Optional[int] = None,
        scene_name: str = "main",
        part_name: str = "bouncing_shapes_backdrop",
    ) -> None:
        super().__init__(part_name, scene_name=scene_name)
        self.circle_count = max(0, int(circle_count))
        self.diamond_count = max(0, int(diamond_count))
        self._rng = random.Random(seed)
        self._shapes: list[ShapeSpriteState] = []
        self._scene_name = str(scene_name)
        self._host = None
        self._create_shapes()
        self._rng.shuffle(self._shapes)

    def bind_runtime(self, demo) -> None:
        """Bind host services and initialize random positions using screen bounds."""
        self._host = demo
        width, height = demo.screen_rect.size
        self._randomize_positions(width, height)

    def on_screen_update(self, host, dt_seconds: float) -> None:
        """Advance shape positions and bounce off active screen boundaries."""
        del dt_seconds
        if host is None or not hasattr(host, "screen_rect"):
            return
        width = int(host.screen_rect.width)
        height = int(host.screen_rect.height)
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

    def draw_screen(self, host, surface, theme) -> None:
        """Draw current shape sprites on the already-restored frame surface."""
        del host, theme
        for shape in self._shapes:
            left = int(round(shape.x - shape.radius))
            top = int(round(shape.y - shape.radius))
            surface.blit(shape.sprite, (left, top))

    def _create_shapes(self) -> None:
        """Create cached circle and diamond sprite/motion states at init time."""
        for _ in range(self.circle_count):
            self._shapes.append(self._create_circle_shape())
        for _ in range(self.diamond_count):
            self._shapes.append(self._create_diamond_shape())

    def _create_circle_shape(self) -> ShapeSpriteState:
        """Create one cached circular sprite with initial velocity."""
        radius = self._rng.randint(12, 38)
        diameter = radius * 2
        sprite = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        fill_color = (
            self._rng.randint(45, 245),
            self._rng.randint(45, 245),
            self._rng.randint(45, 245),
            190,
        )
        border_color = (15, 15, 15, 230)
        center = (radius, radius)
        pygame.draw.circle(sprite, border_color, center, radius)
        pygame.draw.circle(sprite, fill_color, center, max(1, radius - 2))
        dx, dy = self._random_velocity()

        return ShapeSpriteState(
            kind="circle",
            radius=radius,
            sprite=sprite,
            x=0.0,
            y=0.0,
            dx=dx,
            dy=dy,
        )

    def _create_diamond_shape(self) -> ShapeSpriteState:
        """Create one cached diamond sprite (45-degree square) with velocity."""
        radius = self._rng.randint(12, 38)
        diameter = radius * 2
        sprite = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        fill_color = (
            self._rng.randint(45, 245),
            self._rng.randint(45, 245),
            self._rng.randint(45, 245),
            190,
        )
        border_color = (15, 15, 15, 230)
        points = [
            (radius, 0),
            (diameter - 1, radius),
            (radius, diameter - 1),
            (0, radius),
        ]
        pygame.draw.polygon(sprite, fill_color, points)
        pygame.draw.polygon(sprite, border_color, points, width=2)
        dx, dy = self._random_velocity()

        return ShapeSpriteState(
            kind="diamond",
            radius=radius,
            sprite=sprite,
            x=0.0,
            y=0.0,
            dx=dx,
            dy=dy,
        )

    def _random_velocity(self) -> tuple[float, float]:
        """Create a random velocity vector with bounded speed."""
        speed = self._rng.uniform(1.2, 2.9)
        angle = self._rng.uniform(0.0, math.tau)
        dx = math.cos(angle) * speed
        dy = math.sin(angle) * speed
        return dx, dy

    def _randomize_positions(self, width: int, height: int) -> None:
        """Initialize random on-screen starting positions using current host size."""
        for shape in self._shapes:
            min_x = shape.radius
            max_x = max(min_x, int(width) - shape.radius)
            min_y = shape.radius
            max_y = max(min_y, int(height) - shape.radius)
            shape.x = float(self._rng.randint(min_x, max_x))
            shape.y = float(self._rng.randint(min_y, max_y))


# Backward-compatible alias for existing imports.
BouncingCirclesBackdropFeature = BouncingShapesBackdropFeature
