from __future__ import annotations

from typing import Callable, Optional


class Interval:
    def __init__(self, duration: float, callback: Callable[[], None]) -> None:
        self.timer: float = 0
        self.previous_time: Optional[float] = None
        self.duration: float = duration
        self.callback: Callable[[], None] = callback
