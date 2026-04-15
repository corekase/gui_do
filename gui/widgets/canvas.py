import pygame
from typing import Optional, Any
from pygame import Rect
from pygame.locals import MOUSEWHEEL, MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP
from ..utility.values.constants import WidgetKind, CanvasEventKind
from ..utility.widget import Widget
from .frame import Frame
from ..utility.values.constants import InteractiveState
from ..utility.registry import register_widget

@register_widget("Canvas")
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
        self.CEvent: Optional["CanvasEvent"] = None

    def get_canvas_surface(self) -> pygame.Surface:
        # return a reference to the canvas surface
        return self.canvas

    def restore_pristine(self, area: Optional[Rect] = None) -> None:
        # copy an area from the pristine bitmap to the canvas bitmap
        if area is None:
            area = self.canvas.get_rect()
        self.canvas.blit(self.pristine, area)

    def read_event(self) -> Optional["CanvasEvent"]:
        # canvas events are blocking, no new events will be generated until the previous one
        # is read. either as a signal or in a callback, the first thing is to read the event
        if self.queued_event == True:
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
        if self.get_collide(window):
            if self.queued_event == False:
                self.queued_event = True
                # within the canvas so update information about that
                canvas_x, canvas_y = self.gui.convert_to_window(self.gui.get_mouse_pos(), self.window)
                # create a new event
                self.CEvent = CanvasEvent()
                # all events have the position field
                self.CEvent.pos = (canvas_x - self.draw_rect.x, canvas_y - self.draw_rect.y)
                # and type specific fields
                if event.type == MOUSEWHEEL:
                    self.CEvent.type = CanvasEventKind.MouseWheel
                    self.CEvent.y = event.y
                elif event.type == MOUSEMOTION:
                    self.CEvent.type = CanvasEventKind.MouseMotion
                    self.CEvent.rel = event.rel
                elif event.type == MOUSEBUTTONDOWN:
                    self.CEvent.type = CanvasEventKind.MouseButtonDown
                    self.CEvent.button = event.button
                elif event.type == MOUSEBUTTONUP:
                    self.CEvent.type = CanvasEventKind.MouseButtonUp
                    self.CEvent.button = event.button
                else:
                    # otherwise the catch-all event is MousePosition which is set above for all events
                    self.CEvent.type = CanvasEventKind.MousePosition
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

class CanvasEvent:
    def __init__(self) -> None:
        self.type: Optional[CanvasEventKind] = None
        self.pos: Optional[tuple] = None
        self.y: Optional[int] = None
        self.rel: Optional[tuple] = None
        self.button: Optional[int] = None
