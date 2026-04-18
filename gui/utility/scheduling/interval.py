from __future__ import annotations

from typing import Callable, Optional


class Interval:
    """Mutable timer interval state tracked by `Timers`.

    Attributes:
        timer: Accumulated elapsed time since last callback tick.
        previous_time: Last update timestamp in scheduler time units.
        duration: Callback period in scheduler time units.
        callback: Invoked each time enough elapsed time accumulates.
    """

    def __init__(self, duration: float, callback: Callable[[], None]) -> None:
        """Create a fresh interval accumulator."""
        # Start at zero so the first update initializes baseline timing.
        self.timer: float = 0
        self.previous_time: Optional[float] = None
        self.duration: float = duration
        self.callback: Callable[[], None] = callback
