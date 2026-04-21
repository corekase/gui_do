from collections import deque
from dataclasses import dataclass
from typing import Callable, Deque, Optional

from pygame import Rect, Surface
from pygame.draw import rect as draw_rect
from pygame.locals import MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, MOUSEWHEEL

from ..core.ui_node import UiNode


@dataclass
class CanvasEventPacket:
    event_type: int
    pos: Optional[tuple] = None
    rel: Optional[tuple] = None
    button: Optional[int] = None
    wheel_delta: Optional[int] = None


class CanvasControl(UiNode):
    """Drawable canvas with internal event queue."""

    def __init__(self, control_id: str, rect: Rect, max_events: int = 256) -> None:
        super().__init__(control_id, rect)
        self.canvas = Surface(self.rect.size).convert_alpha()
        self.canvas.fill((0, 0, 0, 0))
        self._events: Deque[CanvasEventPacket] = deque(maxlen=max(1, int(max_events)))
        self.coalesce_motion_events = True
        self.overflow_mode = "drop_oldest"
        self.on_overflow: Optional[Callable[[int, int], None]] = None
        self._dropped_events = 0

    def get_canvas_surface(self) -> Surface:
        return self.canvas

    def set_event_queue_limit(self, max_events: int) -> None:
        max_events = max(1, int(max_events))
        snapshot = list(self._events)[-max_events:]
        self._events = deque(snapshot, maxlen=max_events)

    def set_motion_coalescing(self, enabled: bool) -> None:
        self.coalesce_motion_events = bool(enabled)

    def set_overflow_handler(self, callback: Optional[Callable[[int, int], None]]) -> None:
        self.on_overflow = callback

    def set_overflow_mode(self, mode: str) -> None:
        if mode not in ("drop_oldest", "drop_newest"):
            raise ValueError("mode must be drop_oldest or drop_newest")
        self.overflow_mode = mode

    def read_event(self) -> Optional[CanvasEventPacket]:
        if not self._events:
            return None
        return self._events.popleft()

    def handle_event(self, event, _app) -> bool:
        raw = getattr(event, "pos", None)
        if not (isinstance(raw, tuple) and len(raw) == 2 and self.rect.collidepoint(raw)):
            return False

        packet = CanvasEventPacket(
            event_type=event.type,
            pos=raw,
            rel=getattr(event, "rel", None),
            button=getattr(event, "button", None),
            wheel_delta=getattr(event, "y", None),
        )
        if event.type == MOUSEMOTION and self.coalesce_motion_events and self._events:
            last = self._events[-1]
            if last.event_type == MOUSEMOTION:
                self._events[-1] = packet
                return True

        if len(self._events) >= self._events.maxlen:
            self._dropped_events += 1
            if self.overflow_mode == "drop_newest":
                if self.on_overflow is not None:
                    self.on_overflow(self._dropped_events, len(self._events))
                return True

        self._events.append(packet)
        if self.on_overflow is not None and self._dropped_events > 0:
            self.on_overflow(self._dropped_events, len(self._events))
        if event.type in (MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, MOUSEWHEEL):
            return True
        return False

    def draw(self, surface, theme) -> None:
        draw_rect(surface, theme.medium, self.rect, 0)
        draw_rect(surface, theme.dark, self.rect, 2)
        surface.blit(self.canvas, self.rect)
