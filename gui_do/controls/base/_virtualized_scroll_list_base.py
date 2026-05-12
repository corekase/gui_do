from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from .ui_node import UiNode

if TYPE_CHECKING:
    from pygame import Rect


class _VirtualizedScrollListBase(UiNode):
    """Shared scroll state and geometry helpers for virtualized list-like controls."""

    def __init__(self, control_id: str, rect) -> None:
        super().__init__(control_id, rect)
        self._scroll_offset: int = 0
        self._scrollbar_dragging: bool = False
        self._scrollbar_drag_anchor: int = 0

    # ------------------------------------------------------------------
    # Abstract helpers (override in subclasses)
    # ------------------------------------------------------------------

    def _content_height(self) -> int:
        """Total scrollable content height in pixels."""
        return 0

    def _viewport_height(self) -> int:
        """Visible viewport height in pixels."""
        return max(1, self.rect.height)

    # ------------------------------------------------------------------
    # Shared scroll geometry
    # ------------------------------------------------------------------

    def _max_scroll(self) -> int:
        return max(0, self._content_height() - self._viewport_height())

    def _clamp_scroll(self) -> None:
        self._scroll_offset = max(0, min(self._scroll_offset, self._max_scroll()))

    def _set_scroll_from_handle_top(self, top: int) -> None:
        sb_rect = self._scrollbar_rect()
        handle_rect = self._scrollbar_handle_rect()
        if sb_rect is None or handle_rect is None:
            return
        travel = max(1, sb_rect.height - handle_rect.height)
        ratio = (int(top) - sb_rect.y) / float(travel)
        ratio = min(max(ratio, 0.0), 1.0)
        self._scroll_offset = int(round(ratio * self._max_scroll()))
        self._clamp_scroll()
        self.invalidate()

    def _scrollbar_rect(self) -> Optional["Rect"]:
        """Return scrollbar track rect, or None if scrollbar is not shown."""
        return None

    def _scrollbar_handle_rect(self) -> Optional["Rect"]:
        """Return scrollbar thumb rect, or None if scrollbar is not shown."""
        return None
