import pygame
from pygame import Rect
from pygame.event import Event as PygameEvent
from typing import Optional, TYPE_CHECKING
from ..utility.constants import WidgetKind
from ..utility.widget import Widget

if TYPE_CHECKING:
    from ..utility.guimanager import GuiManager
    from .window import Window

class Image(Widget):
    def __init__(self, gui: "GuiManager", id: str, rect: Rect, image: str, automatic_pristine: bool = False, scale: bool = True) -> None:
        # initialize id and rect
        super().__init__(gui, id, rect)
        self.WidgetKind = WidgetKind.Image
        self._image: pygame.Surface = pygame.image.load(self.gui.bitmap_factory.file_resource('images', image))
        if scale:
            self._image = pygame.transform.smoothscale(self._image, (rect.width, rect.height))
        self.auto_restore_pristine = automatic_pristine

    def handle_event(self, _: PygameEvent, _a: Optional["Window"]) -> bool:
        return False

    def draw(self) -> None:
        super().draw()
        # draw the image bitmap
        self.surface.blit(self._image, self.draw_rect)
