from __future__ import annotations

import pygame
from pygame import Rect
from pygame.surface import Surface
from typing import Any, Optional, TYPE_CHECKING

from .events import GuiError
from .resource_error import DataResourceErrorHandler

if TYPE_CHECKING:
    from .gui_manager import GuiManager


class GraphicsCoordinator:
    """Owns pristine/backdrop bitmap operations for manager and managed surfaces."""

    def __init__(self, gui_manager: "GuiManager") -> None:
        """Create GraphicsCoordinator."""
        self.gui: "GuiManager" = gui_manager

    def copy_graphic_area(self, surface: Surface, rect: Rect, flags: int = 0) -> Surface:
        """Copy graphic area."""
        bitmap = pygame.Surface((rect.width, rect.height), flags)
        bitmap.blit(surface, (0, 0), rect)
        return bitmap

    def set_pristine(self, image: str, obj: Optional[Any] = None) -> None:
        """Set pristine."""
        if obj is None:
            obj = self.gui
        if obj.surface is None:
            raise GuiError('set_pristine target surface is not initialized')
        if image is None or not isinstance(image, str) or image == '':
            raise GuiError(f'set_pristine image must be a non-empty string, got: {image!r}')

        image_path = self.gui.graphics_factory.file_resource('images', image)
        try:
            bitmap = pygame.image.load(image_path)
        except GuiError:
            raise
        except Exception as exc:
            DataResourceErrorHandler.raise_load_error('failed to load pristine image', image_path, exc)

        _, _, width, height = obj.surface.get_rect()
        scaled_bitmap = pygame.transform.smoothscale(bitmap, (width, height))
        obj.surface.blit(scaled_bitmap.convert(), (0, 0), scaled_bitmap.get_rect())
        obj.pristine = self.copy_graphic_area(obj.surface, obj.surface.get_rect()).convert()

    def restore_pristine(self, area: Optional[Rect] = None, obj: Optional[Any] = None) -> None:
        """Restore pristine."""
        if obj is None:
            obj = self.gui
        if obj.pristine is None:
            raise GuiError('restore_pristine called before pristine was initialized')
        if area is None:
            area = obj.pristine.get_rect()
        x, y, _, _ = area
        obj.surface.blit(obj.pristine, (x, y), area)
