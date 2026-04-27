from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Hashable


@dataclass
class _Timer:
    interval_seconds: float
    callback: Callable[[], None]
    elapsed_seconds: float = 0.0
    once: bool = False


class Timers:
    """Frame-driven repeating and one-shot timer service."""

    def __init__(self) -> None:
        self._timers: Dict[Hashable, _Timer] = {}

    def add_timer(self, timer_id: Hashable, interval_seconds: float, callback: Callable[[], None]) -> None:
        """Register a repeating timer that fires every *interval_seconds*."""
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be > 0")
        if not callable(callback):
            raise ValueError("callback must be callable")
        self._timers[timer_id] = _Timer(float(interval_seconds), callback)

    def add_once(self, timer_id: Hashable, delay_seconds: float, callback: Callable[[], None]) -> None:
        """Register a one-shot timer that fires once after *delay_seconds* then removes itself."""
        if delay_seconds <= 0:
            raise ValueError("delay_seconds must be > 0")
        if not callable(callback):
            raise ValueError("callback must be callable")
        self._timers[timer_id] = _Timer(float(delay_seconds), callback, once=True)

    def has_timer(self, timer_id: Hashable) -> bool:
        """Return True if a timer with *timer_id* is currently registered."""
        return timer_id in self._timers

    def remove_timer(self, timer_id: Hashable) -> None:
        self._timers.pop(timer_id, None)

    def timer_ids(self) -> list:
        """Return a list of all currently registered timer ids (both repeating and one-shot)."""
        return list(self._timers.keys())

    def cancel_all(self) -> int:
        """Cancel all registered timers and return the number that were removed."""
        count = len(self._timers)
        self._timers.clear()
        return count

    def reschedule(self, timer_id: Hashable, new_interval_seconds: float) -> bool:
        """Change the interval of an existing repeating timer; return False if not found.

        The elapsed accumulator is preserved so that partial progress toward the next
        fire is not discarded.  One-shot timers may also be rescheduled — their
        remaining delay is updated to *new_interval_seconds*.  Raises ``ValueError``
        when *new_interval_seconds* is not > 0.
        """
        if new_interval_seconds <= 0:
            raise ValueError("new_interval_seconds must be > 0")
        timer = self._timers.get(timer_id)
        if timer is None:
            return False
        timer.interval_seconds = float(new_interval_seconds)
        return True

    def update(self, dt_seconds: float) -> None:
        if dt_seconds <= 0 or not self._timers:
            return
        for timer_id in list(self._timers.keys()):
            timer = self._timers.get(timer_id)
            if timer is None:
                continue
            timer.elapsed_seconds += dt_seconds
            if timer.once:
                if timer.elapsed_seconds >= timer.interval_seconds:
                    self._timers.pop(timer_id, None)
                    timer.callback()
            else:
                while timer.elapsed_seconds >= timer.interval_seconds:
                    timer.elapsed_seconds -= timer.interval_seconds
                    timer.callback()
