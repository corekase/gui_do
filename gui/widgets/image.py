import pygame
from .widget import Widget
from ..utility import file_resource

class Image(Widget):
    def __init__(self, id, rect, image, scale=True):
        # initialize id and rect
        super().__init__(id, rect)
        self.image = pygame.image.load(file_resource('images', image))
        if scale:
            self.image = pygame.transform.smoothscale(self.image, (rect.width, rect.height))

    def handle_event(self, _, _a):
        return False

    def draw(self):
        # draw the image bitmap
        self.surface.blit(self.image, self.rect)
