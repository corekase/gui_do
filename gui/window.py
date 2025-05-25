from .guimanager import GuiManager
from .frame import Frame, State
import pygame
from pygame import Rect
from .utility import set_font, set_last_font, render_text, centre

class Window:
    def __init__(self, name, title, pos, size):
        self.gui = GuiManager()
        self.set_name(name)
        self.x, self.y = pos
        self.width, self.height = size
        self.titlebar_size = 20
        self.surface = pygame.surface.Surface(size).convert()
        self.widgets = []
        self.gui.add_window(self)
        self.gui.set_active_object(self)
        frame = Frame('window_frame', Rect(0, 0, size[0], size[1]))
        frame.state = State.IDLE
        frame.surface = self.surface
        self.widgets.insert(0, frame)
        self.title_bar_graphic = self.make_title_bar_graphic(title)
        self.title_bar_rect = self.title_bar_graphic.get_rect()
        self.set_pos(pos)

    def make_title_bar_graphic(self, title):
        set_font('titlebar')
        text_bitmap = render_text(title)
        title_surface = pygame.surface.Surface((self.width, self.titlebar_size)).convert()
        frame = Frame('titlebar_frame', Rect(0, 0, self.width, self.titlebar_size))
        frame.state = State.ARMED
        frame.surface = title_surface
        frame.draw()
        title_surface.blit(text_bitmap, (4, centre(self.titlebar_size, 10) - 2))
        set_last_font()
        return title_surface

    def draw_title_bar(self):
        self.gui.surface.blit(self.title_bar_graphic, (self.x, self.y - self.titlebar_size))

    def get_rect(self):
        # total rect of the window including titlebar and surface
        return Rect(self.x, self.y - self.titlebar_size, self.width, self.height + self.titlebar_size)

    def set_pos(self, pos):
        self.x, self.y = pos
        self.title_bar_rect = Rect(self.x, self.y - self.titlebar_size, self.width, self.titlebar_size)

    def set_name(self, name):
        # name the window
        self.name = name

    def get_name(self):
        # return the name of the window
        return self.name
