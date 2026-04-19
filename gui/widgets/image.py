from __future__ import annotations

import pygame
from pygame import Rect
from pygame.event import Event as PygameEvent
from typing import Optional, TYPE_CHECKING
from ..utility.events import GuiError
from ..utility.gui_utils.resource_error import DataResourceErrorHandler
from ..utility.intermediates.widget import Widget

if TYPE_CHECKING:
    from ..utility.gui_manager import GuiManager
    from .window import Window

class Image(Widget):
    """Displays a bitmap loaded from data/images."""

    def __init__(self, gui: "GuiManager", id: str, rect: Rect, image: str, automatic_pristine: bool = False, scale: bool = True) -> None:
        """Create Image."""
        super().__init__(gui, id, rect)
        if not isinstance(image, str) or image == '':
            raise GuiError(f'image must be a non-empty string, got: {image!r}')
        image_path = self.gui.graphics_factory.file_resource('images', image)
        try:
            self._image = pygame.image.load(image_path)
        except GuiError:
            raise
        except Exception as exc:
            DataResourceErrorHandler.raise_load_error('failed to load widget image', image_path, exc)
        if scale:
            self._image = pygame.transform.smoothscale(self._image, (rect.width, rect.height))
        self._disabled_image = self._build_disabled_surface(self._image)
        self.auto_restore_pristine = automatic_pristine

    def handle_event(self, _: PygameEvent, _a: Optional["Window"]) -> bool:
        """Handle event."""
        if self.disabled:
            return False
        return False

    def leave(self) -> None:
        """Image is non-interactive and keeps no focus state."""
        return

    def draw(self) -> None:
        """Draw."""
        super().draw()
        if self.disabled:
            self.surface.blit(self._disabled_image, self.draw_rect)
            return
        self.surface.blit(self._image, self.draw_rect)
