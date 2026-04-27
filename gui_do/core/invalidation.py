from __future__ import annotations

from typing import List, Optional, Tuple


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
        from pygame import Rect as PygameRect
        r = PygameRect(rect)
        if self._screen_size is not None and r.width * r.height >= self._screen_size[0] * self._screen_size[1]:
            self._full_redraw = True
            self._dirty_rects.clear()
            return
        if not self._full_redraw:
            self._dirty_rects.append(r)

    def begin_frame(self) -> tuple:
        """Return (is_full_redraw, dirty_rects_snapshot)."""
        return self._full_redraw, list(self._dirty_rects)

    def end_frame(self) -> None:
        """Clear per-frame dirty state."""
        self._full_redraw = False
        self._dirty_rects.clear()

    def merge_dirty_rects(self) -> List:
        """Return a merged list of dirty rects (union overlapping pairs)."""
        if not self._dirty_rects:
            return []
        merged = list(self._dirty_rects)
        changed = True
        while changed:
            changed = False
            next_list: List = []
            skip: set = set()
            for i in range(len(merged)):
                if i in skip:
                    continue
                r1 = merged[i]
                merged_flag = False
                for j in range(i + 1, len(merged)):
                    if j in skip:
                        continue
                    r2 = merged[j]
                    if r1.colliderect(r2):
                        next_list.append(r1.union(r2))
                        skip.add(j)
                        merged_flag = True
                        changed = True
                        break
                if not merged_flag:
                    next_list.append(r1)
            merged = next_list
        return merged
