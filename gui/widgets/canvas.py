import pygame
from pygame import Rect
from .widget import Widget
from .frame import Frame, FrState
from ..command import copy_graphic_area, convert_to_window, set_backdrop

class Canvas(Widget):
    def __init__(self, id, rect, backdrop=None, canvas_callback=None):
        super().__init__(id, rect)
        # create widget surface
        self.surface = pygame.surface.Surface((rect.width, rect.height)).convert()
        self.pristine = pygame.surface.Surface((rect.width, rect.height)).convert()
        # create canvas surface
        self.canvas = pygame.surface.Surface((rect.width, rect.height)).convert()
        # if there is no backdrop make a frame as one otherwise load the backdrop
        if backdrop == None:
            # make a frame for the backdrop of the window surface
            frame = Frame('canvas_frame', Rect(0, 0, rect.width, rect.height))
            frame.state = FrState.Idle
            frame.surface = self.canvas
            frame.draw()
            self.surface.blit(self.canvas, self.canvas.get_rect())
            self.pristine = copy_graphic_area(self.canvas, self.canvas.get_rect()).convert()
        else:
            set_backdrop(backdrop, self)
        # variables that the gui_do client can read
        self.last_x = self.last_y = None
        self.last_buttons = []
        self.canvas_callback = canvas_callback

    def get_canvas_surface(self):
        # return a reference to the canvas surface
        return self.canvas

    def restore_pristine(self, area=None):
        # copy an area from the pristine bitmap to the canvas bitmap
        if area == None:
            area = self.canvas.get_rect()
        self.canvas.blit(self.pristine, area)

    def read(self):
        # returns (last_x, last_y) as a coordinate, and last mouse buttons as a three
        # value sequence of true or false for the buttons
        # -> To-do: if the canvas widget receives mousewheel events then put those here
        #           in a variable to be read.
        return (self.last_x, self.last_y), self.last_buttons

    def handle_event(self, event, window):
        if self.get_collide(window):
            # -> To-do: if mousewheel event..
            # within the canvas so update information about that
            last_x, last_y = convert_to_window(self.gui.get_mouse_pos(), self.window)
            self.last_x, self.last_y = last_x - self.rect.x, last_y - self.rect.y
            self.last_buttons = pygame.mouse.get_pressed()
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
            return False

    def draw(self):
        # copy the canvas surface to the widget surface
        self.surface.blit(self.canvas, self.rect)
