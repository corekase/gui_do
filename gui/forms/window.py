import pygame
from pygame import Rect
from ..guimanager import GuiManager
from ..bitmapfactory import BitmapFactory
from ..utility import copy_graphic_area, set_active_object, colours
from ..widgets.frame import Frame, FrameState

class Window:
    def __init__(self, name, title, pos, size):
        self.gui = GuiManager()
        factory = BitmapFactory()
        # window x and y position from the main surface coordinate, not the titlebar
        self.x, self.y = pos
        self.width, self.height = size
        # titlebar size
        self.titlebar_size = 20
        # window surface
        self.surface = pygame.surface.Surface(size).convert()
        # make a frame for the backdrop of the window surface
        frame = Frame('window_frame', Rect(0, 0, size[0], size[1]))
        frame.state = FrameState.IDLE
        frame.surface = self.surface
        frame.draw()
        self.pristine = None
        self.window_save_pristine()
        # widgets on that surface
        self.widgets = []
        # add this window to the gui
        self.gui.add_window(self)
        # make this object the destination for gui add commands
        set_active_object(self)
        # set the window to the position passed in
        self.set_pos(pos)
        self.title_bar_bitmap = factory.draw_title_bar_bitmap(title, self.width, self.height)
        self.title_bar_rect = self.title_bar_bitmap.get_rect()
        self.window_widget_lower_bitmap = factory.draw_window_lower_widget_bitmap(self.titlebar_size, colours['full'], colours['medium'])

    def window_save_pristine(self):
        # update the window pristine bitmap
        self.pristine = copy_graphic_area(self.surface, self.surface.get_rect()).convert()

    def draw_title_bar(self):
        self.gui.surface.blit(self.title_bar_bitmap, (self.x, self.y - self.titlebar_size))
        self.gui.surface.blit(self.window_widget_lower_bitmap, self.get_widget_rect())

    def get_title_bar_rect(self):
        return Rect(self.x, self.y - self.titlebar_size, self.width, self.titlebar_size)

    def get_window_rect(self):
        # total rect of the window including titlebar and surface
        return Rect(self.x, self.y - self.titlebar_size, self.width, self.height + self.titlebar_size)

    def get_widget_rect(self):
        x, y, w, h = self.window_widget_lower_bitmap.get_rect()
        return Rect(self.x + self.width - self.titlebar_size + 1, self.y - self.titlebar_size + 1, w, h)

    def set_pos(self, pos):
        self.x, self.y = pos

    def get_name(self):
        # return the name of the window
        return self.name
