import pygame
from pygame import Rect
from pygame.locals import MOUSEWHEEL, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION
from .widget import Widget
from .frame import Frame, FrState
from ..command import copy_graphic_area, convert_to_window, set_backdrop
from enum import Enum

CKind = Enum('GKind', ['MouseWheel', 'MouseMotion', 'MouseButtonDown', 'MouseButtonUp'])

class Canvas(Widget):
    def __init__(self, id, rect, backdrop=None, canvas_callback=None, automatic_pristine=False):
        super().__init__(id, rect)
        # create canvas surface
        self.canvas = pygame.surface.Surface((rect.width, rect.height)).convert()
        # if there is no backdrop make a frame as one otherwise load the backdrop
        if backdrop == None:
            # make a frame for the backdrop of the window surface
            frame = Frame('canvas_frame', Rect(0, 0, rect.width, rect.height))
            frame.state = FrState.Idle
            frame.surface = self.canvas
            frame.draw()
            self.pristine = copy_graphic_area(self.canvas, self.canvas.get_rect()).convert()
        else:
            set_backdrop(backdrop, self)
        # variables that the gui_do client can read
        self.canvas_callback = canvas_callback
        self.auto_restore_pristine = automatic_pristine
        self.queued_event = False
        self.focus = False

    def get_canvas_surface(self):
        # return a reference to the canvas surface
        return self.canvas

    def restore_pristine(self, area=None):
        # copy an area from the pristine bitmap to the canvas bitmap
        if area == None:
            area = self.canvas.get_rect()
        self.canvas.blit(self.pristine, area)

    def read_event(self):
        # returns (last_x, last_y) as a coordinate, and last mouse buttons as a three
        # value sequence of true or false for the buttons, and then the last mousewheel
        if self.queued_event == True:
            self.queued_event = False
            return self.CEvent

    def focused(self):
        return self.focus

    def handle_event(self, event, window):
        if self.get_collide(window):
            self.focus = True
            if self.queued_event == False:
                self.queued_event = True
                # within the canvas so update information about that
                last_x, last_y = convert_to_window(self.gui.get_mouse_pos(), self.window)
                # create a new event
                self.CEvent = CanvasEvent()
                # all events have the position field
                self.CEvent.pos = (last_x - self.rect.x, last_y - self.rect.y)
                # and type specific fields
                if event.type == MOUSEWHEEL:
                    self.CEvent.type = CKind.MouseWheel
                    self.CEvent.y = event.y
                elif event.type == MOUSEMOTION:
                    self.CEvent.type = CKind.MouseMotion
                    self.CEvent.rel = event.rel
                elif event.type == MOUSEBUTTONDOWN:
                    self.CEvent.type = CKind.MouseButtonDown
                    self.CEvent.button = event.button
                elif event.type == MOUSEBUTTONUP:
                    self.CEvent.type = CKind.MouseButtonUp
                    self.CEvent.button = event.button
                # the mouse is over the canvas so either do the callback or signal activated
                if self.canvas_callback != None:
                    # do the callback
                    self.canvas_callback()
                    # callback consumes the event
                    return False
                else:
                    # no callback, so signal the event instead
                    return True
        else:
            # the mouse is not over the canvas
            self.focus = False
            return False

    def draw(self):
        # copy the canvas surface to the widget surface
        self.surface.blit(self.canvas, self.rect)
        # handle the pristine surface
        if self.auto_restore_pristine:
            self.restore_pristine()

class CanvasEvent:
    def __init__(self):
        self.type: CKind = None
        self.pos = None
        self.y = None
        self.rel = None
        self.button = None
