"""Per-shape runtime state for the bouncing shapes demo feature."""

from __future__ import annotations

from dataclasses import dataclass

import pygame


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


__all__ = ["ShapeSpriteState"]
