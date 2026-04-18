from dataclasses import dataclass
from typing import Tuple

from pygame import Rect


@dataclass(frozen=True)
class CursorPlacement:
    """Value object for cursor anchor, hotspot, and resulting rect."""

    anchor: Tuple[int, int]
    hotspot: Tuple[int, int]
    size: Tuple[int, int]

    def build_rect(self) -> Rect:
        return Rect(
            self.anchor[0] - self.hotspot[0],
            self.anchor[1] - self.hotspot[1],
            self.size[0],
            self.size[1],
        )
