from dataclasses import dataclass

from pygame import Rect
from pygame.surface import Surface


@dataclass(frozen=True)
class InteractiveVisuals:
    idle: Surface
    hover: Surface
    armed: Surface
    hit_rect: Rect
