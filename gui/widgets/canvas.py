import pygame
from typing import Optional, Any, Tuple
from pygame import Rect
from pygame.locals import MOUSEWHEEL, MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP
from ..utility.constants import WidgetKind, CanvasEvent
from ..utility.widget import Widget
from .frame import Frame
from ..utility.constants import InteractiveState

class CanvasEventPacket:
    """Event packet for canvas-specific events.

    Contains event type, mouse position relative to canvas, and type-specific data.
    """
    def __init__(self) -> None:
        self.type: Optional[Any] = None
        self.pos: Optional[Tuple[int, int]] = None
        self.rel: Optional[Tuple[int, int]] = None
        self.button: Optional[int] = None
        self.y: Optional[int] = None

class Canvas(Widget):
    def __init__(self, gui: Any, id: Any, rect: Rect, backdrop: Optional[str] = None, canvas_callback: Optional[Any] = None, automatic_pristine: bool = False) -> None:
        super().__init__(gui, id, rect)
        self.WidgetKind = WidgetKind.Canvas
        # create canvas surface
        self.canvas: pygame.Surface = pygame.surface.Surface((rect.width, rect.height)).convert()
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
        self.canvas_callback: Optional[Any] = canvas_callback
        self.auto_restore_pristine: bool = automatic_pristine
        self.queued_event: bool = False
        self.CEvent: Optional["CanvasEventPacket"] = None

    def get_canvas_surface(self) -> pygame.Surface:
        # return a reference to the canvas surface
        return self.canvas

    def restore_pristine(self, area: Optional[Rect] = None) -> None:
        # copy an area from the pristine bitmap to the canvas bitmap
        if area is None:
            area = self.canvas.get_rect()
        self.canvas.blit(self.pristine, area)

    def read_event(self) -> Optional[CanvasEventPacket]:
        """Read a queued canvas event.

        Canvas events are blocking - no new events are generated until the previous
        one is read. This must be called first to retrieve any queued event.

        Returns:
            CanvasEventPacket if an event is queued, None otherwise.
        """
        if self.queued_event:
            self.queued_event = False
            return self.CEvent
        return None

    def focused(self) -> bool:
        # return a boolean of whether or not the mouse is over the canvas
        if self.draw_rect.collidepoint(self.gui.convert_to_window(self.gui.get_mouse_pos(), self.window)):
            return True
        else:
            return False

    def handle_event(self, event: Any, window: Any) -> bool:
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
            if not self.queued_event:
                self.queued_event = True
                # within the canvas so update information about that
                canvas_x, canvas_y = self.gui.convert_to_window(self.gui.get_mouse_pos(), self.window)
                # create a new event
                self.CEvent = CanvasEventPacket()
                # all events have the position field
                self.CEvent.pos = (canvas_x - self.draw_rect.x, canvas_y - self.draw_rect.y)
                # and type specific fields
                if event.type == MOUSEWHEEL:
                    self.CEvent.type = CanvasEvent.MouseWheel
                    self.CEvent.y = event.y
                elif event.type == MOUSEMOTION:
                    self.CEvent.type = CanvasEvent.MouseMotion
                    self.CEvent.rel = event.rel
                elif event.type == MOUSEBUTTONDOWN:
                    self.CEvent.type = CanvasEvent.MouseButtonDown
                    self.CEvent.button = event.button
                elif event.type == MOUSEBUTTONUP:
                    self.CEvent.type = CanvasEvent.MouseButtonUp
                    self.CEvent.button = event.button
                else:
                    # otherwise the catch-all event is MousePosition which is set above for all events
                    self.CEvent.type = CanvasEvent.MousePosition
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
                # return no signal, there is a queued event waiting to be read
                return False
        else:
            # the mouse is not over the canvas
            return False

    def draw(self) -> None:
        # copy the canvas surface to the widget surface
        self.surface.blit(self.canvas, self.draw_rect)
        # handle the pristine surface
        if self.auto_restore_pristine:
            self.restore_pristine()
