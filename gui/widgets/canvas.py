# this will be a surface that the client code can draw directly on
# and is displayed in the gui
import pygame
from pygame import Rect
from .widget import Widget
from .frame import Frame, FrState
from ..command import copy_graphic_area

class Canvas(Widget):
    def __init__(self, id, rect, backdrop=None):
        super().__init__(id, rect)
        self.surface = pygame.surface.Surface((rect.width, rect.height)).convert()
        self.canvas = pygame.surface.Surface((rect.width, rect.height)).convert()
        if backdrop == None:
            # make a frame for the backdrop of the window surface
            frame = Frame('canvas_frame', Rect(0, 0, rect.width, rect.height))
            frame.state = FrState.Idle
            frame.surface = self.canvas
            frame.draw()
        else:
            backdrop = pygame.transform.smoothscale(backdrop, (rect.width, rect.height))
            self.canvas.blit(backdrop, (0, 0))
        self.pristine = copy_graphic_area(self.canvas, Rect(0, 0, rect.width, rect.height)).convert()

    def get_surface(self):
        return self.canvas

    def handle_event(self, _, _a):
        return False

    def draw(self):
        self.surface.blit(self.canvas, (self.rect.x, self.rect.y))
