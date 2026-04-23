"""Animated circle backdrop feature for the gui_do demo screen."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Optional

import pygame

from shared.part_lifecycle import Part


@dataclass
class CircleSpriteState:
    """Per-circle cached sprite with runtime position and velocity."""

    radius: int
    sprite: pygame.Surface
    x: float
    y: float
    dx: float
    dy: float


class BouncingCirclesBackdropFeature(Part):
    """Render and animate cached random circles as a moving screen backdrop."""

    def __init__(self, *, circle_count: int = 28, seed: Optional[int] = None) -> None:
        super().__init__("bouncing_circles_backdrop")
        self.circle_count = max(1, int(circle_count))
        self._rng = random.Random(seed)
        self._circles: list[CircleSpriteState] = []
        self._scene_name = "main"
        self._host = None
        self._base_pristine: Optional[pygame.Surface] = None
        self._composed_pristine: Optional[pygame.Surface] = None
        self._lifecycle_dispose = None
        self._create_circles()

    def bind_runtime(self, demo) -> None:
        """Install composed screen lifecycle callbacks for circle rendering/motion."""
        if self._lifecycle_dispose is not None:
            return
        self._host = demo
        app = demo.app
        width, height = demo.screen_rect.size
        self._base_pristine = pygame.Surface((width, height)).convert()
        restored = app.restore_pristine(scene_name=self._scene_name, surface=self._base_pristine)
        if not restored:
            self._base_pristine.fill(app.theme.background)
        self._composed_pristine = self._base_pristine.copy()
        self._randomize_positions(width, height)

        self._lifecycle_dispose = app.chain_screen_lifecycle(
            preamble=self.screen_preamble,
            postamble=self.screen_postamble,
        )

    def on_unregister(self, host) -> None:
        """Detach lifecycle composition hooks when the part is unregistered."""
        if self._lifecycle_dispose is None:
            return
        self._lifecycle_dispose()
        self._lifecycle_dispose = None

    def screen_preamble(self) -> None:
        """Compose the current backdrop frame by drawing cached circle sprites."""
        if self._host is None or self._base_pristine is None or self._composed_pristine is None:
            return
        self._composed_pristine.blit(self._base_pristine, (0, 0))
        for circle in self._circles:
            left = int(round(circle.x - circle.radius))
            top = int(round(circle.y - circle.radius))
            self._composed_pristine.blit(circle.sprite, (left, top))
        self._host.app.set_pristine(self._composed_pristine, scene_name=self._scene_name)

    def screen_postamble(self) -> None:
        """Advance circle positions and bounce off the screen boundaries."""
        if self._host is None:
            return
        width = int(self._host.screen_rect.width)
        height = int(self._host.screen_rect.height)
        for circle in self._circles:
            circle.x += circle.dx
            circle.y += circle.dy

            if circle.x - circle.radius <= 0:
                circle.x = float(circle.radius)
                circle.dx = abs(circle.dx)
            elif circle.x + circle.radius >= width:
                circle.x = float(width - circle.radius)
                circle.dx = -abs(circle.dx)

            if circle.y - circle.radius <= 0:
                circle.y = float(circle.radius)
                circle.dy = abs(circle.dy)
            elif circle.y + circle.radius >= height:
                circle.y = float(height - circle.radius)
                circle.dy = -abs(circle.dy)

    def _create_circles(self) -> None:
        """Create cached sprite + motion state for each circle once at init time."""
        for _ in range(self.circle_count):
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

            speed = self._rng.uniform(1.2, 2.9)
            angle = self._rng.uniform(0.0, math.tau)
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed

            self._circles.append(
                CircleSpriteState(
                    radius=radius,
                    sprite=sprite,
                    x=0.0,
                    y=0.0,
                    dx=dx,
                    dy=dy,
                )
            )

    def _randomize_positions(self, width: int, height: int) -> None:
        """Initialize random on-screen starting positions using current host size."""
        for circle in self._circles:
            min_x = circle.radius
            max_x = max(min_x, int(width) - circle.radius)
            min_y = circle.radius
            max_y = max(min_y, int(height) - circle.radius)
            circle.x = float(self._rng.randint(min_x, max_x))
            circle.y = float(self._rng.randint(min_y, max_y))
