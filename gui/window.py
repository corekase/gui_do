#
import pygame

class Window:
    def __init__(self, size, pos):
        self.width, self.height = size
        self.x, self.y = pos
        self.surface = pygame.surface.Surface(size).convert()
        self.widgets = {}
