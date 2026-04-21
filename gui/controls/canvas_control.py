from collections import deque
from dataclasses import dataclass
from typing import Callable, Deque, Optional
from typing import TYPE_CHECKING

from pygame import Rect, Surface

from ..core.gui_event import EventType, GuiEvent
from ..core.ui_node import UiNode

if TYPE_CHECKING:
    from ..theme.color_theme import ColorTheme


@dataclass
class CanvasEventPacket:
    kind: EventType
    pos: Optional[tuple] = None
    rel: Optional[tuple] = None
    button: Optional[int] = None
    wheel_delta: Optional[int] = None

    def is_mouse_motion(self) -> bool:
        return self.kind is EventType.MOUSE_MOTION

    def is_mouse_wheel(self) -> bool:
        return self.kind is EventType.MOUSE_WHEEL

    def is_mouse_down(self, button: Optional[int] = None) -> bool:
        if self.kind is not EventType.MOUSE_BUTTON_DOWN:
            return False
        return button is None or self.button == int(button)

    def is_mouse_up(self, button: Optional[int] = None) -> bool:
        if self.kind is not EventType.MOUSE_BUTTON_UP:
            return False
        return button is None or self.button == int(button)


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
        self._visuals = None
        self._visual_size = None

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

    def handle_event(self, event: GuiEvent, _app) -> bool:
        raw = event.pos
        if not (isinstance(raw, tuple) and len(raw) == 2 and self.rect.collidepoint(raw)):
            return False

        packet = CanvasEventPacket(
            kind=event.kind,
            pos=raw,
            rel=event.rel,
            button=event.button,
            wheel_delta=event.wheel_delta,
        )
        if event.is_mouse_motion() and self.coalesce_motion_events and self._events:
            last = self._events[-1]
            if last.is_mouse_motion():
                self._events[-1] = packet
                self._dropped_events = 0
                return True

        if len(self._events) >= self._events.maxlen:
            self._dropped_events += 1
            if self.overflow_mode == "drop_newest":
                if self.on_overflow is not None:
                    self.on_overflow(self._dropped_events, len(self._events))
                return True

        self._events.append(packet)
        self._dropped_events = 0
        return event.is_mouse_down() or event.is_mouse_up() or event.is_mouse_motion() or event.is_mouse_wheel()

    def draw(self, surface: Surface, theme: "ColorTheme") -> None:
        factory = theme.graphics_factory
        visual_size = (self.rect.width, self.rect.height)
        if self._visuals is None or self._visual_size != visual_size:
            self._visuals = factory.build_frame_visuals(self.rect)
            self._visual_size = visual_size
        selected = factory.resolve_visual_state(
            self._visuals,
            visible=self.visible,
            enabled=self.enabled,
            armed=False,
            hovered=False,
        )
        surface.blit(selected, self.rect)
        surface.blit(self.canvas, self.rect)
