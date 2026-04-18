from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from pygame.surface import Surface


@dataclass(frozen=True)
class CursorAsset:
    """Immutable cursor registration payload.

    Attributes:
        name: Logical cursor identifier.
        image: Cursor surface loaded from project resources.
        hotspot: Cursor hotspot offset relative to image origin.
        source_path: Original source path used to load the asset.
    """

    name: str
    image: Surface
    hotspot: Tuple[int, int]
    source_path: str
