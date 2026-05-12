from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter


class FrameTimer:
    """Tracks per-frame delta time for use inside on_update."""

    def __init__(self) -> None:
        self._last: float = 0.0

    def tick(self) -> float:
        """Return seconds elapsed since the previous call, or 0.0 on first call."""
        now = perf_counter()
        if self._last == 0.0:
            self._last = now
            return 0.0
        dt = now - self._last
        self._last = now
        return dt

    def reset(self) -> None:
        """Reset internal clock so the next tick returns 0.0."""
        self._last = 0.0


@dataclass(slots=True)
class PlacedControl:
    """Generic placed-control record for tracking layout placement."""

    control: object
    label: object | None
    name: str
    column_index: int
    row_index: int
