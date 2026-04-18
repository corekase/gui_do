from __future__ import annotations

from typing import Callable, Dict, Hashable

from ..events import GuiError
from .interval import Interval


class Timers:
    def __init__(self) -> None:
        self.timers: Dict[Hashable, Interval] = {}

    def add_timer(self, id: Hashable, duration: float, callback: Callable[[], None]) -> None:
        try:
            hash(id)
        except TypeError as exc:
            raise GuiError(f'timer id must be hashable: {id!r}') from exc
        if duration <= 0:
            raise GuiError(f'timer duration must be > 0, got: {duration}')
        if not callable(callback):
            raise GuiError('timer callback must be callable')
        self.timers[id] = Interval(duration, callback)

    def remove_timer(self, id: Hashable) -> None:
        try:
            hash(id)
        except TypeError as exc:
            raise GuiError(f'timer id must be hashable: {id!r}') from exc
        if id in self.timers:
            del self.timers[id]

    def timer_updates(self, now_time: int) -> None:
        for id in list(self.timers.keys()):
            interval = self.timers.get(id)
            if interval is None:
                continue
            if interval.previous_time is None:
                interval.previous_time = now_time
            else:
                elapsed_time = now_time - interval.previous_time
                interval.previous_time = now_time
                interval.timer += elapsed_time
                while interval.timer >= interval.duration:
                    interval.timer -= interval.duration
                    interval.callback()
                    interval = self.timers.get(id)
                    if interval is None:
                        break
