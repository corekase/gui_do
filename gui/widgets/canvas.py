import pygame
from collections import deque
import logging
from pygame.event import Event as PygameEvent
from pygame.surface import Surface
from typing import Callable, Optional, Tuple, TYPE_CHECKING
from pygame import Rect
from pygame.locals import MOUSEWHEEL, MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP
from ..utility.constants import GuiError, InteractiveState, CanvasEvent
from ..utility.widget import Widget
from .frame import Frame

if TYPE_CHECKING:
    from ..utility.guimanager import GuiManager
    from .window import Window

_logger = logging.getLogger(__name__)

class CanvasEventPacket:
    """Canvas input payload with normalized coordinates and event-specific fields."""

    def __init__(self) -> None:
        self.type: Optional[CanvasEvent] = None
        self.pos: Optional[Tuple[int, int]] = None
        self.rel: Optional[Tuple[int, int]] = None
        self.button: Optional[int] = None
        self.y: Optional[int] = None

class Canvas(Widget):
    """Off-screen drawing surface that queues canvas-local input events."""

    _DEFAULT_MAX_QUEUED_EVENTS = 128

    def __init__(self, gui: "GuiManager", id: str, rect: Rect, backdrop: Optional[str] = None, on_activate: Optional[Callable[[], None]] = None, automatic_pristine: bool = False) -> None:
        if on_activate is not None and not callable(on_activate):
            raise GuiError('on_activate must be callable when provided')
        super().__init__(gui, id, rect)
        self.canvas: Surface = pygame.surface.Surface((rect.width, rect.height)).convert()
        if backdrop is None:
            frame = Frame(gui, 'canvas_frame', Rect(0, 0, rect.width, rect.height))
            frame.state = InteractiveState.Idle
            frame.surface = self.canvas
            frame.draw()
            self.pristine = self.gui.copy_graphic_area(self.canvas, self.canvas.get_rect()).convert()
        else:
            self.gui.set_pristine(backdrop, self)
        self.on_activate = on_activate
        self.auto_restore_pristine: bool = automatic_pristine
        self._events: deque[CanvasEventPacket] = deque()
        self._configure_max_queued_events()
        self.dropped_events: int = 0
        self.last_overflow: bool = False
        self.on_overflow: Optional[Callable[[int, int], None]] = None
        self.coalesce_motion_events: bool = True
        self.queued_event: bool = False
        self.CEvent: Optional["CanvasEventPacket"] = None

    def get_canvas_surface(self) -> Surface:
        return self.canvas

    def get_event_queue_limit(self) -> int:
        maxlen = self._events.maxlen
        return 0 if maxlen is None else maxlen

    def read_event(self) -> Optional[CanvasEventPacket]:
        """Pop the next queued canvas event, or None when empty."""
        if not self._events:
            self.queued_event = False
            self.CEvent = None
            return None
        event = self._events.popleft()
        self.queued_event = len(self._events) > 0
        self.CEvent = self._events[0] if self._events else None
        return event

    def set_event_queue_limit(self, max_events: int) -> None:
        self._configure_max_queued_events(max_events)
        self.queued_event = len(self._events) > 0
        self.CEvent = self._events[0] if self._events else None

    def _configure_max_queued_events(self, max_events: Optional[int] = None) -> None:
        if max_events is None:
            max_events = self._DEFAULT_MAX_QUEUED_EVENTS
        if not isinstance(max_events, int):
            raise GuiError(f'max_events must be an int, got: {type(max_events).__name__}')
        if max_events <= 0:
            raise GuiError(f'max_events must be > 0, got: {max_events}')
        if self._events.maxlen == max_events:
            return
        self._events = deque(self._events, maxlen=max_events)

    def set_motion_coalescing(self, enabled: bool) -> None:
        if not isinstance(enabled, bool):
            raise GuiError(f'motion coalescing flag must be bool, got: {type(enabled).__name__}')
        self.coalesce_motion_events = enabled

    def set_overflow_handler(self, callback: Optional[Callable[[int, int], None]]) -> None:
        if callback is not None and not callable(callback):
            raise GuiError('overflow callback must be callable when provided')
        self.on_overflow = callback

    def handle_event(self, event: PygameEvent, window: Optional["Window"]) -> bool:
        """Queue supported events while focused and signal activation on enqueue."""
        if event.type not in (MOUSEWHEEL, MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP):
            return False
        locked_owner = (self.gui.locking_object is self) and self.gui.mouse_locked
        if self.get_collide(window) or locked_owner:
            canvas_x, canvas_y = self.gui.convert_to_window(self.gui.get_mouse_pos(), self.window)
            packet = CanvasEventPacket()
            packet.pos = (canvas_x - self.draw_rect.x, canvas_y - self.draw_rect.y)
            if event.type == MOUSEWHEEL:
                packet.type = CanvasEvent.MouseWheel
                packet.y = getattr(event, 'y', None)
            elif event.type == MOUSEMOTION:
                packet.type = CanvasEvent.MouseMotion
                packet.rel = getattr(event, 'rel', None)
            elif event.type == MOUSEBUTTONDOWN:
                packet.type = CanvasEvent.MouseButtonDown
                packet.button = getattr(event, 'button', None)
            elif event.type == MOUSEBUTTONUP:
                packet.type = CanvasEvent.MouseButtonUp
                packet.button = getattr(event, 'button', None)
            # Coalescing keeps motion floods from starving click/wheel processing.
            if (
                self.coalesce_motion_events
                and packet.type == CanvasEvent.MouseMotion
                and len(self._events) > 0
                and self._events[-1].type == CanvasEvent.MouseMotion
            ):
                self._events[-1] = packet
                self.queued_event = True
                self.CEvent = self._events[0]
                return True
            was_full = len(self._events) == self._events.maxlen
            self.last_overflow = was_full
            if was_full:
                self.dropped_events += 1
                if self.on_overflow is not None:
                    try:
                        self.on_overflow(1, self.dropped_events)
                    except Exception as exc:
                        _logger.warning('Canvas overflow callback failed: %s: %s', type(exc).__name__, exc)
            self._events.append(packet)
            self.queued_event = True
            self.CEvent = self._events[0]
            return True
        else:
            return False

    def draw(self) -> None:
        """Blit canvas contents into the owning GUI surface."""
        self.surface.blit(self.canvas, self.draw_rect)
        if self.auto_restore_pristine:
            self.restore_pristine()

    def focused(self) -> bool:
        """Return True when mouse is inside this canvas."""
        if self.draw_rect.collidepoint(self.gui.convert_to_window(self.gui.get_mouse_pos(), self.window)):
            return True
        else:
            return False

    def restore_pristine(self, area: Optional[Rect] = None) -> None:
        """Restore a region from the canvas pristine snapshot."""
        if self.pristine is None:
            raise GuiError('canvas pristine image is not initialized')
        if area is None:
            area = self.canvas.get_rect()
        self.canvas.blit(self.pristine, (area.x, area.y), area)
