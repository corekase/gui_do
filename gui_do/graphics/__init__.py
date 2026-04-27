from pathlib import Path
import pygame
from ..core.error_handling import io_error, logical_error

from .built_in_definitions import BUILT_IN_COLOURS
from .built_in_factory import InteractiveVisuals, BuiltInGraphicsFactory, WindowChromeVisuals


def _convert_if_available(surface: pygame.Surface) -> pygame.Surface:
    """Return a display-formatted surface when possible, otherwise a safe copy.

    In headless/unit-test contexts pygame may not have a display format set, and
    `Surface.convert()` raises `pygame.error`. In that case we preserve behavior
    by returning a plain copy.
    """
    try:
        return surface.convert()
    except pygame.error:
        return surface.copy()


def load_pristine_surface(source):
    """Load a background-pristine surface from a Surface, path string, or None.

    Accepted *source* values:
    - ``None``   → returns ``None`` (no pristine background)
    - ``pygame.Surface`` → returned as-is after ``convert()``
    - ``str`` or ``Path`` → resolved relative to the application CWD when not absolute
    """
    if source is None:
        return None
    if isinstance(source, pygame.Surface):
        return _convert_if_available(source)
    if isinstance(source, (str, Path)):
        candidate = Path(source)
        if not candidate.is_absolute():
            candidate = Path.cwd() / candidate
        try:
            return _convert_if_available(pygame.image.load(str(candidate)))
        except Exception as exc:
            raise io_error(
                "failed to load pristine surface",
                subsystem="gui.graphics",
                operation="load_pristine_surface",
                cause=exc,
                path=str(candidate),
                exc_type=ValueError,
                details={"source": str(source)},
                source_skip_frames=1,
            ) from exc
    raise logical_error(
        "pristine source must be a Surface or path-like string",
        subsystem="gui.graphics",
        operation="load_pristine_surface",
        exc_type=TypeError,
        details={"source_type": type(source).__name__},
        source_skip_frames=1,
    )


__all__ = [
    "BUILT_IN_COLOURS",
    "InteractiveVisuals",
    "BuiltInGraphicsFactory",
    "WindowChromeVisuals",
    "load_pristine_surface",
]
