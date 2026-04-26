from __future__ import annotations


class InvalidationTracker:
    """Tracks dirty regions and exposes a conservative full-redraw fallback."""

    def __init__(self) -> None:
        self._full_redraw = True

    def invalidate_all(self) -> None:
        self._full_redraw = True

    def begin_frame(self) -> tuple[bool, list]:
        return self._full_redraw, []

    def end_frame(self) -> None:
        self._full_redraw = False
