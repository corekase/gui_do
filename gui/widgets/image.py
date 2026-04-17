import pygame
from pygame import Rect
from pygame.event import Event as PygameEvent
from typing import Optional, TYPE_CHECKING
from ..utility.constants import GuiError
from ..utility.resource_error import DataResourceErrorHandler
from ..utility.widget import Widget

if TYPE_CHECKING:
    from ..utility.guimanager import GuiManager
    from .window import Window

class Image(Widget):
    """Displays a bitmap loaded from data/images."""

    def __init__(self, gui: "GuiManager", id: str, rect: Rect, image: str, automatic_pristine: bool = False, scale: bool = True) -> None:
        super().__init__(gui, id, rect)
        image_path = self.gui.bitmap_factory.file_resource('images', image)
        try:
            self._image = pygame.image.load(image_path)
        except GuiError:
            raise
        except Exception as exc:
            DataResourceErrorHandler.raise_load_error('failed to load widget image', image_path, exc)
        if scale:
            self._image = pygame.transform.smoothscale(self._image, (rect.width, rect.height))
        self.auto_restore_pristine = automatic_pristine

    def handle_event(self, _: PygameEvent, _a: Optional["Window"]) -> bool:
        return False

    def draw(self) -> None:
        super().draw()
        self.surface.blit(self._image, self.draw_rect)
