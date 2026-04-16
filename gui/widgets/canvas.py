import pygame
from collections import deque
import logging
from pygame.event import Event as PygameEvent
from pygame.surface import Surface
from typing import Callable, Optional, Tuple, TYPE_CHECKING
from pygame import Rect
from pygame.locals import MOUSEWHEEL, MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP
from ..utility.constants import WidgetKind, CanvasEvent
from ..utility.widget import Widget
from .frame import Frame
from ..utility.constants import InteractiveState
from ..utility.constants import GuiError

if TYPE_CHECKING:
    from ..utility.guimanager import GuiManager
    from .window import Window

_logger = logging.getLogger(__name__)

class CanvasEventPacket:
    """Event packet for canvas-specific events.

    Contains event type, mouse position relative to canvas, and type-specific data.
    """
    def __init__(self) -> None:
        self.type: Optional[CanvasEvent] = None
        self.pos: Optional[Tuple[int, int]] = None
        self.rel: Optional[Tuple[int, int]] = None
        self.button: Optional[int] = None
        self.y: Optional[int] = None

class Canvas(Widget):
    def __init__(self, gui: "GuiManager", id: str, rect: Rect, backdrop: Optional[str] = None, on_activate: Optional[Callable[[], None]] = None, automatic_pristine: bool = False) -> None:
        if on_activate is not None and not callable(on_activate):
            raise GuiError('on_activate must be callable when provided')
        super().__init__(gui, id, rect)
        self.WidgetKind = WidgetKind.Canvas
        # create canvas surface
        self.canvas: Surface = pygame.surface.Surface((rect.width, rect.height)).convert()
        # if there is no backdrop make a frame as one otherwise load the backdrop
        if backdrop is None:
            # make a frame for the backdrop of the window surface
            frame = Frame(gui, 'canvas_frame', Rect(0, 0, rect.width, rect.height))
            frame.state = InteractiveState.Idle
            frame.surface = self.canvas
            frame.draw()
            self.pristine = self.gui.copy_graphic_area(self.canvas, self.canvas.get_rect()).convert()
        else:
            self.gui.set_pristine(backdrop, self)
        self.on_activate = on_activate
        self.auto_restore_pristine: bool = automatic_pristine
        self._events: deque[CanvasEventPacket] = deque(maxlen=128)
        self.dropped_events: int = 0
        self.last_overflow: bool = False
        self.on_overflow: Optional[Callable[[int, int], None]] = None
        self.queued_event: bool = False
        self.CEvent: Optional["CanvasEventPacket"] = None

    def set_event_queue_limit(self, max_events: int) -> None:
        if not isinstance(max_events, int):
            raise GuiError(f'max_events must be an int, got: {type(max_events).__name__}')
        if max_events <= 0:
            raise GuiError(f'max_events must be > 0, got: {max_events}')
        if self._events.maxlen == max_events:
            return
        self._events = deque(self._events, maxlen=max_events)
        self.queued_event = len(self._events) > 0
        self.CEvent = self._events[0] if self._events else None

    def get_event_queue_limit(self) -> int:
        maxlen = self._events.maxlen
        return 0 if maxlen is None else maxlen

    def set_overflow_handler(self, callback: Optional[Callable[[int, int], None]]) -> None:
        if callback is not None and not callable(callback):
            raise GuiError('overflow callback must be callable when provided')
        self.on_overflow = callback

    def get_canvas_surface(self) -> Surface:
        # return a reference to the canvas surface
        return self.canvas

    def restore_pristine(self, area: Optional[Rect] = None) -> None:
        # copy an area from the pristine bitmap to the canvas bitmap
        if self.pristine is None:
            raise GuiError('canvas pristine image is not initialized')
        if area is None:
            area = self.canvas.get_rect()
        self.canvas.blit(self.pristine, (area.x, area.y), area)

    def read_event(self) -> Optional[CanvasEventPacket]:
        """Read a queued canvas event.

        Canvas events are blocking - no new events are generated until the previous
        one is read. This must be called first to retrieve any queued event.

        Returns:
            CanvasEventPacket if an event is queued, None otherwise.
        """
        if not self._events:
            self.queued_event = False
            self.CEvent = None
            return None
        event = self._events.popleft()
        self.queued_event = len(self._events) > 0
        self.CEvent = self._events[0] if self._events else None
        return event

    def focused(self) -> bool:
        # return a boolean of whether or not the mouse is over the canvas
        if self.draw_rect.collidepoint(self.gui.convert_to_window(self.gui.get_mouse_pos(), self.window)):
            return True
        else:
            return False

    def handle_event(self, event: PygameEvent, window: Optional["Window"]) -> bool:
        """Handle canvas events and queue them for processing.

        Events are queued while the canvas has focus. If a queued event hasn't been
        read yet, no new events are generated until it's retrieved via read_event().

        Args:
            event: The pygame event to handle.
            window: The parent window, if any.

        Returns:
            bool: True if event was handled and should signal activation, False otherwise.
        """
        if event.type not in (MOUSEWHEEL, MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP):
            return False
        if self.get_collide(window):
            # within the canvas so update information about that
            canvas_x, canvas_y = self.gui.convert_to_window(self.gui.get_mouse_pos(), self.window)
            # create a new event
            packet = CanvasEventPacket()
            # all events have the position field
            packet.pos = (canvas_x - self.draw_rect.x, canvas_y - self.draw_rect.y)
            # and type specific fields
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
            # signal activation; GuiManager dispatches on_activate if present
            return True
        else:
            # the mouse is not over the canvas
            return False

    def draw(self) -> None:
        # copy the canvas surface to the widget surface
        self.surface.blit(self.canvas, self.draw_rect)
        # handle the pristine surface
        if self.auto_restore_pristine:
            self.restore_pristine()
