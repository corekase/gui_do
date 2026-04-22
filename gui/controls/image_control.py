from pathlib import Path
import pygame
from typing import TYPE_CHECKING
from pygame import Rect

from ..core.ui_node import UiNode

if TYPE_CHECKING:
    from ..theme.color_theme import ColorTheme


class ImageControl(UiNode):
    """Image control with optional scaling and disabled-state rendering."""

    def __init__(self, control_id: str, rect: Rect, image_path: str | Path | pygame.Surface, scale: bool = True) -> None:
        super().__init__(control_id, rect)
        self.image_path = image_path
        self.scale = bool(scale)
        self._base_image = self._load_image(image_path)
        self._scaled_image = None
        self._scaled_size = None
        self._disabled_image = None
        self._disabled_size = None

    @staticmethod
    def _resolve_image_path(image_path: str | Path) -> Path:
        candidate = Path(image_path)
        if candidate.is_absolute():
            return candidate
        root = Path(__file__).resolve().parents[2]
        in_data_images = root / "data" / "images" / str(image_path)
        if in_data_images.exists():
            return in_data_images
        return candidate

    @classmethod
    def _load_image(cls, image_path: str | Path | pygame.Surface) -> pygame.Surface:
        if isinstance(image_path, pygame.Surface):
            return image_path.convert_alpha()
        resolved = cls._resolve_image_path(image_path)
        return pygame.image.load(str(resolved)).convert_alpha()

    def _get_render_image(self) -> pygame.Surface:
        if not self.scale:
            return self._base_image
        target_size = self.rect.size
        if self._scaled_image is None or self._scaled_size != target_size:
            self._scaled_image = pygame.transform.smoothscale(self._base_image, target_size)
            self._scaled_size = target_size
            self._disabled_image = None
            self._disabled_size = None
        return self._scaled_image

    def set_image(self, image_path: str | Path | pygame.Surface) -> None:
        self.image_path = image_path
        self._base_image = self._load_image(image_path)
        self._scaled_image = None
        self._scaled_size = None
        self._disabled_image = None
        self._disabled_size = None
        self.invalidate()

    def draw(self, surface: pygame.Surface, theme: "ColorTheme") -> None:
        if not self.visible:
            return
        image = self._get_render_image()
        if self.enabled:
            surface.blit(image, self.rect)
            return
        if self._disabled_image is None or self._disabled_size != image.get_size():
            self._disabled_image = theme.graphics_factory.build_disabled_bitmap(image)
            self._disabled_size = image.get_size()
        surface.blit(self._disabled_image, self.rect)
