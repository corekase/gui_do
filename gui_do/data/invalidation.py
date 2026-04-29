from __future__ import annotations

from typing import List, Optional, Tuple

from pygame import Rect as PygameRect


class InvalidationTracker:
    """Tracks dirty regions and exposes a conservative full-redraw fallback."""

    def __init__(self) -> None:
        self._full_redraw = True
        self._dirty_rects: List = []
        self._screen_size: Optional[Tuple[int, int]] = None

    def set_screen_size(self, size: Tuple[int, int]) -> None:
        """Register screen dimensions for full-rect promotion check."""
        self._screen_size = (int(size[0]), int(size[1]))

    def invalidate_all(self) -> None:
        """Mark full frame as needing redraw."""
        self._full_redraw = True
        self._dirty_rects.clear()

    def invalidate_rect(self, rect) -> None:
        """Add a dirty region. Promotes to full_redraw when rect covers the screen."""
        r = PygameRect(rect)
        if self._screen_size is not None and r.width * r.height >= self._screen_size[0] * self._screen_size[1]:
            self._full_redraw = True
            self._dirty_rects.clear()
            return
        if not self._full_redraw:
            self._dirty_rects.append(r)

    def begin_frame(self) -> tuple:
        """Return (is_full_redraw, dirty_rects_snapshot)."""
        if self._full_redraw or not self._dirty_rects:
            return self._full_redraw, []
        return self._full_redraw, list(self._dirty_rects)

    def end_frame(self) -> None:
        """Clear per-frame dirty state."""
        self._full_redraw = False
        self._dirty_rects.clear()

    def merge_dirty_rects(self) -> List:
        """Return a merged list of dirty rects (union overlapping rects).

        Sorts by (y, x) then performs a single greedy sweep, unioning each
        rect with the last merged rect when they collide.  O(n log n) vs the
        prior O(n²) while-changed loop.
        """
        if not self._dirty_rects:
            return []
        rects = sorted(self._dirty_rects, key=lambda r: (r.y, r.x))
        merged: List = [rects[0].copy()]
        for r in rects[1:]:
            last = merged[-1]
            if last.colliderect(r):
                merged[-1] = last.union(r)
            else:
                merged.append(r.copy())
        return merged
