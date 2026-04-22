from __future__ import annotations

from typing import List, Optional

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

    @property
    def is_dirty(self) -> bool:
        """Return True when a full redraw is pending or any dirty rects are tracked."""
        return self._full_redraw or bool(self._dirty_regions)

    @property
    def dirty_region_count(self) -> int:
        """Return the number of pending dirty rects.

        Returns 0 when a full-redraw flag is set (no individual regions tracked)
        or when nothing has been invalidated.
        """
        return len(self._dirty_regions)

    def merge_dirty_regions(self) -> Optional[Rect]:
        """Return the union bounding rect of all pending dirty regions, or ``None``
        when the tracker is clean. When a full-redraw is pending the result is also
        ``None`` since the caller should redraw everything."""
        if self._full_redraw or not self._dirty_regions:
            return None
        merged = self._dirty_regions[0].copy()
        for region in self._dirty_regions[1:]:
            merged = merged.union(region)
        return merged

    def begin_frame(self) -> tuple[bool, list[Rect]]:
        if self._full_redraw:
            return True, []
        return False, [Rect(r) for r in self._dirty_regions]

    def end_frame(self) -> None:
        self._full_redraw = False
        self._dirty_regions.clear()
