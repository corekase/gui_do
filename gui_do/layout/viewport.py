"""Viewport — shared scroll/zoom state for all scrollable and zoomable surfaces.

A :class:`Viewport` encapsulates scroll offset, zoom level, and the coordinate
transforms between screen space and node-local space.  Scroll containers,
:class:`~gui_do.CanvasControl`, :class:`~gui_do.DataGridControl`, and similar
controls all share this abstraction so that features like animated scrolling,
snap-to-item, minimap projection, and rubber-band zoom compose without
per-control reimplementation.

Usage::

    from gui_do import Viewport

    vp = Viewport(content_size=(2000, 1500), viewport_size=(800, 600))

    # Scroll:
    vp.scroll_to(0, 200)
    vp.scroll_by(0, 50)
    vp.clamp()

    # Zoom (anchor at screen center):
    vp.set_zoom(2.0, anchor=(400, 300))

    # Coordinate transforms:
    local_pt  = vp.screen_to_local((mx, my))
    screen_pt = vp.local_to_screen((lx, ly))

    # What portion of content is visible?
    vis = vp.visible_rect()   # pygame.Rect in content coordinates

    # React to changes:
    vp.subscribe(lambda: my_control.invalidate())
"""
from __future__ import annotations

import math
from typing import Callable, Optional

from pygame import Rect


class Viewport:
    """Observable scroll-and-zoom state for scrollable/zoomable surfaces.

    Parameters
    ----------
    content_size:
        Total size of the scrollable content in pixels (width, height).
    viewport_size:
        Visible viewport size in pixels (width, height).
    zoom:
        Initial zoom factor (1.0 = no zoom).
    min_zoom / max_zoom:
        Zoom bounds (clamped on set).
    """

    def __init__(
        self,
        content_size: Tuple[int, int] = (0, 0),
        viewport_size: Tuple[int, int] = (0, 0),
        *,
        zoom: float = 1.0,
        min_zoom: float = 0.1,
        max_zoom: float = 32.0,
    ) -> None:
        self._content_w, self._content_h = max(0, content_size[0]), max(0, content_size[1])
        self._vp_w, self._vp_h = max(0, viewport_size[0]), max(0, viewport_size[1])
        self._zoom = float(zoom)
        self._min_zoom = float(min_zoom)
        self._max_zoom = float(max_zoom)
        self._scroll_x: float = 0.0
        self._scroll_y: float = 0.0
        self._subscribers: List[Callable[[], None]] = []

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def scroll_x(self) -> float:
        return self._scroll_x

    @property
    def scroll_y(self) -> float:
        return self._scroll_y

    @property
    def scroll_offset(self) -> Tuple[float, float]:
        """Current scroll offset as ``(x, y)``."""
        return (self._scroll_x, self._scroll_y)

    @property
    def zoom(self) -> float:
        return self._zoom

    @property
    def content_size(self) -> Tuple[int, int]:
        return (self._content_w, self._content_h)

    @property
    def viewport_size(self) -> Tuple[int, int]:
        return (self._vp_w, self._vp_h)

    # ------------------------------------------------------------------
    # Scrolling
    # ------------------------------------------------------------------

    def scroll_to(self, x: float, y: float) -> None:
        """Scroll to absolute content position *(x, y)*."""
        prev = (self._scroll_x, self._scroll_y)
        self._scroll_x = float(x)
        self._scroll_y = float(y)
        self.clamp()
        if (self._scroll_x, self._scroll_y) != prev:
            self._notify()

    def scroll_by(self, dx: float, dy: float) -> None:
        """Scroll by *(dx, dy)* relative to the current offset."""
        self.scroll_to(self._scroll_x + dx, self._scroll_y + dy)

    def scroll_to_item(self, item_rect: Rect, *, padding: int = 4) -> None:
        """Scroll the minimum amount to make *item_rect* (in content coords) fully visible."""
        vl = self._scroll_x
        vr = vl + self._vp_w / self._zoom
        vt = self._scroll_y
        vb = vt + self._vp_h / self._zoom

        new_x = self._scroll_x
        new_y = self._scroll_y

        if item_rect.left - padding < vl:
            new_x = item_rect.left - padding
        elif item_rect.right + padding > vr:
            new_x = item_rect.right + padding - self._vp_w / self._zoom

        if item_rect.top - padding < vt:
            new_y = item_rect.top - padding
        elif item_rect.bottom + padding > vb:
            new_y = item_rect.bottom + padding - self._vp_h / self._zoom

        self.scroll_to(new_x, new_y)

    def clamp(self) -> None:
        """Clamp scroll offset so the viewport does not exceed content bounds."""
        scaled_vp_w = self._vp_w / max(self._zoom, 1e-9)
        scaled_vp_h = self._vp_h / max(self._zoom, 1e-9)
        max_x = max(0.0, self._content_w - scaled_vp_w)
        max_y = max(0.0, self._content_h - scaled_vp_h)
        self._scroll_x = max(0.0, min(self._scroll_x, max_x))
        self._scroll_y = max(0.0, min(self._scroll_y, max_y))

    # ------------------------------------------------------------------
    # Zooming
    # ------------------------------------------------------------------

    def set_zoom(self, zoom: float, *, anchor: Optional[Tuple[float, float]] = None) -> None:
        """Set zoom level, optionally anchoring to a screen-space point.

        When *anchor* is given the content point under the anchor stays
        fixed in screen space after the zoom change.
        """
        new_zoom = max(self._min_zoom, min(self._max_zoom, float(zoom)))
        if math.isclose(new_zoom, self._zoom, rel_tol=1e-9):
            return
        if anchor is not None:
            ax, ay = anchor
            # Content point under anchor before zoom change:
            cx = self._scroll_x + ax / self._zoom
            cy = self._scroll_y + ay / self._zoom
            self._zoom = new_zoom
            # Adjust scroll so the same content point stays under anchor:
            self._scroll_x = cx - ax / self._zoom
            self._scroll_y = cy - ay / self._zoom
        else:
            self._zoom = new_zoom
        self.clamp()
        self._notify()

    def adjust_zoom(self, factor: float, *, anchor: Optional[Tuple[float, float]] = None) -> None:
        """Multiply current zoom by *factor*."""
        self.set_zoom(self._zoom * factor, anchor=anchor)

    # ------------------------------------------------------------------
    # Sizing
    # ------------------------------------------------------------------

    def set_content_size(self, width: int, height: int) -> None:
        """Update the total content size (e.g. after dataset changes)."""
        changed = (self._content_w, self._content_h) != (width, height)
        self._content_w = max(0, int(width))
        self._content_h = max(0, int(height))
        self.clamp()
        if changed:
            self._notify()

    def set_viewport_size(self, width: int, height: int) -> None:
        """Update the viewport size (e.g. after control resize)."""
        changed = (self._vp_w, self._vp_h) != (width, height)
        self._vp_w = max(0, int(width))
        self._vp_h = max(0, int(height))
        self.clamp()
        if changed:
            self._notify()

    # ------------------------------------------------------------------
    # Coordinate transforms
    # ------------------------------------------------------------------

    def screen_to_local(self, screen_pt: Tuple[float, float]) -> Tuple[float, float]:
        """Convert a screen-space point to content-local coordinates."""
        sx, sy = screen_pt
        lx = self._scroll_x + sx / self._zoom
        ly = self._scroll_y + sy / self._zoom
        return (lx, ly)

    def local_to_screen(self, local_pt: Tuple[float, float]) -> Tuple[float, float]:
        """Convert a content-local point to screen-space coordinates."""
        lx, ly = local_pt
        sx = (lx - self._scroll_x) * self._zoom
        sy = (ly - self._scroll_y) * self._zoom
        return (sx, sy)

    def visible_rect(self) -> Rect:
        """Return the visible region in content coordinates as a ``pygame.Rect``."""
        w = int(math.ceil(self._vp_w / max(self._zoom, 1e-9)))
        h = int(math.ceil(self._vp_h / max(self._zoom, 1e-9)))
        return Rect(int(self._scroll_x), int(self._scroll_y), w, h)

    # ------------------------------------------------------------------
    # Reactive subscriptions
    # ------------------------------------------------------------------

    def subscribe(self, callback: Callable[[], None]) -> Callable[[], None]:
        """Subscribe *callback* to viewport changes.  Returns an unsub callable."""
        self._subscribers.append(callback)

        def _unsub() -> None:
            try:
                self._subscribers.remove(callback)
            except ValueError:
                pass

        return _unsub

    def _notify(self) -> None:
        subscribers = self._subscribers
        i = 0
        while i < len(subscribers):
            cb = subscribers[i]
            cb()
            if i < len(subscribers) and subscribers[i] is cb:
                i += 1
