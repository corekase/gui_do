from __future__ import annotations

from typing import Tuple, Union

from pygame import Rect

from .rect_source import RectSource, resolve_rect


Geometry = Union[Rect, Tuple[int, int]]


class AnchorLayout:
    """Anchor-only layout helper used by application/runtime window placement."""

    def __init__(self) -> None:
        self._anchor_bounds = Rect(0, 0, 1, 1)

    def set_anchor_bounds(self, bounds: RectSource) -> None:
        self._anchor_bounds = resolve_rect(bounds)

    def anchored(
        self,
        size: Tuple[int, int],
        anchor: str = "center",
        margin: Tuple[int, int] = (0, 0),
        use_rect: bool = True,
    ) -> Geometry:
        width, height = int(size[0]), int(size[1])
        rect = Rect(0, 0, width, height)
        bounds = self._anchor_bounds
        dx, dy = int(margin[0]), int(margin[1])
        if anchor == "top_left":
            rect.topleft = (bounds.left + dx, bounds.top + dy)
        elif anchor == "top_center":
            rect.midtop = (bounds.centerx + dx, bounds.top + dy)
        elif anchor == "top_right":
            rect.topright = (bounds.right - dx, bounds.top + dy)
        elif anchor == "center_left":
            rect.midleft = (bounds.left + dx, bounds.centery + dy)
        elif anchor == "center_right":
            rect.midright = (bounds.right - dx, bounds.centery + dy)
        elif anchor == "bottom_left":
            rect.bottomleft = (bounds.left + dx, bounds.bottom - dy)
        elif anchor == "bottom_center":
            rect.midbottom = (bounds.centerx + dx, bounds.bottom - dy)
        elif anchor == "bottom_right":
            rect.bottomright = (bounds.right - dx, bounds.bottom - dy)
        else:
            rect.center = bounds.center
            rect.x += dx
            rect.y += dy
        if use_rect:
            return rect
        return rect.topleft
