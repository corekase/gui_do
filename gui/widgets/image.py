import pygame
from typing import Any
from ..utility.constants import WidgetKind
from ..utility.widget import Widget

class Image(Widget):
    def __init__(self, gui: Any, id: Any, rect: Any, image: str, automatic_pristine: bool = False, scale: bool = True) -> None:
        # initialize id and rect
        super().__init__(gui, id, rect)
        self.WidgetKind = WidgetKind.Image
        self.image: pygame.Surface = pygame.image.load(self.gui.bitmap_factory.file_resource('images', image))
        if scale:
            self.image = pygame.transform.smoothscale(self.image, (rect.width, rect.height))
        self.auto_restore_pristine = automatic_pristine

    def handle_event(self, _, _a) -> bool:
        return False

    def draw(self) -> None:
        super().draw()
        # draw the image bitmap
        self.surface.blit(self.image, self.draw_rect)
