from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Hashable


@dataclass
class _Timer:
    interval_seconds: float
    callback: Callable[[], None]
    elapsed_seconds: float = 0.0


class Timers:
    """Frame-driven repeating timer service."""

    def __init__(self) -> None:
        self._timers: Dict[Hashable, _Timer] = {}

    def add_timer(self, timer_id: Hashable, interval_seconds: float, callback: Callable[[], None]) -> None:
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be > 0")
        if not callable(callback):
            raise ValueError("callback must be callable")
        self._timers[timer_id] = _Timer(float(interval_seconds), callback)

    def remove_timer(self, timer_id: Hashable) -> None:
        self._timers.pop(timer_id, None)

    def update(self, dt_seconds: float) -> None:
        if dt_seconds <= 0:
            return
        for timer_id in list(self._timers.keys()):
            timer = self._timers.get(timer_id)
            if timer is None:
                continue
            timer.elapsed_seconds += dt_seconds
            while timer.elapsed_seconds >= timer.interval_seconds:
                timer.elapsed_seconds -= timer.interval_seconds
                timer.callback()
