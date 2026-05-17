"""Per-shape runtime state for the bouncing shapes demo feature."""

from __future__ import annotations

from dataclasses import dataclass

import pygame


@dataclass
class ShapeSpriteState:
    """Per-shape cached sprite with runtime position and velocity."""

    radius: int
    sprite: pygame.Surface
    center_x: float
    center_y: float
    velocity_x: float
    velocity_y: float


__all__ = ["ShapeSpriteState"]
