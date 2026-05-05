"""DirtyRegionTracker — per-frame dirty-rect accumulation and render gating.

Controls call :meth:`DirtyRegionTracker.mark_dirty` whenever their visual
state changes.  The render loop calls :meth:`consume_dirty_regions` once per
frame to obtain the minimal set of rects that need repainting, then skips
``draw()`` for any control whose ``rect`` does not intersect the dirty union.

Usage::

    from gui_do import DirtyRegionTracker

    tracker = DirtyRegionTracker()

    # Wire into UiNode — set node._invalidation_tracker = tracker in scene mount.
    # Controls call:  self._invalidation_tracker.mark_dirty(self.rect)

    # In render loop:
    dirty = tracker.consume_dirty_regions()   # list of pygame.Rect
    # blit/draw only controls that overlap dirty union

    # Mark a single full-screen refresh (e.g. after scene switch):
    tracker.mark_all_dirty(screen_rect)

    # Query without consuming:
    if tracker.has_dirty:
        draw_frame()
"""
from __future__ import annotations

from typing import List, Optional

from pygame import Rect


class DirtyRegionTracker:
    """Accumulates per-frame dirty rects and supplies a consumable dirty list.

    Thread model: all calls must come from the main (render) thread.
    """

    def __init__(self) -> None:
        self._dirty: List[Rect] = []
        self._dirty_union: Optional[Rect] = None
        self._full_dirty: bool = False
        self._full_dirty_rect: Optional[Rect] = None

    # ------------------------------------------------------------------
    # Marking
    # ------------------------------------------------------------------

    def mark_dirty(self, rect: Rect) -> None:
        """Accumulate *rect* as needing a redraw this frame."""
        if self._full_dirty:
            return  # already a full-screen dirty — no point accumulating
        if rect.width > 0 and rect.height > 0:
            r = Rect(rect)
            self._dirty.append(r)
            if self._dirty_union is None:
                self._dirty_union = Rect(r)
            else:
                self._dirty_union.union_ip(r)

    def mark_all_dirty(self, screen_rect: Rect) -> None:
        """Mark the entire *screen_rect* as dirty (e.g. after scene switch)."""
        self._full_dirty = True
        self._full_dirty_rect = Rect(screen_rect)
        self._dirty.clear()
        self._dirty_union = None

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    @property
    def has_dirty(self) -> bool:
        """True if any region was marked dirty since the last consume."""
        return self._full_dirty or bool(self._dirty)

    # ------------------------------------------------------------------
    # Consuming
    # ------------------------------------------------------------------

    def consume_dirty_regions(self) -> List[Rect]:
        """Return accumulated dirty rects and reset for the next frame.

        If :meth:`mark_all_dirty` was called the list contains the single
        full-screen rect.  Otherwise it contains all accumulated per-rect
        marks.  The caller may union them for a single blit or iterate
        individually.
        """
        if self._full_dirty:
            rects = [self._full_dirty_rect] if self._full_dirty_rect else []
            self._full_dirty = False
            self._full_dirty_rect = None
            return rects
        result = self._dirty
        self._dirty = []
        self._dirty_union = None
        return result

    def dirty_union(self) -> Optional[Rect]:
        """Return the union of all pending dirty rects without consuming them.

        Returns ``None`` when nothing is dirty.
        """
        if not self.has_dirty:
            return None
        if self._full_dirty:
            return self._full_dirty_rect
        if not self._dirty:
            return None
        union = Rect(self._dirty[0])
        for r in self._dirty[1:]:
            union.union_ip(r)
        return union

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def rects_union(rects: List[Rect]) -> Optional[Rect]:
        """Union a list of rects. Returns None for empty list."""
        if not rects:
            return None
        result = Rect(rects[0])
        for r in rects[1:]:
            result.union_ip(r)
        return result

    def overlaps_dirty(self, rect: Rect) -> bool:
        """Return True if *rect* intersects any current dirty region.

        Uses a cached union of all dirty rects for O(1) overlap testing
        instead of iterating every individual dirty rect.
        """
        if not self.has_dirty:
            return False
        if self._full_dirty:
            return True
        return self._dirty_union is not None and self._dirty_union.colliderect(rect)
