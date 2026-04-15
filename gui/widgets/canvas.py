import pygame
from collections import deque
from pygame.event import Event as PygameEvent
from pygame.surface import Surface
from typing import Callable, Optional, Tuple, TYPE_CHECKING
from pygame import Rect
from pygame.locals import MOUSEWHEEL, MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP
from ..utility.constants import WidgetKind, CanvasEvent
from ..utility.widget import Widget
from .frame import Frame
from ..utility.constants import InteractiveState

if TYPE_CHECKING:
    from ..utility.guimanager import GuiManager
    from .window import Window

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
    def __init__(self, gui: "GuiManager", id: str, rect: Rect, backdrop: Optional[str] = None, canvas_callback: Optional[Callable[[], None]] = None, automatic_pristine: bool = False) -> None:
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
        self.canvas_callback: Optional[Callable[[], None]] = canvas_callback
        self.auto_restore_pristine: bool = automatic_pristine
        self._events: deque[CanvasEventPacket] = deque(maxlen=32)
        self.dropped_events: int = 0
        self.last_overflow: bool = False
        self.queued_event: bool = False
        self.CEvent: Optional["CanvasEventPacket"] = None

    def get_canvas_surface(self) -> Surface:
        # return a reference to the canvas surface
        return self.canvas

    def restore_pristine(self, area: Optional[Rect] = None) -> None:
        # copy an area from the pristine bitmap to the canvas bitmap
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
                packet.y = event.y
            elif event.type == MOUSEMOTION:
                packet.type = CanvasEvent.MouseMotion
                packet.rel = event.rel
            elif event.type == MOUSEBUTTONDOWN:
                packet.type = CanvasEvent.MouseButtonDown
                packet.button = event.button
            elif event.type == MOUSEBUTTONUP:
                packet.type = CanvasEvent.MouseButtonUp
                packet.button = event.button
            else:
                # otherwise the catch-all event is MousePosition which is set above for all events
                packet.type = CanvasEvent.MousePosition
            was_full = len(self._events) == self._events.maxlen
            self.last_overflow = was_full
            if was_full:
                self.dropped_events += 1
            self._events.append(packet)
            self.queued_event = True
            self.CEvent = self._events[0]
            # the mouse is over the canvas so either do the callback or signal activated
            if self.canvas_callback is not None:
                # do the callback
                self.canvas_callback()
                # callback consumes the event
                return False
            else:
                # no callback, so signal the event instead
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
