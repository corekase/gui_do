import pygame
from ..values.constants import WidgetKind
from .utility.widget import Widget
from .utility.registry import register_widget

@register_widget("Image")
class Image(Widget):
    def __init__(self, gui, id, rect, image, automatic_pristine=False, scale=True):
        # initialize id and rect
        super().__init__(gui, id, rect)
        self.WidgetKind = WidgetKind.Image
        self.image = pygame.image.load(self.gui.bitmap_factory.file_resource('images', image))
        if scale:
            self.image = pygame.transform.smoothscale(self.image, (rect.width, rect.height))
        self.auto_restore_pristine = automatic_pristine

    def handle_event(self, _, _a):
        return False

    def draw(self):
        super().draw()
        # draw the image bitmap
        self.surface.blit(self.image, self.draw_rect)
