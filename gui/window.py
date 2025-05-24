from .frame import Frame, State
import pygame
from pygame import Rect
from . import utility
from .utility import set_font, set_last_font, render_text, centre

class Window:
    def __init__(self, gui_manager, title, group, size, pos):
        self.gui_manager = gui_manager
        self.group = group
        self.width, self.height = size
        self.x, self.y = pos
        self.surface = pygame.surface.Surface(size).convert()
        self.widgets = {}
        self.widgets[group] = []
        self.gui_manager.add_window(self)
        self.gui_manager.set_group(group, self)
        frame = Frame('none', Rect(0, 0, size[0], size[1]))
        frame.state = State.IDLE
        frame.surface = self.surface
        self.widgets[group].insert(0, frame)
        self.title_bar_graphic = self.make_title_bar_graphic(title)
        self.title_bar_rect = self.title_bar_graphic.get_rect()
        self.set_pos(pos)

    def make_title_bar_graphic(self, title):
        set_font('titlebar')
        text_bitmap = render_text(title)
        title_surface = pygame.surface.Surface((self.width, 20)).convert()
        frame = Frame('none', Rect(0, 0, self.width, 20))
        frame.surface = title_surface
        frame.state = State.ARMED
        frame.draw()
        title_surface.blit(text_bitmap, (4, centre(20, 10) - 2))
        set_last_font()
        return title_surface

    def draw_title_bar(self):
        self.gui_manager.surface.blit(self.title_bar_graphic, (self.x, self.y - 20))

    def set_pos(self, pos):
        self.x, self.y = pos
        self.title_bar_rect = Rect(self.x, self.y - 20, self.width, 20)
