from __future__ import annotations

from pygame import Rect


class InvalidationTracker:
    """Tracks dirty regions and exposes a conservative full-redraw fallback."""

    def __init__(self) -> None:
        self._full_redraw = True
        self._dirty_regions: list[Rect] = []

    def invalidate_all(self) -> None:
        self._full_redraw = True
        self._dirty_regions.clear()

    def invalidate_rect(self, rect: Rect) -> None:
        if self._full_redraw:
            return
        self._dirty_regions.append(Rect(rect))

    def begin_frame(self) -> tuple[bool, list[Rect]]:
        if self._full_redraw:
            return True, []
        return False, [Rect(r) for r in self._dirty_regions]

    def end_frame(self) -> None:
        self._full_redraw = False
        self._dirty_regions.clear()
