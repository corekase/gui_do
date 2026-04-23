from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple, Union

from pygame import Rect


Geometry = Union[Rect, Tuple[int, int]]


@dataclass
class _LinearConfig:
    anchor: Tuple[int, int] = (0, 0)
    width: int = 100
    height: int = 40
    spacing: int = 8
    horizontal: bool = True
    wrap_count: int = 0
    use_rect: bool = True


class LayoutManager:
    """Grid, linear, and anchor layout helpers for controls."""

    def __init__(self) -> None:
        self._linear = _LinearConfig()
        self._linear_cursor = 0
        self._anchor_bounds = Rect(0, 0, 1, 1)

    def set_linear_properties(
        self,
        anchor: Tuple[int, int],
        item_width: int,
        item_height: int,
        spacing: int,
        horizontal: bool = True,
        wrap_count: int = 0,
        use_rect: bool = True,
    ) -> None:
        self._linear = _LinearConfig(anchor, int(item_width), int(item_height), int(spacing), bool(horizontal), int(wrap_count), bool(use_rect))
        self._linear_cursor = 0

    def linear(self, index: int) -> Geometry:
        x = int(index)
        y = 0
        if self._linear.wrap_count > 0:
            y = x // self._linear.wrap_count
            x = x % self._linear.wrap_count
        if not self._linear.horizontal:
            x, y = y, x
        px = self._linear.anchor[0] + (x * (self._linear.width + self._linear.spacing))
        py = self._linear.anchor[1] + (y * (self._linear.height + self._linear.spacing))
        if self._linear.use_rect:
            return Rect(px, py, self._linear.width, self._linear.height)
        return (px, py)

    def next_linear(self) -> Geometry:
        geo = self.linear(self._linear_cursor)
        self._linear_cursor += 1
        return geo

    def set_anchor_bounds(self, bounds: Rect) -> None:
        self._anchor_bounds = Rect(bounds)

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
