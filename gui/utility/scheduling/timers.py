from __future__ import annotations

from typing import Callable, Dict, Hashable

from ..events import GuiError
from .interval import Interval


class Timers:
    """Own and update named repeating timer intervals.

    The manager supports hashable timer ids, per-tick elapsed accumulation,
    and safe removal during callback execution.
    """

    def __init__(self) -> None:
        """Initialize an empty timer registry."""
        self.timers: Dict[Hashable, Interval] = {}

    def add_timer(self, id: Hashable, duration: float, callback: Callable[[], None]) -> None:
        """Register or replace a repeating timer.

        Args:
            id: Hashable identifier for timer lookup and replacement.
            duration: Positive interval duration.
            callback: Callable invoked for each elapsed interval tick.
        """
        # Enforce hashability because timer ids are dict keys.
        try:
            hash(id)
        except TypeError as exc:
            raise GuiError(f'timer id must be hashable: {id!r}') from exc
        # Reject invalid interval and callback contracts early.
        if duration <= 0:
            raise GuiError(f'timer duration must be > 0, got: {duration}')
        if not callable(callback):
            raise GuiError('timer callback must be callable')
        # Replacing an existing id intentionally resets interval state.
        self.timers[id] = Interval(duration, callback)

    def remove_timer(self, id: Hashable) -> None:
        """Remove a timer by id when present."""
        # Mirror add-time hashability guard for consistent API errors.
        try:
            hash(id)
        except TypeError as exc:
            raise GuiError(f'timer id must be hashable: {id!r}') from exc
        # Deletion is intentionally idempotent for absent keys.
        if id in self.timers:
            del self.timers[id]

    def timer_updates(self, now_time: int) -> None:
        """Advance all timers and execute callbacks for elapsed intervals.

        Timers are iterated over a snapshot so callbacks can safely remove their
        own timer ids without mutating the active key iteration.
        """
        # Iterate over a snapshot so callbacks can mutate `self.timers` safely.
        for id in list(self.timers.keys()):
            interval = self.timers.get(id)
            if interval is None:
                continue
            # First sighting establishes a baseline timestamp.
            if interval.previous_time is None:
                interval.previous_time = now_time
            else:
                # Accumulate elapsed time since last update.
                elapsed_time = now_time - interval.previous_time
                interval.previous_time = now_time
                interval.timer += elapsed_time
                # Run callback once per elapsed duration chunk.
                while interval.timer >= interval.duration:
                    interval.timer -= interval.duration
                    interval.callback()
                    # Re-fetch in case callback removed/replaced this timer.
                    interval = self.timers.get(id)
                    if interval is None:
                        break
