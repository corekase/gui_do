from pygame import Rect
from typing import TYPE_CHECKING

from ..core.ui_node import UiNode

if TYPE_CHECKING:
    import pygame
    from ..theme.color_theme import ColorTheme


class FrameControl(UiNode):
    """Decorative frame control."""

    def __init__(self, control_id: str, rect: Rect, border_width: int = 1) -> None:
        super().__init__(control_id, rect)
        self.border_width = max(1, int(border_width))
        self._visuals = None
        self._visual_size = None

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        factory = theme.graphics_factory
        visual_size = (self.rect.width, self.rect.height)
        if self._visuals is None or self._visual_size != visual_size:
            self._visuals = factory.build_frame_visuals(self.rect)
            self._visual_size = visual_size
        selected = factory.resolve_visual_state(
            self._visuals,
            visible=self.visible,
            enabled=self.enabled,
            armed=False,
            hovered=False,
        )
        surface.blit(selected, self.rect)
