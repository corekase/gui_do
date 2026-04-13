import pygame
from ..constants import GType
from .widget import Widget

class Image(Widget):
    def __init__(self, gui, id, rect, image, automatic_pristine=False, scale=True):
        # initialize id and rect
        super().__init__(gui, id, rect)
        self.GType = GType.Image
        self.image = pygame.image.load(self.gui.get_bitmapfactory().file_resource('images', image))
        if scale:
            self.image = pygame.transform.smoothscale(self.image, (rect.width, rect.height))
        self.auto_restore_pristine = automatic_pristine

    def handle_event(self, _, _a):
        return False

    def draw(self):
        super().draw()
        # draw the image bitmap
        self.surface.blit(self.image, self.draw_rect)
