import pygame
from typing import TYPE_CHECKING
from pygame import Rect

from ..core.ui_node import UiNode

if TYPE_CHECKING:
    from ..theme.color_theme import ColorTheme


class ImageControl(UiNode):
    """Static image control."""

    def __init__(self, control_id: str, rect: Rect, image_path: str, scale: bool = True) -> None:
        super().__init__(control_id, rect)
        self.image_path = image_path
        self.scale = bool(scale)
        self._image = pygame.image.load(self.image_path).convert_alpha()
        if self.scale:
            self._image = pygame.transform.smoothscale(self._image, self.rect.size)

    def draw(self, surface: pygame.Surface, _theme: "ColorTheme") -> None:
        surface.blit(self._image, self.rect)
