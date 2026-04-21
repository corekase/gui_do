from __future__ import annotations

from pygame import Rect
from typing import Any, Tuple


def validate_point(point: Tuple[int, int], label: str = 'point') -> Tuple[int, int]:
    """Validate and normalize a point tuple of two ints."""
    if not isinstance(point, tuple) or len(point) != 2:
        raise ValueError(f'{label} must be a tuple of (x, y), got: {point}')
    x, y = point
    if not isinstance(x, int) or not isinstance(y, int):
        raise ValueError(f'{label} values must be ints, got: {point}')
    return (x, y)


def clamp_point_to_rect(point: Tuple[int, int], rect: Rect) -> Tuple[int, int]:
    """Clamp point to rect inclusive bounds [left, right-1] x [top, bottom-1]."""
    x, y = validate_point(point)
    if not isinstance(rect, Rect):
        raise ValueError(f'rect must be a Rect, got: {rect}')
    max_x = rect.right - 1
    max_y = rect.bottom - 1
    if x < rect.left:
        x = rect.left
    elif x > max_x:
        x = max_x
    if y < rect.top:
        y = rect.top
    elif y > max_y:
        y = max_y
    return (x, y)


def point_in_rect(point: Tuple[int, int], rect: Rect) -> bool:
    """Return whether a validated point is inside rect using pygame collide semantics."""
    x, y = validate_point(point)
    if not isinstance(rect, Rect):
        raise ValueError(f'rect must be a Rect, got: {rect}')
    return bool(rect.collidepoint((x, y)))


def _window_origin(window: Any) -> Tuple[int, int]:
    """Return normalized (x, y) origin for window-like containers."""
    try:
        wx = window.x
        wy = window.y
    except AttributeError as exc:
        raise ValueError(f'window must provide integer x and y, got: {window}') from exc
    if not isinstance(wx, int) or not isinstance(wy, int):
        raise ValueError(f'window must provide integer x and y, got: {window}')
    return (wx, wy)


def to_screen(point: Tuple[int, int], window: Any) -> Tuple[int, int]:
    """Convert container-local point into screen coordinates."""
    x, y = validate_point(point)
    wx, wy = _window_origin(window)
    return (x + wx, y + wy)


def to_window(point: Tuple[int, int], window: Any) -> Tuple[int, int]:
    """Convert screen point into container-local coordinates."""
    x, y = validate_point(point)
    wx, wy = _window_origin(window)
    return (x - wx, y - wy)
