from __future__ import annotations

from dataclasses import dataclass

from pygame import Rect
from pygame.surface import Surface


@dataclass(frozen=True)
class InteractiveVisuals:
    """Pre-rendered bitmaps and hit geometry for interactive controls."""

    idle: Surface
    hover: Surface
    armed: Surface
    hit_rect: Rect
