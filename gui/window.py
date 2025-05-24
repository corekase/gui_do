#
import pygame

class Window:
    def __init__(self, gui_manager, group, size, pos):
        self.gui_manager = gui_manager
        self.group = group
        self.width, self.height = size
        self.x, self.y = pos
        self.surface = pygame.surface.Surface(size).convert()
        self.widgets = {}
        self.gui_manager.add_window(self)
        self.gui_manager.set_group(group, self)

    def set_pos(self, pos):
        self.x, self.y = pos
