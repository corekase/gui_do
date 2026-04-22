from pathlib import Path
import pygame

from .built_in_definitions import BUILT_IN_COLOURS
from .built_in_factory import InteractiveVisuals, BuiltInGraphicsFactory, WindowChromeVisuals


def load_pristine_surface(source):
    """Load a background-pristine surface from a Surface, path string, or None.

    Accepted *source* values:
    - ``None``   → returns ``None`` (no pristine background)
    - ``pygame.Surface`` → returned as-is after ``convert()``
    - ``str`` or ``Path`` → resolved relative to the repo ``data/images/`` directory
    """
    if source is None:
        return None
    if isinstance(source, pygame.Surface):
        return source.convert()
    if isinstance(source, (str, Path)):
        candidate = Path(source)
        if not candidate.is_absolute():
            root = Path(__file__).resolve().parents[2]
            candidate = root / "data" / "images" / str(source)
        return pygame.image.load(str(candidate)).convert()
    raise TypeError("pristine source must be a Surface or path-like string")


__all__ = [
    "BUILT_IN_COLOURS",
    "InteractiveVisuals",
    "BuiltInGraphicsFactory",
    "WindowChromeVisuals",
    "load_pristine_surface",
]
