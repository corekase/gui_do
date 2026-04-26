from pygame import Rect
from pygame.draw import rect as draw_rect
from typing import TYPE_CHECKING

from ..core.ui_node import UiNode

if TYPE_CHECKING:
    import pygame
    from ..theme.color_theme import ColorTheme


class FrameControl(UiNode):
    """Decorative frame control."""

    def __init__(self, control_id: str, rect: Rect, border_width: int = 1) -> None:
        super().__init__(control_id, rect)
        self._border_width = max(1, int(border_width))
        self._visuals = None
        self._visual_size = None

    @property
    def border_width(self) -> int:
        return self._border_width

    @border_width.setter
    def border_width(self, value: int) -> None:
        next_width = max(1, int(value))
        if self._border_width == next_width:
            return
        self._border_width = next_width
        self.invalidate()

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
        if not self.visible:
            return
        border_colour = theme.dark if self.enabled else theme.medium
        draw_rect(surface, border_colour, self.rect, self._border_width)
