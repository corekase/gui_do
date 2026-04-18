from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from pygame.surface import Surface


@dataclass(frozen=True)
class CursorAsset:
    name: str
    image: Surface
    hotspot: Tuple[int, int]
    source_path: str
